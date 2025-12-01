import os
import torch
import time
import io
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import librosa
from huggingface_hub import login
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "openai/whisper-large-v3")
HF_TOKEN = os.getenv("HF_TOKEN")
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
DEVICE_OVERRIDE = os.getenv("DEVICE_OVERRIDE")

# Global variables for model and device
model = None
processor = None
pipe = None
device = None
model_name = None

# Pydantic models for API documentation
class TranscriptionSegment(BaseModel):
    text: str
    timestamp: List[float]

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    task: str
    duration_seconds: float
    segments: Optional[List[Dict[str, Any]]] = None
    processing_time_seconds: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: Optional[str]
    model_name: Optional[str]

def detect_device() -> str:
    """
    Detect the best available device for inference.
    Priority: CUDA (NVIDIA GPU) > MPS (Apple Silicon) > CPU
    """
    if DEVICE_OVERRIDE:
        print(f"Device override: {DEVICE_OVERRIDE}")
        return DEVICE_OVERRIDE

    if torch.cuda.is_available():
        device = "cuda:0"
        print(f"Using device: {device} ({torch.cuda.get_device_name(0)})")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        return device
    elif torch.backends.mps.is_available():
        device = "mps"
        print(f"Using device: {device} (Apple Metal)")
        return device
    else:
        device = "cpu"
        print(f"Using device: {device}")
        return device

async def load_audio_from_upload(file: UploadFile) -> np.ndarray:
    """
    Load audio file from upload into numpy array at 16kHz.
    Whisper models require 16kHz mono audio.

    Parameters:
    - file: UploadFile object from FastAPI

    Returns:
    - numpy array of audio samples at 16kHz
    """
    try:
        # Read file content into memory
        content = await file.read()
        audio_buffer = io.BytesIO(content)

        # Load with librosa (handles multiple formats, resamples to 16kHz)
        audio_array, _ = librosa.load(
            audio_buffer,
            sr=16000,  # Whisper requires 16kHz
            mono=True   # Convert to mono
        )

        return audio_array
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to load audio file: {str(e)}. Ensure the file is a valid audio format."
        )

def validate_audio_file(file: UploadFile, max_size_mb: int):
    """
    Validate uploaded audio file format.

    Parameters:
    - file: UploadFile object
    - max_size_mb: Maximum file size in MB
    """
    if not file:
        raise HTTPException(
            status_code=400,
            detail="No audio file provided"
        )

    # Validate file extension
    allowed_extensions = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4", ".aac"}
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file format: {ext}. Supported formats: {', '.join(sorted(allowed_extensions))}"
        )

# Initialize FastAPI app
app = FastAPI(
    title="Whisper STT Server",
    description="Speech-to-Text service using OpenAI Whisper models",
    version="1.0.0"
)

@app.on_event("startup")
async def load_model():
    """Load the Whisper model once when the server starts"""
    global model, processor, pipe, device, model_name

    print("=" * 60)
    print("Loading Whisper model... This may take a while on first run.")
    print("=" * 60)

    model_name = WHISPER_MODEL
    print(f"Model: {model_name}")

    # Detect device
    device = detect_device()
    dtype = torch.float16 if device != "cpu" else torch.float32
    print(f"Torch dtype: {dtype}")

    # Authenticate with HuggingFace (if token provided)
    if HF_TOKEN:
        print("Authenticating with HuggingFace...")
        login(token=HF_TOKEN)
    else:
        print("No HF_TOKEN found. Using public model access.")

    # Load model and processor
    print(f"Loading model from HuggingFace Hub...")
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_name,
        dtype=dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_name)

    # Create pipeline for easy inference
    print("Creating ASR pipeline...")
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        dtype=dtype,
        device=device,
    )

    print("=" * 60)
    print(f"Model '{model_name}' loaded successfully!")
    print(f"Server is ready on device: {device}")
    print("=" * 60)

