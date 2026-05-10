"""IndicParlerEngine — wraps ai4bharat/indic-parler-tts.

Lifted directly from the original server.py implementation. Behavior
unchanged: bf16 on CUDA, fp32 elsewhere; description-conditioned VALL-E-
style generation with a frozen text-encoder tokenizer.
"""

from __future__ import annotations

import os
from typing import Tuple

import numpy as np
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

from .base import TTSEngine
from .speakers import LANGUAGE_SPEAKERS, get_speaker_description

_INDIC_PARLER_LANGUAGES: set[str] = {
    "as", "bn", "brx", "hne", "doi", "en", "gu", "hi", "kn", "ml",
    "mni", "mr", "ne", "or", "pa", "sa", "ta", "te",
}


def _resolve_device(configured: str) -> str:
    if configured != "auto":
        return configured
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _log_device_info(device: str) -> None:
    print(f"  Using device: {device}")
    if device == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        print(f"  GPU Memory: {props.total_memory / 1024**3:.2f} GB")
    elif device == "mps":
        print("  Using Apple Metal Performance Shaders")
    else:
        print("  Running on CPU (slow for TTS)")


class IndicParlerEngine(TTSEngine):
    name = "indic_parler"

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        offline: bool | None = None,
    ) -> None:
        super().__init__()
        self.model_name = model_name or os.getenv(
            "TTS_MODEL_NAME", "ai4bharat/indic-parler-tts"
        )
        self.configured_device = device or os.getenv("TTS_DEVICE", "auto")
        self.offline = (
            offline
            if offline is not None
            else os.getenv("HF_HUB_OFFLINE", "").lower() in ("1", "true", "on", "yes")
        )

        self._model: ParlerTTSForConditionalGeneration | None = None
        self._tokenizer: AutoTokenizer | None = None
        self._description_tokenizer: AutoTokenizer | None = None
        self._device: str | None = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    @property
    def device(self) -> str | None:
        return self._device

    def supported_languages(self) -> set[str]:
        return set(_INDIC_PARLER_LANGUAGES)

    def load(self) -> None:
        if self.loaded:
            return

        print(f"  Model: {self.model_name}")
        device = _resolve_device(self.configured_device)
        _log_device_info(device)

        # bf16 on CUDA roughly halves VRAM and ~doubles throughput vs fp32. CPU
        # and MPS keep fp32: bf16 on CPU is slow, MPS bf16 support is patchy.
        dtype = torch.bfloat16 if device == "cuda" else torch.float32
        print(f"  Dtype: {dtype}")

        model = ParlerTTSForConditionalGeneration.from_pretrained(
            self.model_name,
            local_files_only=self.offline,
            torch_dtype=dtype,
        ).to(device)
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, local_files_only=self.offline
        )
        description_tokenizer = AutoTokenizer.from_pretrained(
            model.config.text_encoder._name_or_path,
            local_files_only=self.offline,
        )

        self._model = model
        self._tokenizer = tokenizer
        self._description_tokenizer = description_tokenizer
        self._device = device

    def synthesize(
        self,
        text: str,
        language_code: str,
        speaker_name: str | None,
        custom_description: str | None,
    ) -> Tuple[np.ndarray, int]:
        if self._model is None:
            raise RuntimeError("IndicParlerEngine not loaded")

        if custom_description:
            description = custom_description
        else:
            description = get_speaker_description(language_code, speaker_name)

        description_inputs = self._description_tokenizer(
            description, return_tensors="pt"
        ).to(self._device)
        prompt_inputs = self._tokenizer(text, return_tensors="pt").to(self._device)

        with torch.inference_mode():
            generation = self._model.generate(
                input_ids=description_inputs.input_ids,
                attention_mask=description_inputs.attention_mask,
                prompt_input_ids=prompt_inputs.input_ids,
                prompt_attention_mask=prompt_inputs.attention_mask,
            )

        waveform = generation.to(torch.float32).cpu().numpy().squeeze()
        return waveform, int(self._model.config.sampling_rate)
