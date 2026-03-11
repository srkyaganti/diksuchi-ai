"""
Faster Whisper STT Service - GPU-accelerated Speech-to-Text.

Uses faster-whisper with CTranslate2 for efficient GPU-accelerated transcription.
Supports multiple Whisper model sizes and VAD filtering.
"""

from dotenv import load_dotenv

load_dotenv()

import os
import io
import numpy as np
import soundfile as sf
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel

# --------------------------------------------------
# Configuration
# --------------------------------------------------

STT_MODEL_NAME = os.getenv("STT_MODEL_NAME", "large-v3")
STT_DEVICE = os.getenv("STT_DEVICE", "cuda")
STT_COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "float16")
STT_PORT = int(os.getenv("STT_PORT", "8080"))
STT_HF_TOKEN = os.getenv("STT_HF_TOKEN") or os.getenv("HF_TOKEN")

# --------------------------------------------------
# Global model instance
# --------------------------------------------------

model: WhisperModel | None = None


# --------------------------------------------------
# Lifespan event handler
# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model

    print("=" * 60)
    print("Faster Whisper STT Service Starting...")
    print("=" * 60)
    print(f"Model: {STT_MODEL_NAME}")
    print(f"Device: {STT_DEVICE}")
    print(f"Compute type: {STT_COMPUTE_TYPE}")

    if STT_HF_TOKEN:
        from huggingface_hub import login

        login(token=STT_HF_TOKEN)
        print("HuggingFace authentication configured")

    print("Initializing Whisper model...")
    model = WhisperModel(
        STT_MODEL_NAME, device=STT_DEVICE, compute_type=STT_COMPUTE_TYPE
    )

    print("=" * 60)
    print("Model ready.")
    print("=" * 60)

    yield

    model = None
    print("Model unloaded.")


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="Faster Whisper STT Service",
    description="GPU accelerated speech-to-text using faster-whisper",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------


@app.get("/")
def health():
    """Health check endpoint."""
    return {
        "status": "running" if model is not None else "loading",
        "model": STT_MODEL_NAME,
        "device": STT_DEVICE,
        "compute_type": STT_COMPUTE_TYPE,
    }


@app.get("/health")
def health_detailed():
    """Detailed health check."""
    return {
        "status": "healthy" if model is not None else "loading",
        "model_loaded": model is not None,
        "model": STT_MODEL_NAME,
        "device": STT_DEVICE,
        "compute_type": STT_COMPUTE_TYPE,
    }


# --------------------------------------------------
# Utility: load audio into numpy
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
# Transcribe endpoint
# --------------------------------------------------


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Transcribe a single audio file.

    Returns language detection, full text, and segment-level timestamps.
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not initialized")

    try:
        file_bytes = await file.read()
        audio = load_audio(file_bytes)

        segments, info = model.transcribe(audio, beam_size=5, vad_filter=True)

        segments_out = []
        full_text = []

        for seg in segments:
            text = seg.text.strip()
            segments_out.append({"start": seg.start, "end": seg.end, "text": text})
            full_text.append(text)

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "text": " ".join(full_text),
            "segments": segments_out,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# Batch transcription endpoint
# --------------------------------------------------


@app.post("/transcribe-batch")
async def transcribe_batch(files: list[UploadFile] = File(...)):
    """
    Transcribe multiple audio files.

    Returns array of transcription results.
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not initialized")

    results = []

    for file in files:
        file_bytes = await file.read()
        audio = load_audio(file_bytes)

        segments, info = model.transcribe(audio)

        text = " ".join([s.text.strip() for s in segments])

        results.append(
            {"filename": file.filename, "language": info.language, "text": text}
        )

    return {"results": results}


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print(f"Starting STT service on port {STT_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=STT_PORT)
