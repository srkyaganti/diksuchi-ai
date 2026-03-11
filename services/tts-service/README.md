# Indic Parler TTS Service

GPU-accelerated text-to-speech service for 18+ Indian languages using [ParlerTTS](https://github.com/huggingface/parler-tts).

## Features

- **18+ Indian Languages**: Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, Assamese, and more
- **Multiple Speakers**: Each language has multiple speaker voices with recommended defaults
- **GPU Acceleration**: CUDA support for fast audio generation
- **Apple Silicon**: MPS support for Mac M1/M2/M3
- **RESTful API**: Simple FastAPI endpoints for integration
- **Custom Voice Descriptions**: Override speaker defaults with custom descriptions

## Supported Languages

| Code | Language | Available Speakers |
|------|----------|-------------------|
| `as` | Assamese | Amit, Sita, Poonam, Rakesh |
| `bn` | Bengali | Arjun, Aditi, Tapan, Rashmi, Arnav, Riya |
| `brx` | Bodo | Bikram, Maya, Kalpana |
| `hne` | Chhattisgarhi | Bhanu, Champa |
| `doi` | Dogri | Karan |
| `en` | English | Thoma, Mary, Swapna, Dinesh, and more |
| `gu` | Gujarati | Yash, Neha |
| `hi` | Hindi | Rohit, Divya, Aman, Rani |
| `kn` | Kannada | Suresh, Anu, Chetan, Vidya |
| `ml` | Malayalam | Anjali, Anju, Harish |
| `mni` | Manipuri | Laishram, Ranjit |
| `mr` | Marathi | Sanjay, Sunita, Nikhil, Radha, Varun, Isha |
| `ne` | Nepali | Amrita |
| `or` | Odia | Manas, Debjani |
| `pa` | Punjabi | Divjot, Gurpreet |
| `sa` | Sanskrit | Aryan |
| `ta` | Tamil | Kavitha, Jaya |
| `te` | Telugu | Prakash, Lalitha, Kiran |

## Quick Start

### Using Docker (Recommended)

```bash
# From project root
docker-compose up tts-service

# Or build and run standalone
docker build -t diksuchi-tts .
docker run -p 8002:8002 --gpus all -e TTS_HF_TOKEN=your_token diksuchi-tts
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TTS_HF_TOKEN=your_huggingface_token

# Run server
python server.py
```

The service will be available at `http://localhost:8002`.

## API Endpoints

### `GET /`

Health check endpoint.

**Response:**
```json
{
  "status": "running",
  "model": "ai4bharat/indic-parler-tts",
  "device": "cuda"
}
```

### `GET /health`

Detailed health check.

### `POST /generate`

Generate audio from text.

**Request Body:**
```json
{
  "text": "नमस्ते, आप कैसे हैं?",
  "language_code": "hi",
  "speaker_name": "Rohit",
  "custom_description": null
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to convert to speech |
| `language_code` | string | Yes | ISO 639 language code (e.g., `hi`, `en`) |
| `speaker_name` | string | No | Speaker name (uses recommended if omitted) |
| `custom_description` | string | No | Custom voice description |

**Response:** WAV audio file (`audio/wav`)

### `GET /languages`

List all supported languages and speakers.

### `GET /languages/{language_code}`

Get speaker information for a specific language.

## Testing

### Test with curl

```bash
# Health check
curl http://localhost:8002/health

# Generate audio
curl -X POST "http://localhost:8002/generate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "language_code": "en"}' \
  --output output.wav

# List languages
curl http://localhost:8002/languages
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_MODEL_NAME` | `ai4bharat/indic-parler-tts` | HuggingFace model name |
| `TTS_DEVICE` | `auto` | Device: `auto`, `cuda`, `mps`, `cpu` |
| `TTS_PORT` | `8002` | Server port |
| `TTS_HF_TOKEN` | - | HuggingFace token (or use `HF_TOKEN`) |

## API Documentation

Once running, access the interactive API docs at:
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

## Notes

- First run downloads the model (~2-3GB)
- GPU strongly recommended for reasonable generation speed
- CPU mode works but is significantly slower
- Requires HuggingFace token for gated model access
