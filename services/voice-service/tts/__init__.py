"""TTS engine abstractions and language-code router for voice-service."""

from .base import TTSEngine
from .registry import (
    LANGUAGE_ENGINE,
    SUPPORTED_LANGUAGES,
    TTSRouter,
    normalize_language_code,
)
from .speakers import LANGUAGE_SPEAKERS, get_speaker_description

__all__ = [
    "TTSEngine",
    "TTSRouter",
    "LANGUAGE_ENGINE",
    "SUPPORTED_LANGUAGES",
    "LANGUAGE_SPEAKERS",
    "normalize_language_code",
    "get_speaker_description",
]
