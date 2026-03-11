# Faster Whisper STT Service

GPU-accelerated speech-to-text service using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## Features

- Fast GPU-accelerated transcription using CTranslate2
- Multiple model support (tiny, base, small, medium, large-v2, large-v3, distil-large-v3, turbo)
- Voice Activity Detection (VAD) filtering
- Language auto-detection
- Batch transcription support
- RESTful API with FastAPI

## Prerequisites

- Docker with NVIDIA Container Toolkit (for GPU)
- NVIDIA GPU with CUDA support
- FFmpeg (for mp3/m4a format support)

## Quick Start

### Using Docker (Recommended)

```bash
# From project root
docker-compose up stt-service

# Or build and run standalone
docker build -t diksuchi-stt .
docker run -p 8080:8080 --gpus all -e STT_HF_TOKEN=your_token diksuchi-stt
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
```

The service will be available at `http://localhost:8080`.

## API Endpoints

### `GET /`

Health check endpoint.

**Response:**
```json
{
  "status": "running",
  "model": "large-v3",
  "device": "cuda",
  "compute_type": "float16"
}
```

### `GET /health`

Detailed health check.

### `POST /transcribe`

Transcribe a single audio file.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "language": "en",
  "language_probability": 0.98,
  "text": "Full transcription text...",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Segment text"
    }
  ]
}
```

### `POST /transcribe-batch`

Transcribe multiple audio files.

**Request:** `multipart/form-data` with multiple `files` fields

## Testing

### Test with curl

```bash
# Health check
curl http://localhost:8080/health

# Transcribe audio
curl -X POST "http://localhost:8080/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3"
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `STT_MODEL_NAME` | `large-v3` | Whisper model size |
| `STT_DEVICE` | `cuda` | Device (cuda/cpu) |
| `STT_COMPUTE_TYPE` | `float16` | Compute precision |
| `STT_PORT` | `8080` | Server port |
| `STT_HF_TOKEN` | - | HuggingFace token (or use `HF_TOKEN`) |

### Available Models

- `tiny` - Fastest, lowest accuracy
- `base` - Fast, basic accuracy
- `small` - Good balance
- `medium` - Better accuracy
- `large-v2` - High accuracy
- `large-v3` - Highest accuracy (default)
- `distil-large-v3` - Distilled version, faster
- `turbo` - Optimized for speed

## Supported Audio Formats

- WAV
- MP3
- M4A
- FLAC
- OGG
- And other formats supported by `soundfile`

## API Documentation

Once running, access the interactive API docs at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`
