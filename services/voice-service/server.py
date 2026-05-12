"""
Voice Service - Combined STT and TTS for Diksuchi AI

GPU-accelerated speech-to-text and text-to-speech service.
- STT: Faster Whisper with CTranslate2
- TTS: language-routed across Indic Parler TTS (Indic + English) and
  HebTTS (Hebrew); see tts/registry.py for the language allowlist.
"""

from dotenv import load_dotenv

load_dotenv()

import asyncio
import io
import os
from contextlib import asynccontextmanager

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from faster_whisper import WhisperModel
from pydantic import BaseModel

from tts import (
    LANGUAGE_SPEAKERS,
    SUPPORTED_LANGUAGES,
    TTSRouter,
    normalize_language_code,
)
from tts.hebtts import HebTTSEngine
from tts.indic_parler import IndicParlerEngine

# --------------------------------------------------
# Configuration
# --------------------------------------------------

# STT Configuration
STT_MODEL_NAME = os.getenv("STT_MODEL_NAME", "large-v3")
STT_DEVICE = os.getenv("STT_DEVICE", "cuda")
STT_COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "float16")
STT_VAD_FILTER = os.getenv("STT_VAD_FILTER", "false").lower() == "true"

# TTS Configuration
TTS_MODEL_NAME = os.getenv("TTS_MODEL_NAME", "ai4bharat/indic-parler-tts")
TTS_DEVICE = os.getenv("TTS_DEVICE", "auto")

# Common Configuration
VOICE_SERVICE_PORT = int(os.getenv("VOICE_SERVICE_PORT", "8000"))
HF_TOKEN = os.getenv("HF_TOKEN")
HF_HUB_OFFLINE = os.getenv("HF_HUB_OFFLINE", "").lower() in ("1", "true", "on", "yes")

# --------------------------------------------------
# Global state
# --------------------------------------------------

stt_model: WhisperModel | None = None
router: TTSRouter | None = None


# --------------------------------------------------
# Utility Functions
# --------------------------------------------------


def load_audio(file_bytes: bytes) -> np.ndarray:
    """Load audio file bytes into a numpy array (mono, float32)."""
    try:
        audio, sr = sf.read(io.BytesIO(file_bytes))

        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        return audio.astype(np.float32)

    except Exception as e:
        raise RuntimeError(
            "Unable to decode audio. Install ffmpeg if using mp3/m4a formats."
        ) from e


# --------------------------------------------------
# Lifespan event handler
# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global stt_model, router

    print("=" * 60)
    print("Voice Service Starting...")
    print("=" * 60)

    if HF_HUB_OFFLINE:
        # In offline mode huggingface_hub.login() would call whoami() over the
        # network and raise OfflineModeIsEnabled. Skip it — HF_TOKEN, if set,
        # is read directly from the environment for any cached lookups.
        print("✓ HuggingFace offline mode enabled (cache only)\n")
    elif HF_TOKEN:
        from huggingface_hub import login

        login(token=HF_TOKEN)
        print("✓ HuggingFace authentication configured\n")

    print("[1/3] Loading STT Model (Faster Whisper)...")
    print(f"  Model: {STT_MODEL_NAME}")
    print(f"  Device: {STT_DEVICE}")
    print(f"  Compute type: {STT_COMPUTE_TYPE}")

    try:
        stt_model = WhisperModel(
            STT_MODEL_NAME, device=STT_DEVICE, compute_type=STT_COMPUTE_TYPE
        )
        print("✓ STT model loaded successfully\n")
    except Exception as e:
        print(f"✗ Failed to load STT model: {e}")
        raise SystemExit(1)

    print("[2/3] Loading TTS Model (Indic Parler TTS)...")
    indic = IndicParlerEngine(
        model_name=TTS_MODEL_NAME, device=TTS_DEVICE, offline=HF_HUB_OFFLINE
    )
    try:
        indic.load()
        print("✓ Indic Parler engine loaded\n")
    except Exception as e:
        print(f"✗ Failed to load Indic Parler engine: {e}")
        raise SystemExit(1)

    print("[3/3] Loading TTS Model (HebTTS)...")
    heb = HebTTSEngine(device=TTS_DEVICE)
    try:
        heb.load()
        print("✓ HebTTS engine loaded\n")
    except Exception as e:
        print(f"✗ Failed to load HebTTS engine: {e}")
        raise SystemExit(1)

    router = TTSRouter({indic.name: indic, heb.name: heb})

    print("=" * 60)
    print("✓ All models loaded! Service ready.")
    print("=" * 60)

    yield

    stt_model = None
    router = None
    print("Models unloaded.")


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="Voice Service",
    description="Combined STT and TTS service for Diksuchi AI",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Root Health Endpoints
# --------------------------------------------------


def _engines_loaded() -> bool:
    return router is not None and all(e.loaded for e in router.engines().values())


