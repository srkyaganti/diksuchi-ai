#!/bin/bash

# Download BGE-M3 GGUF Embedding Model
# This script downloads the BGE-M3 GGUF model required for embeddings
# Uses the modern Hugging Face CLI (hf)

set -e  # Exit on error

MODEL_DIR="models"
MODEL_FILE="bge-m3.gguf"
TEMP_FILE="bge-m3-Q8_0.gguf"
HF_REPO="lm-kit/bge-m3-gguf"

echo "🔽 Downloading BGE-M3 GGUF Embedding Model..."
echo "   Repository: $HF_REPO"
echo "   Size: ~635MB (Q8_0 quantization)"
echo ""

# Check if hf CLI is installed
if ! command -v hf &> /dev/null; then
    echo "❌ Hugging Face CLI not found!"
    echo "   Install with: pip install -U huggingface_hub"
    echo "   Or use curl: curl -LsSf https://hf.co/cli/install.sh | sh"
    exit 1
fi

# Create models directory
mkdir -p "$MODEL_DIR"

# Check if model already exists
if [ -f "$MODEL_DIR/$MODEL_FILE" ]; then
    echo "✅ Model already exists at $MODEL_DIR/$MODEL_FILE"
    echo "   Delete it first if you want to re-download"
    exit 0
fi

# Download model using modern hf CLI
echo "📥 Downloading from Hugging Face..."
hf download \
    "$HF_REPO" \
    "$TEMP_FILE" \
    --local-dir "$MODEL_DIR"

# Rename to expected filename
echo "📝 Renaming $TEMP_FILE to $MODEL_FILE..."
mv "$MODEL_DIR/$TEMP_FILE" "$MODEL_DIR/$MODEL_FILE"

echo ""
echo "✅ Model downloaded successfully!"
echo "   Location: $MODEL_DIR/$MODEL_FILE"
echo "   Size: $(du -h "$MODEL_DIR/$MODEL_FILE" | cut -f1)"
echo ""
echo "🚀 You can now start the python-worker:"
echo "   docker-compose up -d python-worker"
