# Diksuchi LLM Service

Unified LLM inference service with OpenAI-compatible API. This service replaces external dependencies like LM Studio and Ollama with a self-hosted, containerized solution.

## Features

- **OpenAI-Compatible API**: Drop-in replacement for LM Studio - `/v1/chat/completions` endpoint
- **GPU Acceleration**: Automatic CUDA support for NVIDIA GPUs
- **GGUF Models**: Memory-efficient quantized models via llama-cpp-python
- **Docker Integration**: Seamlessly integrates with existing Diksuchi-AI services
- **Health Checks**: Built-in health monitoring for Docker Compose

## Quick Start

### 1. Download a GGUF Model

Download a quantized GGUF model and place it in `models/llm/`:

```bash
# Create models directory
mkdir -p ../../models/llm

# Example: Download Llama 3.2 3B Instruct (recommended for testing)
# You can use huggingface-cli or wget
huggingface-cli download \
  bartowski/Llama-3.2-3B-Instruct-GGUF \
  Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  --local-dir ../../models/llm

# Or download any other GGUF model you prefer
```

### 2. Configure Environment

Update your `.env` file in the project root:

```env
# LLM Service Configuration
MODEL_PATH=/app/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
N_GPU_LAYERS=99  # Use all GPU layers (set to 0 for CPU)
CHAT_FORMAT=llama-3
```

### 3. Build and Start

```bash
# From project root
docker-compose build llm-service
docker-compose up -d llm-service

# Check health
curl http://localhost:8003/v1/models
```

### 4. Test the API

```bash
# Test chat completion
curl http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.2-3b",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
  }'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `/app/models/your-model.gguf` | Path to GGUF model file |
| `N_GPU_LAYERS` | `0` | Number of layers to offload to GPU (`-1` or `99` = all, `0` = CPU only) |
| `CHAT_FORMAT` | `llama-3` | Chat template format (llama-2, llama-3, chatml, mistral-instruct, etc.) |
| `API_PORT` | `8003` | Port for API server |

### GPU Support

**NVIDIA GPU (CUDA)**:
- Dockerfile is configured for CUDA by default
- Set `N_GPU_LAYERS=99` to use GPU
- Requires NVIDIA Docker runtime

**CPU Only**:
- Set `N_GPU_LAYERS=0` in environment
- Slower but works without GPU

**Apple Silicon (MPS)**:
- Not recommended in Docker (limited support)
- Run natively on macOS for best performance

## API Endpoints

### Chat Completions: `POST /v1/chat/completions`

OpenAI-compatible chat endpoint with streaming support.

**Request**:
```json
{
  "model": "your-model-name",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is RAG?"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

**Response**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1699123456,
  "model": "your-model-name",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "RAG stands for Retrieval-Augmented Generation..."
    },
    "finish_reason": "stop"
  }]
}
```

### Models List: `GET /v1/models`

List available models.

### Health Check: `GET /v1/models`

Used by Docker Compose to verify service health.

## Integration with Next.js

The Next.js app uses `@ai-sdk/openai-compatible` which already supports this API format. Just update the base URL:

```typescript
// services/web/src/app/api/chat/route.ts
const llmService = createOpenAICompatible({
  name: "llm-service",
  baseURL: "http://llm-service:8003/v1"
});
```

## Troubleshooting

### Model Not Found Error

```
FileNotFoundError: Model file not found: /app/models/your-model.gguf
```

**Solution**: Download a GGUF model and place it in `models/llm/`, then update `MODEL_PATH` in `.env`.

### Out of Memory Error

```
CUDA out of memory
```

**Solution**:
- Use a smaller model (3B or 7B instead of 13B+)
- Reduce `N_GPU_LAYERS` (e.g., set to 20 instead of 99)
- Use a more quantized model (Q4_K_M instead of Q8_0)

### Slow Inference

**CPU Mode**: If `N_GPU_LAYERS=0`, inference will be slow.
**Solution**: Enable GPU with `N_GPU_LAYERS=99`

### Container Won't Start

**Check logs**:
```bash
docker-compose logs llm-service
```

**Common issues**:
- NVIDIA runtime not installed: Install nvidia-docker2
- Model file missing: Check `MODEL_PATH`
- Port conflict: Port 8003 already in use

## Performance Tips

1. **Use Quantized Models**: Q4_K_M offers best size/quality balance
2. **Enable GPU**: Set `N_GPU_LAYERS=99` for 10-20x speedup
3. **Choose Right Model Size**:
   - 3B models: ~3GB VRAM, fast inference
   - 7B models: ~5-8GB VRAM, good quality
   - 13B+ models: 16GB+ VRAM, best quality

## Recommended Models

| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| Llama-3.2-3B-Instruct | 2.5GB | 4GB | Development, fast inference |
| Llama-3.1-8B-Instruct | 5GB | 8GB | Balanced quality/speed |
| Mistral-7B-Instruct | 5GB | 8GB | Good reasoning |
| Qwen2.5-7B-Instruct | 5GB | 8GB | Strong multi-lingual |

Download quantized GGUF versions (Q4_K_M or Q5_K_M) from [HuggingFace](https://huggingface.co/models?search=gguf).

## License

Part of the Diksuchi-AI platform.
