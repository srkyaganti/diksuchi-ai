import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from huggingface_hub import login
import io

# Login to HuggingFace
login(token="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")

# Initialize FastAPI app
app = FastAPI(title="Indic Parler TTS Server")

# Global variables for model and tokenizers
model = None
tokenizer = None
description_tokenizer = None
device = None

# Language to speaker mapping (using ISO 639 language codes)
LANGUAGE_SPEAKERS = {
    "as": {  # Assamese
        "available": ["Amit", "Sita", "Poonam", "Rakesh"],
        "recommended": ["Amit", "Sita"]
    },
    "bn": {  # Bengali
        "available": ["Arjun", "Aditi", "Tapan", "Rashmi", "Arnav", "Riya"],
        "recommended": ["Arjun", "Aditi"]
    },
    "brx": {  # Bodo
        "available": ["Bikram", "Maya", "Kalpana"],
        "recommended": ["Bikram", "Maya"]
    },
    "hne": {  # Chhattisgarhi
        "available": ["Bhanu", "Champa"],
        "recommended": ["Bhanu", "Champa"]
    },
    "doi": {  # Dogri
        "available": ["Karan"],
        "recommended": ["Karan"]
    },
    "en": {  # English
        "available": ["Thoma", "Mary", "Swapna", "Dinesh", "Meera", "Jatin", "Aakash", "Sneha", "Kabir", "Tisha", "Chingkhei", "Thoiba", "Priya", "Tarun", "Gauri", "Nisha", "Raghav", "Kavya", "Ravi", "Vikas", "Riya"],
        "recommended": ["Thoma", "Mary"]
    },
    "gu": {  # Gujarati
        "available": ["Yash", "Neha"],
        "recommended": ["Yash", "Neha"]
    },
    "hi": {  # Hindi
        "available": ["Rohit", "Divya", "Aman", "Rani"],
        "recommended": ["Rohit", "Divya"]
    },
    "kn": {  # Kannada
        "available": ["Suresh", "Anu", "Chetan", "Vidya"],
        "recommended": ["Suresh", "Anu"]
    },
    "ml": {  # Malayalam
        "available": ["Anjali", "Anju", "Harish"],
        "recommended": ["Anjali", "Harish"]
    },
    "mni": {  # Manipuri (Meitei)
        "available": ["Laishram", "Ranjit"],
        "recommended": ["Laishram", "Ranjit"]
    },
    "mr": {  # Marathi
        "available": ["Sanjay", "Sunita", "Nikhil", "Radha", "Varun", "Isha"],
        "recommended": ["Sanjay", "Sunita"]
    },
    "ne": {  # Nepali
        "available": ["Amrita"],
        "recommended": ["Amrita"]
    },
    "or": {  # Odia
        "available": ["Manas", "Debjani"],
        "recommended": ["Manas", "Debjani"]
    },
    "pa": {  # Punjabi
        "available": ["Divjot", "Gurpreet"],
        "recommended": ["Divjot", "Gurpreet"]
    },
    "sa": {  # Sanskrit
        "available": ["Aryan"],
        "recommended": ["Aryan"]
    },
    "ta": {  # Tamil
        "available": ["Kavitha", "Jaya"],
        "recommended": ["Jaya"]
    },
    "te": {  # Telugu
        "available": ["Prakash", "Lalitha", "Kiran"],
        "recommended": ["Prakash", "Lalitha"]
    }
}

class TTSRequest(BaseModel):
    text: str
    language_code: str
    speaker_name: str = None
    custom_description: str = None

