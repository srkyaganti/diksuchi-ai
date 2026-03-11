"""
Indic Parler TTS Service - Text-to-Speech for 18+ Indian Languages.

GPU-accelerated TTS service using ai4bharat/indic-parler-tts model.
Supports multiple Indian languages with various speaker voices.
"""

from dotenv import load_dotenv

load_dotenv()

import os
import io
from contextlib import asynccontextmanager

import torch
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

# --------------------------------------------------
# Configuration
# --------------------------------------------------

TTS_MODEL_NAME = os.getenv("TTS_MODEL_NAME", "ai4bharat/indic-parler-tts")
TTS_DEVICE = os.getenv("TTS_DEVICE", "auto")  # auto, cuda, mps, cpu
TTS_PORT = int(os.getenv("TTS_PORT", "8002"))
TTS_HF_TOKEN = os.getenv("TTS_HF_TOKEN") or os.getenv("HF_TOKEN")

# --------------------------------------------------
# Language to speaker mapping (ISO 639 language codes)
# --------------------------------------------------

LANGUAGE_SPEAKERS = {
    "as": {  # Assamese
        "available": ["Amit", "Sita", "Poonam", "Rakesh"],
        "recommended": ["Amit", "Sita"],
    },
    "bn": {  # Bengali
        "available": ["Arjun", "Aditi", "Tapan", "Rashmi", "Arnav", "Riya"],
        "recommended": ["Arjun", "Aditi"],
    },
    "brx": {  # Bodo
        "available": ["Bikram", "Maya", "Kalpana"],
        "recommended": ["Bikram", "Maya"],
    },
    "hne": {  # Chhattisgarhi
        "available": ["Bhanu", "Champa"],
        "recommended": ["Bhanu", "Champa"],
    },
    "doi": {  # Dogri
        "available": ["Karan"],
        "recommended": ["Karan"],
    },
    "en": {  # English
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
    "gu": {  # Gujarati
        "available": ["Yash", "Neha"],
        "recommended": ["Yash", "Neha"],
    },
    "hi": {  # Hindi
        "available": ["Rohit", "Divya", "Aman", "Rani"],
        "recommended": ["Rohit", "Divya"],
    },
    "kn": {  # Kannada
        "available": ["Suresh", "Anu", "Chetan", "Vidya"],
        "recommended": ["Suresh", "Anu"],
    },
    "ml": {  # Malayalam
        "available": ["Anjali", "Anju", "Harish"],
        "recommended": ["Anjali", "Harish"],
    },
    "mni": {  # Manipuri (Meitei)
        "available": ["Laishram", "Ranjit"],
        "recommended": ["Laishram", "Ranjit"],
    },
    "mr": {  # Marathi
        "available": ["Sanjay", "Sunita", "Nikhil", "Radha", "Varun", "Isha"],
        "recommended": ["Sanjay", "Sunita"],
    },
    "ne": {  # Nepali
        "available": ["Amrita"],
        "recommended": ["Amrita"],
    },
    "or": {  # Odia
        "available": ["Manas", "Debjani"],
        "recommended": ["Manas", "Debjani"],
    },
    "pa": {  # Punjabi
        "available": ["Divjot", "Gurpreet"],
        "recommended": ["Divjot", "Gurpreet"],
    },
    "sa": {  # Sanskrit
        "available": ["Aryan"],
        "recommended": ["Aryan"],
    },
    "ta": {  # Tamil
        "available": ["Kavitha", "Jaya"],
        "recommended": ["Jaya"],
    },
    "te": {  # Telugu
        "available": ["Prakash", "Lalitha", "Kiran"],
        "recommended": ["Prakash", "Lalitha"],
    },
}

# --------------------------------------------------
# Global model instances
# --------------------------------------------------

model: ParlerTTSForConditionalGeneration | None = None
tokenizer: AutoTokenizer | None = None
description_tokenizer: AutoTokenizer | None = None
device: str | None = None


def _resolve_device() -> str:
    """Resolve the best available device."""
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
    print(f"Using device: {device}")

    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        print(f"GPU Memory: {props.total_memory / 1024**3:.2f} GB")
    elif device == "mps":
        print("Using Apple Metal Performance Shaders")
    else:
        print("Running on CPU (slow for TTS)")


# --------------------------------------------------
# Lifespan event handler
# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer, description_tokenizer, device

    print("=" * 60)
    print("Indic Parler TTS Service Starting...")
    print("=" * 60)
    print(f"Model: {TTS_MODEL_NAME}")

    device = _resolve_device()
    _log_device_info(device)

    print("Loading model... This may take a while on first run.")

    if TTS_HF_TOKEN:
        from huggingface_hub import login

        login(token=TTS_HF_TOKEN)
        print("HuggingFace authentication configured")

    model = ParlerTTSForConditionalGeneration.from_pretrained(TTS_MODEL_NAME).to(device)
    tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL_NAME)
    description_tokenizer = AutoTokenizer.from_pretrained(
        model.config.text_encoder._name_or_path
    )

    print("=" * 60)
    print("Model loaded successfully! Server is ready.")
    print("=" * 60)

    yield

    model = None
    tokenizer = None
    description_tokenizer = None
    print("Model unloaded.")


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="Indic Parler TTS Service",
    description="Text-to-Speech service for 18+ Indian languages using ParlerTTS",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Request/Response Models
# --------------------------------------------------


class TTSRequest(BaseModel):
    """Request model for TTS generation."""

    text: str
    language_code: str
    speaker_name: str | None = None
    custom_description: str | None = None


class LanguageInfo(BaseModel):
    """Response model for language information."""

    language: str
    available: list[str]
    recommended: list[str]


# --------------------------------------------------
# Utility Functions
# --------------------------------------------------


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
# Health endpoint
# --------------------------------------------------


@app.get("/")
def health():
    """Health check endpoint."""
    return {
        "status": "running" if model is not None else "loading",
        "model": TTS_MODEL_NAME,
        "device": device,
    }


@app.get("/health")
def health_detailed():
    """Detailed health check."""
    return {
        "status": "healthy" if model is not None else "loading",
        "model_loaded": model is not None,
        "model": TTS_MODEL_NAME,
        "device": device,
    }


# --------------------------------------------------
# TTS Generation endpoint
# --------------------------------------------------


@app.post("/generate")
async def generate_audio(request: TTSRequest):
    """
    Generate audio from text using the TTS model.

    Parameters:
    - text: The text to convert to speech
    - language_code: ISO 639 language code (e.g., 'hi', 'en', 'ta', 'bn')
    - speaker_name: Optional speaker name. Uses first recommended if not provided.
    - custom_description: Optional custom voice description (overrides speaker-based)

    Returns: Audio file in WAV format
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

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

        generation = model.generate(
            input_ids=description_input_ids.input_ids,
            attention_mask=description_input_ids.attention_mask,
            prompt_input_ids=prompt_input_ids.input_ids,
            prompt_attention_mask=prompt_input_ids.attention_mask,
        )

        audio_arr = generation.cpu().numpy().squeeze()

        buffer = io.BytesIO()
        sf.write(buffer, audio_arr, model.config.sampling_rate, format="WAV")
        buffer.seek(0)

        return Response(
            content=buffer.read(),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=output.wav"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


# --------------------------------------------------
# Language information endpoints
# --------------------------------------------------


@app.get("/languages")
def list_languages():
    """List all supported languages and their available speakers."""
    return {"languages": LANGUAGE_SPEAKERS}


@app.get("/languages/{language_code}")
def get_language_info(language_code: str):
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

    print(f"Starting TTS service on port {TTS_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=TTS_PORT)
