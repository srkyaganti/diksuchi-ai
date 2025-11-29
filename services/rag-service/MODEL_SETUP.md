# Model Setup Guide

This guide explains how to manage the BGE-M3 GGUF embedding model (~2GB) for the Python RAG worker.

## ⚠️ Important: Don't Commit Models to Git

Model files are **excluded from git** (see `.gitignore`) because:
- Large file size (~2GB) bloats repository
- GitHub has file size limits (100MB per file)
- Models should be downloaded separately

---

## Quick Start

### Option 1: Local Download (Recommended for Development)

```bash
cd python-worker

# Run the download script
./download-model.sh
```

This will:
- Download BGE-M3 GGUF (~605MB, Q8_0 quantization) from Hugging Face
- Place it in `python-worker/models/bge-m3.gguf`
- Model will be bind-mounted into Docker container

**Pros:**
- ✅ Fast development (no rebuilding Docker images)
- ✅ Easy to update/change models
- ✅ Works with `docker-compose` out of the box

**Cons:**
- ❌ Requires local download on each machine

---

### Option 2: Docker Volume (Production)

For production deployments, use a named Docker volume:

1. **Edit `docker-compose.yml`**:
   ```yaml
   volumes:
     # Comment out bind mount
     # - ./python-worker/models:/app/models

     # Uncomment docker volume
     - python_models:/app/models
   ```

2. **Download model into volume**:
   ```bash
   # Start a temporary container to download
   docker run --rm -it \
     -v frontend_python_models:/app/models \
     python:3.11-slim bash

   # Inside container:
   pip install -U huggingface_hub
   hf download \
     lm-kit/bge-m3-gguf \
     bge-m3-Q8_0.gguf \
     --local-dir /app/models
   mv /app/models/bge-m3-Q8_0.gguf /app/models/bge-m3.gguf
   exit
   ```

**Pros:**
- ✅ Persistent across container restarts
- ✅ Shared across multiple containers
- ✅ Better for production

**Cons:**
- ❌ Harder to update
- ❌ Not visible on host filesystem

---

### Option 3: Cloud Storage + Download on Start

For production deployments with CI/CD:

1. **Upload model to cloud storage** (S3, GCS, Azure Blob)

2. **Create init script**:
   ```bash
   # python-worker/init-models.sh
   #!/bin/bash

   if [ ! -f /app/models/bge-m3.gguf ]; then
     echo "Downloading model from S3..."
     aws s3 cp s3://your-bucket/models/bge-m3.gguf /app/models/
   fi
   ```

3. **Update Dockerfile**:
   ```dockerfile
   COPY init-models.sh /app/
   RUN chmod +x /app/init-models.sh
   CMD ["sh", "-c", "/app/init-models.sh && uvicorn main:app"]
   ```

**Pros:**
- ✅ Automated deployment
- ✅ Version controlled (via S3 versioning)
- ✅ Works in CI/CD pipelines

**Cons:**
- ❌ Requires cloud infrastructure
- ❌ Download on every cold start (unless cached)

---

### Option 4: Git LFS (Not Recommended)

**We don't recommend this because:**
- ❌ Costs money on GitHub for bandwidth
- ❌ Cloning the repo becomes slow
- ❌ CI/CD pipelines pull large files every time

But if you must:
```bash
git lfs install
git lfs track "python-worker/models/*.gguf"
git add python-worker/models/bge-m3.gguf
```

---

## Manual Download (Alternative)

If `huggingface-cli` doesn't work:

1. **Visit**: https://huggingface.co/lm-kit/bge-m3-gguf
2. **Download**: `bge-m3-Q8_0.gguf` (~605MB)
3. **Rename to**: `bge-m3.gguf` and place in `python-worker/models/`

---

## Verification

Check if the model is loaded:

```bash
# Check file exists
ls -lh python-worker/models/bge-m3.gguf

# Start python-worker
docker-compose up python-worker

# Check logs - should NOT show "Embedding model not found"
docker-compose logs python-worker | grep -i "embedding model"
```

Expected output:
```
✅ Embedding model loaded: models/bge-m3.gguf
```

---

## Tech Stack Impact

### What You Can Skip

✅ **Ollama for embeddings** - Using local GGUF file instead

### What You Still Need

❌ **Ollama/LM Studio for LLM** - Next.js still uses it for chat (`krutrim-ai-labs_Krutrim-2-instruct`)

### Architecture

```
┌─────────────────────────────────────┐
│ Next.js (Chat Interface)            │
│  ↓                                   │
│ LM Studio/Ollama                     │ ← Still need for LLM
│  → krutrim-ai-labs_Krutrim-2        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Python Worker (RAG/Embeddings)      │
│  ↓                                   │
│ Local GGUF File                      │ ← Skip Ollama here
│  → bge-m3.gguf (2GB)                │
└─────────────────────────────────────┘
```

---

## Troubleshooting

### "Embedding model not found"
- Run `./download-model.sh`
- Check `python-worker/models/bge-m3.gguf` exists
- Verify docker volume mount in `docker-compose.yml`

### "Failed to load Llama model"
- Model might be corrupted - re-download
- Check disk space (need ~2GB free)
- Verify file permissions

### Slow startup
- First load takes ~10-30 seconds to load model into memory (605MB Q8_0 model)
- Check Docker resource limits (need 2GB+ RAM for model)

---

## Model Information

**BGE-M3 GGUF**
- **Size**: ~605MB (Q8_0 quantization)
- **Source**: [lm-kit/bge-m3-gguf](https://huggingface.co/lm-kit/bge-m3-gguf)
- **Original**: [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)
- **Embedding Dimensions**: 1024
- **Languages**: Multilingual (100+ languages)
- **License**: MIT

---

## Summary

**Recommended for you:**
```bash
# 1. Download model locally
cd /Users/srikaryaganti/workspaces/drdo/diksuchi-ai/services/rag-service
./download-model.sh

# 2. Verify in docker-compose.yml (already configured)
# - ./python-worker/models:/app/models  ✓ Enabled

# 3. Start services
cd ..
docker-compose up -d python-worker

# 4. Verify
docker-compose logs python-worker | grep "Embedding model"
```

This approach:
- ✅ Keeps models out of git
- ✅ Easy to download and update
- ✅ Works with Docker bind mount
- ✅ Reduces tech stack (no Ollama for embeddings)
