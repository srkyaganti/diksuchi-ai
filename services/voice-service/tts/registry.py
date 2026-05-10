"""Language-code → TTS engine routing and the API allowlist.

This module is the single source of truth for which language codes the
``/tts/generate`` endpoint accepts. Anything outside ``SUPPORTED_LANGUAGES``
is rejected at the request boundary, so unsupported codes never reach a
model.

Keep ``LANGUAGE_ENGINE`` in sync with the ``SUPPORTED_TTS_LANGUAGES`` set
in ``services/web/src/app/api/voice/synthesize/route.ts``.
"""

from __future__ import annotations

from typing import Mapping

from .base import TTSEngine

# Maps an ISO 639 language code → the engine name that handles it.
LANGUAGE_ENGINE: dict[str, str] = {
    # Indic Parler TTS (ai4bharat/indic-parler-tts)
    "as": "indic_parler",
    "bn": "indic_parler",
    "brx": "indic_parler",
    "hne": "indic_parler",
    "doi": "indic_parler",
    "en": "indic_parler",
    "gu": "indic_parler",
    "hi": "indic_parler",
    "kn": "indic_parler",
    "ml": "indic_parler",
    "mni": "indic_parler",
    "mr": "indic_parler",
    "ne": "indic_parler",
    "or": "indic_parler",
    "pa": "indic_parler",
    "sa": "indic_parler",
    "ta": "indic_parler",
    "te": "indic_parler",
    # HebTTS (slp-rl/HebTTS)
    "he": "hebtts",
}

SUPPORTED_LANGUAGES: frozenset[str] = frozenset(LANGUAGE_ENGINE)

# Whisper and some legacy callers still emit the deprecated ISO 639-1
# code "iw" for Hebrew. Normalize before lookup so callers don't have to
# care which spelling they send.
_ALIASES: dict[str, str] = {"iw": "he"}


def normalize_language_code(code: str) -> str:
    """Lowercase, trim, and collapse legacy aliases to their modern code."""
    code = code.strip().lower()
    return _ALIASES.get(code, code)


class TTSRouter:
    """Resolves a language code to the engine instance that owns it."""

    def __init__(self, engines: Mapping[str, TTSEngine]) -> None:
        missing = set(LANGUAGE_ENGINE.values()) - set(engines)
        if missing:
            raise ValueError(
                f"TTSRouter constructed without engines for: {sorted(missing)}"
            )
        self._engines: dict[str, TTSEngine] = dict(engines)

    def route(self, code: str) -> TTSEngine:
        normalized = normalize_language_code(code)
        if normalized not in LANGUAGE_ENGINE:
            raise KeyError(code)
        return self._engines[LANGUAGE_ENGINE[normalized]]

    def engines(self) -> dict[str, TTSEngine]:
        return dict(self._engines)
