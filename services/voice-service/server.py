"""
Voice Service - Combined STT and TTS for Diksuchi AI

GPU-accelerated speech-to-text and text-to-speech service.
- STT: Faster Whisper with CTranslate2
- TTS: Indic Parler TTS for 18+ Indian languages
"""

from dotenv import load_dotenv

load_dotenv()

import os
import io
import numpy as np
import soundfile as sf
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from faster_whisper import WhisperModel
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

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

# --------------------------------------------------
# Language to speaker mapping (ISO 639 language codes)
# --------------------------------------------------

LANGUAGE_SPEAKERS = {
    "as": {
        "available": ["Amit", "Sita", "Poonam", "Rakesh"],
        "recommended": ["Amit", "Sita"],
    },
    "bn": {
        "available": ["Arjun", "Aditi", "Tapan", "Rashmi", "Arnav", "Riya"],
        "recommended": ["Arjun", "Aditi"],
    },
    "brx": {
        "available": ["Bikram", "Maya", "Kalpana"],
        "recommended": ["Bikram", "Maya"],
    },
    "hne": {
        "available": ["Bhanu", "Champa"],
        "recommended": ["Bhanu", "Champa"],
    },
    "doi": {
        "available": ["Karan"],
        "recommended": ["Karan"],
    },
    "en": {
        "available": [
            "Thoma",
            "Mary",
            "Swapna",
            "Dinesh",
            "Meera",
            "Jatin",
            "Aakash",
            "Sneha",
            "Kabir",
            "Tisha",
            "Chingkhei",
            "Thoiba",
            "Priya",
            "Tarun",
            "Gauri",
            "Nisha",
            "Raghav",
            "Kavya",
            "Ravi",
            "Vikas",
            "Riya",
        ],
        "recommended": ["Thoma", "Mary"],
    },
    "gu": {
        "available": ["Yash", "Neha"],
        "recommended": ["Yash", "Neha"],
    },
    "hi": {
        "available": ["Rohit", "Divya", "Aman", "Rani"],
        "recommended": ["Rohit", "Divya"],
    },
    "kn": {
        "available": ["Suresh", "Anu", "Chetan", "Vidya"],
        "recommended": ["Suresh", "Anu"],
    },
    "ml": {
        "available": ["Anjali", "Anju", "Harish"],
        "recommended": ["Anjali", "Harish"],
    },
    "mni": {
        "available": ["Laishram", "Ranjit"],
        "recommended": ["Laishram", "Ranjit"],
    },
    "mr": {
        "available": ["Sanjay", "Sunita", "Nikhil", "Radha", "Varun", "Isha"],
        "recommended": ["Sanjay", "Sunita"],
    },
    "ne": {
        "available": ["Amrita"],
        "recommended": ["Amrita"],
    },
    "or": {
        "available": ["Manas", "Debjani"],
        "recommended": ["Manas", "Debjani"],
    },
    "pa": {
        "available": ["Divjot", "Gurpreet"],
        "recommended": ["Divjot", "Gurpreet"],
    },
    "sa": {
        "available": ["Aryan"],
        "recommended": ["Aryan"],
    },
    "ta": {
        "available": ["Kavitha", "Jaya"],
        "recommended": ["Jaya"],
    },
    "te": {
        "available": ["Prakash", "Lalitha", "Kiran"],
        "recommended": ["Prakash", "Lalitha"],
    },
}

# --------------------------------------------------
# Global model instances
# --------------------------------------------------

stt_model: WhisperModel | None = None
tts_model: ParlerTTSForConditionalGeneration | None = None
tokenizer: AutoTokenizer | None = None
description_tokenizer: AutoTokenizer | None = None
device: str | None = None


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


def _resolve_device() -> str:
    """Resolve the best available device for TTS."""
    if TTS_DEVICE != "auto":
        return TTS_DEVICE

    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


def _log_device_info(device: str):
    """Log device information."""
    print(f"  Using device: {device}")

    if device == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        print(f"  GPU Memory: {props.total_memory / 1024**3:.2f} GB")
    elif device == "mps":
        print("  Using Apple Metal Performance Shaders")
    else:
        print("  Running on CPU (slow for TTS)")


def get_speaker_description(language_code: str, speaker_name: str | None = None) -> str:
    """
    Build a voice description based on language and speaker.
    If speaker_name is not provided, uses the first recommended speaker.
    """
    language_code = language_code.lower()

    if language_code not in LANGUAGE_SPEAKERS:
        raise ValueError(
            f"Unsupported language: {language_code}. "
            f"Available languages: {', '.join(LANGUAGE_SPEAKERS.keys())}"
        )

    if speaker_name is None:
        speaker_name = LANGUAGE_SPEAKERS[language_code]["recommended"][0]
    else:
        if speaker_name not in LANGUAGE_SPEAKERS[language_code]["available"]:
            raise ValueError(
                f"Speaker '{speaker_name}' not available for {language_code}. "
                f"Available speakers: {', '.join(LANGUAGE_SPEAKERS[language_code]['available'])}"
            )

    description = (
        f"{speaker_name} speaks with a clear voice with slow speed "
        f"with a moderate speed and pitch. The recording is of very high quality, "
        f"with the speaker's voice sounding clear and very close up."
    )

    return description


