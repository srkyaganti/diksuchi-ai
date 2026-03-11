# Voice Service

Combined Speech-to-Text (STT) and Text-to-Speech (TTS) service for Diksuchi AI.

## Features

- **STT**: GPU-accelerated transcription using Faster Whisper (large-v3)
- **TTS**: Text-to-speech for 18+ Indian languages using Indic Parler TTS
- **Namespaced endpoints**: `/stt/*` and `/tts/*` for clear separation
- **Progressive loading**: Shows model loading progress on startup

## Hardware Requirements

- **GPU**: NVIDIA GPU with CUDA support (tested on RTX 5090, 32GB VRAM)
- **RAM**: 64GB recommended
- **Storage**: ~10GB for models

**Memory Usage**:
- STT model: ~3GB VRAM
- TTS model: ~2-3GB VRAM
- Total: ~5-6GB VRAM

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your HF_TOKEN
```

### 3. Run Service

```bash
python server.py
```

The service will start on port 8000 by default.

### 4. Verify

```bash
# Check health
curl http://localhost:8000/health

# Check STT health
curl http://localhost:8000/stt/health

# Check TTS health
curl http://localhost:8000/tts/health
```

## API Endpoints

### STT Endpoints

#### `POST /stt/transcribe`
Transcribe audio file to text.

**Request**: multipart/form-data with `file` field (audio file)

**Response**:
```json
{
  "language": "hi",
  "language_probability": 0.95,
  "text": "Transcribed text here",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Segment text"
    }
  ]
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/stt/transcribe \
  -F "file=@audio.wav"
```

### TTS Endpoints

#### `POST /tts/generate`
Generate audio from text.

**Request**:
```json
{
  "text": "Text to convert to speech",
  "language_code": "hi",
  "speaker_name": "Rohit",
  "custom_description": null
}
```

**Response**: WAV audio file

**Example**:
```bash
curl -X POST http://localhost:8000/tts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "नमस्ते, आप कैसे हैं?",
    "language_code": "hi"
  }' \
  --output output.wav
```

#### `GET /tts/languages`
List all supported languages and speakers.

**Response**:
```json
{
  "languages": {
    "hi": {
      "available": ["Rohit", "Divya", "Aman", "Rani"],
      "recommended": ["Rohit", "Divya"]
    },
    ...
  }
}
```

#### `GET /tts/languages/{language_code}`
Get speaker information for a specific language.

**Example**:
```bash
curl http://localhost:8000/tts/languages/hi
```

### Health Endpoints

#### `GET /health` or `GET /`
Combined health check for both services.

**Response**:
```json
{
  "status": "healthy",
  "stt": {
    "loaded": true,
    "model": "large-v3",
    "device": "cuda"
  },
  "tts": {
    "loaded": true,
    "model": "ai4bharat/indic-parler-tts",
    "device": "cuda"
  }
}
```

#### `GET /stt/health`
STT-specific health check.

#### `GET /tts/health`
TTS-specific health check.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STT_MODEL_NAME` | `large-v3` | Whisper model size |
| `STT_DEVICE` | `cuda` | Device for STT (cuda/cpu) |
| `STT_COMPUTE_TYPE` | `float16` | Compute precision |
| `TTS_MODEL_NAME` | `ai4bharat/indic-parler-tts` | TTS model name |
| `TTS_DEVICE` | `auto` | Device for TTS (auto/cuda/cpu/mps) |
| `VOICE_SERVICE_PORT` | `8000` | Service port |
| `HF_TOKEN` | - | HuggingFace API token |

## Supported Languages

The TTS service supports 18+ Indian languages:

- Hindi (hi), Bengali (bn), Tamil (ta), Telugu (te)
- Marathi (mr), Gujarati (gu), Kannada (kn), Malayalam (ml)
- Punjabi (pa), Assamese (as), Odia (or), Nepali (ne)
- Sanskrit (sa), English (en), and more...

See `/tts/languages` for complete list with available speakers.

## Docker

### Build

```bash
docker build -t diksuchi-voice-service .
```

### Run

```bash
docker run -d \
  --gpus all \
  -p 8000:8000 \
  -e HF_TOKEN=your_token_here \
  diksuchi-voice-service
```

### Docker Compose

```yaml
services:
  voice-service:
    build: ./services/voice-service
    ports:
      - "8000:8000"
    environment:
      - HF_TOKEN=${HF_TOKEN}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

## Troubleshooting

### Model download fails
- Ensure `HF_TOKEN` is set correctly
- Check internet connection
- Verify you have access to the models on HuggingFace

### Out of memory errors
- Reduce model size: `STT_MODEL_NAME=medium`
- Use CPU: `STT_DEVICE=cpu` and `TTS_DEVICE=cpu`
- Close other GPU processes

### Slow startup
- First run downloads models (~10GB)
- Subsequent runs load from cache
- Use smaller models for faster startup

## Architecture

```
Voice Service
├── FastAPI Application
│   ├── STT Module
│   │   └── Faster Whisper (CTranslate2)
│   └── TTS Module
│       └── Indic Parler TTS
├── Shared Components
│   ├── Audio processing (soundfile, numpy)
│   ├── HuggingFace integration
│   └── Health monitoring
└── GPU Acceleration (CUDA)
```

## License

Part of the Diksuchi AI project.
