#!/bin/bash
# Preload Ollama models into memory to eliminate cold start latency
# Run this after Ollama is ready

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
TIMEOUT=120
ELAPSED=0

echo "⏳ Waiting for Ollama to be ready at $OLLAMA_HOST..."

# Wait for Ollama to be ready
while ! curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; do
    if (( ELAPSED >= TIMEOUT )); then
        echo "❌ Ollama not ready after ${TIMEOUT}s - skipping model preload"
        exit 1
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo "   Still waiting... (${ELAPSED}s)"
done

echo "✅ Ollama is ready!"

# Models to preload - customize based on your setup
# From .env: LLM_MODEL=gemma4:e4b
MODELS=("gemma4:e4b")

echo "🚀 Preloading models into memory (this may take a few minutes)..."

for model in "${MODELS[@]}"; do
    echo "   Loading: $model..."
    curl -s -X POST "$OLLAMA_HOST/api/generate" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$model\", \"stream\": false, \"keep_alive\": -1}" \
        > /dev/null 2>&1 &
done

# Wait for all background preload jobs
wait
echo "✅ Models preloaded and ready!"
