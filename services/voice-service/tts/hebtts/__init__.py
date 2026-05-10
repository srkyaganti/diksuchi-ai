"""HebTTSEngine — wraps the vendored slp-rl/HebTTS inference code.

HebTTS uses zero-shot acoustic prompting: each speaker is a reference
WAV clip. We pre-encode each bundled clip once at load time and cache
the resulting acoustic prompt tensors on-device so per-request synthesis
just runs the AR + NAR generation and the encodec decode.

The vendored package is added to ``sys.path`` lazily inside ``load()`` so
that import-time failures (missing ``encodec``/``lhotse``/``phonemizer``)
surface as clean engine-load errors instead of crashing module import.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf
import torch

from ..base import TTSEngine
from ..speakers import LANGUAGE_SPEAKERS

_VENDORED_ROOT = Path(__file__).resolve().parent / "_vendored"
_DEFAULT_CHECKPOINT = Path.home() / ".cache" / "hebtts" / "checkpoint.pt"
_HEBTTS_LANGUAGES: set[str] = {"he"}


class HebTTSEngine(TTSEngine):
    name = "hebtts"

    def __init__(
        self,
        checkpoint_path: str | None = None,
        device: str | None = None,
        top_k: int = 40,
        temperature: float = 1.0,
    ) -> None:
        super().__init__()
        env_ckpt = os.getenv("HEBTTS_CHECKPOINT_PATH")
        self.checkpoint_path = Path(checkpoint_path or env_ckpt or _DEFAULT_CHECKPOINT)
        self.configured_device = device or os.getenv("TTS_DEVICE", "auto")
        self.top_k = int(os.getenv("HEBTTS_TOP_K", top_k))
        self.temperature = float(os.getenv("HEBTTS_TEMPERATURE", temperature))

        self._device: torch.device | None = None
        self._model = None
        self._text_collater = None
        self._audio_tokenizer = None
        self._alef_bert_tokenizer = None
        # speaker_name -> (cached audio_prompts tensor on device, text_prompt str)
        self._speakers: dict[str, tuple[torch.Tensor, str]] = {}

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def supported_languages(self) -> set[str]:
        return set(_HEBTTS_LANGUAGES)

    def _resolve_device(self) -> torch.device:
        if self.configured_device == "cuda":
            return torch.device("cuda", 0)
        if self.configured_device == "cpu":
            return torch.device("cpu")
        if self.configured_device == "mps":
            return torch.device("mps")
        # auto
        if torch.cuda.is_available():
            return torch.device("cuda", 0)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    def load(self) -> None:
        if self.loaded:
            return

        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"HebTTS checkpoint not found at {self.checkpoint_path}. "
                "Set HEBTTS_CHECKPOINT_PATH or run prefetch_models.py to download it."
            )

        # The vendored ``valle`` package is a top-level import; expose it
        # on sys.path so vendored intra-package imports resolve.
        if str(_VENDORED_ROOT) not in sys.path:
            sys.path.insert(0, str(_VENDORED_ROOT))

        # Tame protobuf so omegaconf/lhotse don't trip over the C++ impl.
        os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

        from omegaconf import OmegaConf

        from utils import AttributeDict  # vendored utils.py
        from valle.data import AudioTokenizer  # type: ignore
        from valle.data.collation import get_text_token_collater  # type: ignore
        from valle.data.hebrew_root_tokenizer import (  # type: ignore
            AlefBERTRootTokenizer,
        )
        from valle.models import get_model  # type: ignore

        device = self._resolve_device()
        print(f"  Using device: {device}")
        if device.type == "cuda":
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            print(
                f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
            )

        print(f"  Loading checkpoint: {self.checkpoint_path}")
        # weights_only=False: the upstream checkpoint pickles non-tensor
        # objects (pathlib.PosixPath, training config). PyTorch 2.6 flipped
        # the default to True, which fails on this file. The checkpoint is
        # the official slp-rl/HebTTS release from Google Drive; we trust it.
        checkpoint = torch.load(
            str(self.checkpoint_path), map_location=device, weights_only=False
        )
        args = AttributeDict(checkpoint)

        model = get_model(args)
        missing, unexpected = model.load_state_dict(checkpoint["model"], strict=True)
        assert not missing, f"missing keys: {missing}"
        assert not unexpected, f"unexpected keys: {unexpected}"
        model.to(device)
        model.eval()

        tokens_file = _VENDORED_ROOT / "tokenizer" / "unique_words_tokens_all.k2symbols"
        vocab_file = _VENDORED_ROOT / "tokenizer" / "vocab.txt"
        speakers_yaml = _VENDORED_ROOT / "speakers" / "speakers.yaml"

        text_collater = get_text_token_collater(str(tokens_file))
        audio_tokenizer = AudioTokenizer(mbd=False)
        alef_bert_tokenizer = AlefBERTRootTokenizer(vocab_file=str(vocab_file))

        self._device = device
        self._model = model
        self._text_collater = text_collater
        self._audio_tokenizer = audio_tokenizer
        self._alef_bert_tokenizer = alef_bert_tokenizer

        self._cache_speaker_prompts(speakers_yaml, OmegaConf)
        print(f"  Cached {len(self._speakers)} speakers: {sorted(self._speakers)}")

    def _encode_reference_wav(self, wav_path: Path) -> torch.Tensor:
        """Drop-in replacement for upstream ``tokenize_audio`` that loads
        with soundfile to avoid torchaudio's torchcodec/FFmpeg dependency.

        Returns the encodec-encoded prompt tensor laid out as
        ``[1, num_codebooks, T]`` for direct ``transpose(2, 1)`` downstream,
        matching the shape the upstream caller expects from
        ``encoded_frames[0][0]``.
        """
        # encodec wraps torchaudio's resampler; we do the resample upstream
        # in float32 via soundfile + julius? Avoid extra deps: the cached
        # speaker WAVs in _vendored/speakers/ are 24 kHz mono already (the
        # encodec target), so we skip resampling and assert on mismatch.
        wav, sr = sf.read(str(wav_path), dtype="float32", always_2d=True)
        # soundfile gives [T, C]; encodec expects [B, C, T].
        wav_t = torch.from_numpy(wav.T).unsqueeze(0).contiguous()

        target_sr = self._audio_tokenizer.sample_rate
        target_ch = self._audio_tokenizer.channels
        if sr != target_sr:
            from encodec.utils import convert_audio  # local import; cheap

            wav_t = convert_audio(wav_t.squeeze(0), sr, target_sr, target_ch)
            wav_t = wav_t.unsqueeze(0)
        elif wav_t.shape[1] != target_ch:
            wav_t = wav_t.mean(dim=1, keepdim=True)

        with torch.no_grad():
            encoded_frames = self._audio_tokenizer.encode(wav_t)

        # encoded_frames matches upstream tokenize_audio: list[(codes, scale)]
        # where codes is [B, num_codebooks, T]. Upstream takes [0][0].
        return encoded_frames[0][0]

    def _cache_speaker_prompts(self, speakers_yaml: Path, OmegaConf) -> None:
        catalogue = OmegaConf.load(str(speakers_yaml))
        for name in LANGUAGE_SPEAKERS["he"]["available"]:
            if name not in catalogue:
                warnings.warn(
                    f"Speaker '{name}' listed in LANGUAGE_SPEAKERS['he'] but missing "
                    f"from {speakers_yaml.name}; skipping."
                )
                continue
            entry = catalogue[name]
            audio_path = speakers_yaml.parent / entry["audio-prompt"]
            codes = self._encode_reference_wav(audio_path)
            prompt = codes.transpose(2, 1).to(self._device)
            self._speakers[name] = (prompt, str(entry["text-prompt"]))

    def synthesize(
        self,
        text: str,
        language_code: str,
        speaker_name: str | None,
        custom_description: str | None,
    ) -> Tuple[np.ndarray, int]:
        if self._model is None:
            raise RuntimeError("HebTTSEngine not loaded")

        if custom_description:
            warnings.warn(
                "HebTTS ignores custom_description (no description-conditioned path).",
                stacklevel=2,
            )

        chosen = speaker_name or LANGUAGE_SPEAKERS["he"]["recommended"][0]
        if chosen not in self._speakers:
            available = ", ".join(sorted(self._speakers))
            raise ValueError(
                f"Speaker '{chosen}' not available for he. Available speakers: {available}"
            )
        audio_prompts, prompt_text = self._speakers[chosen]

        # Re-import the module-level helper from the vendored package; we
        # need it both at load time (for caching) and per-request (here)
        # because ``replace_chars`` is part of the same vendored module.
        from valle.data.hebrew_root_tokenizer import replace_chars  # type: ignore

        full_text = [replace_chars(f"{prompt_text} {text}").strip().replace(" ", "_")]
        prompt_only = [replace_chars(prompt_text).strip().replace(" ", "_")]

        tokens = self._alef_bert_tokenizer._tokenize(full_text)
        prompt_tokens = self._alef_bert_tokenizer._tokenize(prompt_only)

        text_tokens, text_tokens_lens = self._text_collater([tokens])
        _, enroll_x_lens = self._text_collater([prompt_tokens])

        with torch.inference_mode():
            encoded_frames = self._model.inference(
                text_tokens.to(self._device),
                text_tokens_lens.to(self._device),
                audio_prompts,
                enroll_x_lens=enroll_x_lens,
                top_k=self.top_k,
                temperature=self.temperature,
            )
            samples = self._audio_tokenizer.decode(
                [(encoded_frames.transpose(2, 1), None)]
            )

        # samples: list[Tensor[B, C, T]]; take first batch, mono.
        wav = samples[0].squeeze().to(torch.float32).cpu().numpy()
        if wav.ndim > 1:
            wav = wav.mean(axis=0)
        return wav, 24000