# --------------------------------------------------
# Lifespan event handler
# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global stt_model, tts_model, tokenizer, description_tokenizer, device

    print("=" * 60)
    print("Voice Service Starting...")
    print("=" * 60)

    if HF_TOKEN:
        from huggingface_hub import login

        login(token=HF_TOKEN)
        print("✓ HuggingFace authentication configured\n")

    print("[1/2] Loading STT Model (Faster Whisper)...")
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

    print("[2/2] Loading TTS Model (Indic Parler TTS)...")
    print(f"  Model: {TTS_MODEL_NAME}")

    device = _resolve_device()
    _log_device_info(device)

    try:
        tts_model = ParlerTTSForConditionalGeneration.from_pretrained(
            TTS_MODEL_NAME
        ).to(device)
        tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL_NAME)
        description_tokenizer = AutoTokenizer.from_pretrained(
            tts_model.config.text_encoder._name_or_path
        )
        print("✓ TTS model loaded successfully\n")
    except Exception as e:
        print(f"✗ Failed to load TTS model: {e}")
        raise SystemExit(1)

    print("=" * 60)
    print("✓ All models loaded! Service ready.")
    print("=" * 60)

    yield

    stt_model = None
    tts_model = None
    tokenizer = None
    description_tokenizer = None
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


@app.get("/")
@app.get("/health")
def health():
    """Combined health check for both services."""
    return {
        "status": "healthy"
        if (stt_model is not None and tts_model is not None)
        else "loading",
        "stt": {
            "loaded": stt_model is not None,
            "model": STT_MODEL_NAME,
            "device": STT_DEVICE,
        },
        "tts": {
            "loaded": tts_model is not None,
            "model": TTS_MODEL_NAME,
            "device": device,
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
async def stt_transcribe(file: UploadFile = File(...), vad_filter: bool = STT_VAD_FILTER):
    """
    Transcribe a single audio file.

    Returns language detection, full text, and segment-level timestamps.
    """
    if stt_model is None:
        raise HTTPException(status_code=503, detail="STT model not loaded")

    try:
        file_bytes = await file.read()
        audio = load_audio(file_bytes)

        segments, info = stt_model.transcribe(audio, beam_size=5, vad_filter=vad_filter)

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
# TTS Endpoints (namespaced with /tts/)
# --------------------------------------------------


@app.get("/tts/health")
def tts_health():
    """TTS-specific health check."""
    return {
        "status": "healthy" if tts_model is not None else "loading",
        "model_loaded": tts_model is not None,
        "model": TTS_MODEL_NAME,
        "device": device,
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
    Generate audio from text using TTS model.

    Parameters:
    - text: The text to convert to speech
    - language_code: ISO 639 language code (e.g., 'hi', 'en', 'ta')
    - speaker_name: Optional speaker name
    - custom_description: Optional custom voice description

    Returns: Audio file in WAV format
    """
    if tts_model is None:
        raise HTTPException(status_code=503, detail="TTS model not loaded yet")

    try:
        if request.custom_description:
            description = request.custom_description
        else:
            try:
                description = get_speaker_description(
                    request.language_code, request.speaker_name
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        description_input_ids = description_tokenizer(
            description, return_tensors="pt"
        ).to(device)
        prompt_input_ids = tokenizer(request.text, return_tensors="pt").to(device)

        generation = tts_model.generate(
            input_ids=description_input_ids.input_ids,
            attention_mask=description_input_ids.attention_mask,
            prompt_input_ids=prompt_input_ids.input_ids,
            prompt_attention_mask=prompt_input_ids.attention_mask,
        )

        audio_arr = generation.cpu().numpy().squeeze()

        buffer = io.BytesIO()
        sf.write(buffer, audio_arr, tts_model.config.sampling_rate, format="WAV")
        buffer.seek(0)

        return Response(
            content=buffer.read(),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=output.wav"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@app.get("/tts/languages")
def tts_list_languages():
    """List all supported languages and their available speakers."""
    return {"languages": LANGUAGE_SPEAKERS}


@app.get("/tts/languages/{language_code}")
def tts_get_language_info(language_code: str):
    """Get speaker information for a specific language."""
    language_code = language_code.lower()

    if language_code not in LANGUAGE_SPEAKERS:
        raise HTTPException(
            status_code=404,
            detail=f"Language '{language_code}' not found. "
            f"Available languages: {', '.join(LANGUAGE_SPEAKERS.keys())}",
        )

    return {"language": language_code, "speakers": LANGUAGE_SPEAKERS[language_code]}


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print(f"Starting Voice Service on port {VOICE_SERVICE_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=VOICE_SERVICE_PORT)
