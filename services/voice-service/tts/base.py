"""Abstract TTS engine interface.

Each concrete engine (Indic Parler, HebTTS, ...) wraps one model and is
keyed in the language router by a stable ``name``. The router calls
``synthesize()`` under the engine's own ``lock`` so two engines can run
concurrently while a single engine remains serialized.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np


class TTSEngine(ABC):
    name: str

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

    @abstractmethod
    def load(self) -> None: ...

    @property
    @abstractmethod
    def loaded(self) -> bool: ...

    @abstractmethod
    def supported_languages(self) -> set[str]: ...

    @abstractmethod
    def synthesize(
        self,
        text: str,
        language_code: str,
        speaker_name: str | None,
        custom_description: str | None,
    ) -> Tuple[np.ndarray, int]:
        """Synthesize text → (mono float32 waveform, sample_rate)."""