def get_speaker_description(language_code: str, speaker_name: str = None) -> str:
    """
    Build a voice description based on language and speaker.
    If speaker_name is not provided, uses the first recommended speaker.
    """
    language_code = language_code.lower()

    if language_code not in LANGUAGE_SPEAKERS:
        raise ValueError(f"Unsupported language: {language_code}. Available languages: {', '.join(LANGUAGE_SPEAKERS.keys())}")

    # If no speaker provided, use the first recommended speaker
    if speaker_name is None:
        speaker_name = LANGUAGE_SPEAKERS[language_code]["recommended"][0]
    else:
        # Validate speaker name
        if speaker_name not in LANGUAGE_SPEAKERS[language_code]["available"]:
            raise ValueError(
                f"Speaker '{speaker_name}' not available for {language_code}. "
                f"Available speakers: {', '.join(LANGUAGE_SPEAKERS[language_code]['available'])}"
            )

    # Build description with speaker name
    description = (
        f"{speaker_name} speaks with a clear voice with slow speed "
        f"with a moderate speed and pitch. The recording is of very high quality, "
        f"with the speaker's voice sounding clear and very close up."
    )

    return description

@app.on_event("startup")
async def load_model():
    """Load the model once when the server starts"""
    global model, tokenizer, description_tokenizer, device

    print("Loading model... This may take a while on first run.")

    # Set device: CUDA (NVIDIA GPU) > MPS (Apple Silicon) > CPU
    if torch.cuda.is_available():
        device = "cuda"
        print(f"Using device: {device} ({torch.cuda.get_device_name(0)})")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    elif torch.backends.mps.is_available():
        device = "mps"
        print(f"Using device: {device} (Apple Metal)")
    else:
        device = "cpu"
        print(f"Using device: {device}")

    # Load the model and tokenizers
    model = ParlerTTSForConditionalGeneration.from_pretrained("ai4bharat/indic-parler-tts").to(device)
    tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts")
    description_tokenizer = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)

    print("Model loaded successfully! Server is ready.")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Indic Parler TTS Server is running",
        "device": device
    }

@app.post("/generate")
async def generate_audio(request: TTSRequest):
    """
    Generate audio from text using the TTS model

    Parameters:
    - text: The text to convert to speech
    - language_code: The ISO 639 language code (e.g., 'hi', 'en', 'ta', 'bn')
    - speaker_name: Optional speaker name. If not provided, uses first recommended speaker
    - custom_description: Optional custom voice description (overrides speaker-based description)

    Returns: Audio file in WAV format
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        # Get description - use custom if provided, otherwise build from language/speaker
        if request.custom_description:
            description = request.custom_description
        else:
            try:
                description = get_speaker_description(request.language_code, request.speaker_name)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Tokenize inputs
        description_input_ids = description_tokenizer(description, return_tensors="pt").to(device)
        prompt_input_ids = tokenizer(request.text, return_tensors="pt").to(device)

        # Generate audio
        generation = model.generate(
            input_ids=description_input_ids.input_ids,
            attention_mask=description_input_ids.attention_mask,
            prompt_input_ids=prompt_input_ids.input_ids,
            prompt_attention_mask=prompt_input_ids.attention_mask
        )

        # Convert audio to numpy array
        audio_arr = generation.cpu().numpy().squeeze()

        # Create in-memory buffer for WAV file
        buffer = io.BytesIO()
        sf.write(buffer, audio_arr, model.config.sampling_rate, format='WAV')
        buffer.seek(0)

        # Return audio buffer directly
        return Response(
            content=buffer.read(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=output.wav"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy" if model is not None else "loading",
        "model_loaded": model is not None,
        "device": device
    }

@app.get("/languages")
async def list_languages():
    """List all supported languages and their available speakers"""
    return {
        "languages": LANGUAGE_SPEAKERS
    }

@app.get("/languages/{language_code}")
async def get_language_info(language_code: str):
    """Get speaker information for a specific language"""
    language_code = language_code.lower()
    if language_code not in LANGUAGE_SPEAKERS:
        raise HTTPException(
            status_code=404,
            detail=f"Language '{language_code}' not found. Available languages: {', '.join(LANGUAGE_SPEAKERS.keys())}"
        )
    return {
        "language": language_code,
        "speakers": LANGUAGE_SPEAKERS[language_code]
    }