@app.get("/")
async def root():
    """Root health check endpoint"""
    return {
        "status": "running",
        "message": "Whisper STT Server is running",
        "device": device,
        "model": model_name
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check endpoint"""
    return {
        "status": "healthy" if model is not None else "loading",
        "model_loaded": model is not None,
        "device": device,
        "model_name": model_name
    }

@app.get("/capabilities")
async def capabilities():
    """Get model capabilities and supported features"""
    return {
        "model": model_name,
        "features": {
            "transcription": True,
            "translation": True,
            "language_detection": True,
            "timestamps": ["none", "sentence", "word"]
        },
        "supported_audio_formats": [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4", ".aac"],
        "max_audio_size_mb": MAX_AUDIO_SIZE_MB,
        "device": device
    }

@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    task: str = Form("transcribe", description="Task: 'transcribe' or 'translate'"),
    language: Optional[str] = Form(None, description="Language code (e.g., 'hi', 'en'). Auto-detect if not provided."),
    return_timestamps: str = Form("sentence", description="Timestamp level: 'none', 'sentence', or 'word'")
):
    """
    Transcribe audio file to text using Whisper.

    Parameters:
    - audio: Audio file to transcribe (mp3, wav, m4a, flac, ogg, webm, mp4, aac)
    - task: 'transcribe' (same language) or 'translate' (to English)
    - language: Optional language code. If not provided, auto-detected
    - return_timestamps: 'none', 'sentence', or 'word'

    Returns:
    - JSON with transcription text, language, segments, and metadata
    """
    # Check if model is loaded
    if model is None or pipe is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded yet. Please wait for server initialization."
        )

    # Validate file
    validate_audio_file(audio, MAX_AUDIO_SIZE_MB)

    # Validate task parameter
    if task not in ["transcribe", "translate"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task: '{task}'. Must be 'transcribe' or 'translate'."
        )

    # Validate return_timestamps parameter
    if return_timestamps not in ["none", "sentence", "word"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid return_timestamps: '{return_timestamps}'. Must be 'none', 'sentence', or 'word'."
        )

    # Load audio into memory
    try:
        print(f"Loading audio file: {audio.filename}")
        audio_array = await load_audio_from_upload(audio)
        audio_duration = len(audio_array) / 16000  # Duration in seconds
        print(f"Audio loaded: {audio_duration:.2f} seconds")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process audio file: {str(e)}"
        )

    # Prepare generation kwargs
    generate_kwargs = {"task": task}

    if language:
        generate_kwargs["language"] = language
        print(f"Language specified: {language}")
    else:
        print("Language: auto-detect")

    # Configure timestamps
    if return_timestamps == "none":
        timestamp_param = False
    elif return_timestamps == "word":
        timestamp_param = "word"
    else:  # sentence
        timestamp_param = True

    # Run inference
    try:
        print(f"Starting transcription (task={task}, timestamps={return_timestamps})...")
        start_time = time.time()

        # Format audio for pipeline: dict with "sampling_rate" and "raw" keys
        audio_input = {
            "sampling_rate": 16000,
            "raw": audio_array
        }

        result = pipe(
            audio_input,
            generate_kwargs=generate_kwargs,
            return_timestamps=timestamp_param
        )

        processing_time = time.time() - start_time
        print(f"Transcription completed in {processing_time:.2f}s")

        # Extract language from result
        detected_language = result.get("chunks", [{}])[0].get("language") if "chunks" in result else None
        response_language = detected_language or language or "unknown"

        # Build response
        response = {
            "text": result["text"],
            "language": response_language,
            "task": task,
            "duration_seconds": audio_duration,
            "processing_time_seconds": round(processing_time, 2)
        }

        # Add segments if timestamps were requested
        if "chunks" in result and result["chunks"]:
            response["segments"] = result["chunks"]

        return JSONResponse(content=response)

    except Exception as e:
        error_msg = str(e)
        print(f"Transcription error: {error_msg}")

        # Handle specific error types
        if "out of memory" in error_msg.lower():
            raise HTTPException(
                status_code=413,
                detail="Audio file too large for processing. Try a shorter clip or smaller model."
            )
        elif "invalid" in error_msg.lower():
            raise HTTPException(
                status_code=422,
                detail=f"Invalid or corrupted audio file: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {error_msg}"
            )

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