@app.get("/")
@app.get("/health")
def health():
    """Combined health check for both services."""
    engines_status = {}
    if router is not None:
        for name, engine in router.engines().items():
            engines_status[name] = {"loaded": engine.loaded}
    return {
        "status": "healthy"
        if (stt_model is not None and _engines_loaded())
        else "loading",
        "stt": {
            "loaded": stt_model is not None,
            "model": STT_MODEL_NAME,
            "device": STT_DEVICE,
        },
        "tts": {
            "loaded": _engines_loaded(),
            "engines": engines_status,
        },
    }


# --------------------------------------------------
# STT Endpoints (namespaced with /stt/)
# --------------------------------------------------


@app.get("/stt/health")
def stt_health():
    """STT-specific health check."""
    return {
        "status": "healthy" if stt_model is not None else "loading",
        "model_loaded": stt_model is not None,
        "model": STT_MODEL_NAME,
        "device": STT_DEVICE,
        "compute_type": STT_COMPUTE_TYPE,
    }


@app.post("/stt/transcribe")
async def stt_transcribe(
    file: UploadFile = File(...),
    vad_filter: bool = STT_VAD_FILTER,
    language: str | None = None,
    task: str = "transcribe",
):
    """
    Transcribe a single audio file.

    Returns language detection, full text, and segment-level timestamps.

    Args:
        file: Audio file to transcribe
        vad_filter: Enable voice activity detection filter
        language: Optional ISO 639-1 language code (e.g., 'en', 'hi') to skip auto-detection
        task: "transcribe" (output spoken language) or "translate" (output English).
              Whisper's translate task only supports target=English.
    """
    if stt_model is None:
        raise HTTPException(status_code=503, detail="STT model not loaded")

    if task not in ("transcribe", "translate"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task '{task}'. Must be 'transcribe' or 'translate'.",
        )

    try:
        file_bytes = await file.read()
        audio = load_audio(file_bytes)

        transcribe_kwargs = {
            "audio": audio,
            "beam_size": 5,
            "vad_filter": vad_filter,
            "task": task,
        }
        if language:
            transcribe_kwargs["language"] = language

        segments, info = stt_model.transcribe(**transcribe_kwargs)

        segments_out = []
        full_text = []

        for seg in segments:
            text = seg.text.strip()
            segments_out.append({"start": seg.start, "end": seg.end, "text": text})
            full_text.append(text)

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "task": task,
            "text": " ".join(full_text),
            "segments": segments_out,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# TTS Endpoints (namespaced with /tts/)
# --------------------------------------------------


@app.get("/tts/health")
def tts_health():
    """TTS-specific health check."""
    if router is None:
        return {"status": "loading", "engines": {}}
    engines = {
        name: {"loaded": engine.loaded, "languages": sorted(engine.supported_languages())}
        for name, engine in router.engines().items()
    }
    return {
        "status": "healthy" if _engines_loaded() else "loading",
        "supported_languages": sorted(SUPPORTED_LANGUAGES),
        "engines": engines,
    }


class TTSRequest(BaseModel):
    """Request model for TTS generation."""

    text: str
    language_code: str
    speaker_name: str | None = None
    custom_description: str | None = None


@app.post("/tts/generate")
async def tts_generate(request: TTSRequest):
    """
    Generate audio from text using the TTS engine bound to ``language_code``.

    Returns 400 immediately if the language code is not in the allowlist —
    no model code runs for unsupported codes.
    """
    if router is None:
        raise HTTPException(status_code=503, detail="TTS engines not loaded yet")

    code = normalize_language_code(request.language_code)
    if code not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_language",
                "language_code": request.language_code,
                "supported": sorted(SUPPORTED_LANGUAGES),
            },
        )

    try:
        engine = router.route(code)
    except KeyError:
        # Defensive: route() and the allowlist agree, so this shouldn't fire.
        raise HTTPException(status_code=500, detail="No engine for language")

    try:
        async with engine.lock:
            audio_arr, sample_rate = await asyncio.to_thread(
                engine.synthesize,
                request.text,
                code,
                request.speaker_name,
                request.custom_description,
            )

        buffer = io.BytesIO()
        sf.write(buffer, audio_arr, sample_rate, format="WAV")
        buffer.seek(0)

        return Response(
            content=buffer.read(),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=output.wav"},
        )

    except ValueError as e:
        # Engine-level validation (unknown speaker, etc.).
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@app.get("/tts/languages")
def tts_list_languages():
    """List all supported languages and their available speakers."""
    return {"languages": LANGUAGE_SPEAKERS}


@app.get("/tts/languages/{language_code}")
def tts_get_language_info(language_code: str):
    """Get speaker information for a specific language."""
    code = normalize_language_code(language_code)

    if code not in LANGUAGE_SPEAKERS:
        raise HTTPException(
            status_code=404,
            detail=f"Language '{language_code}' not found. "
            f"Available languages: {', '.join(LANGUAGE_SPEAKERS.keys())}",
        )

    return {"language": code, "speakers": LANGUAGE_SPEAKERS[code]}


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print(f"Starting Voice Service on port {VOICE_SERVICE_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=VOICE_SERVICE_PORT)
