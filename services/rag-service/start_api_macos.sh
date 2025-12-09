#!/bin/bash

# RAG Service API Startup Script for macOS
# Runs FastAPI server only

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
SERVICE_DIR="$PROJECT_ROOT/services/rag-service"

cd "$SERVICE_DIR"

REDIS_HOST="127.0.0.1"
REDIS_PORT="6379"

CHROMADB_HOST="127.0.0.1"
CHROMADB_PORT="8000"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source <(cat "$PROJECT_ROOT/.env" | grep -v '^#' | grep -v '^$' | sed 's/#.*$//')
    set +a
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate

# Check dependencies
echo "Checking Redis connection..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping > /dev/null 2>&1 || {
    echo "ERROR: Redis not running. Start Redis first:"
    echo "  brew services start redis"
    exit 1
}

echo "Checking ChromaDB connection..."
curl -s http://$CHROMADB_HOST:$CHROMADB_PORT/api/v2/heartbeat > /dev/null 2>&1 || {
    echo "ERROR: ChromaDB not running. Start ChromaDB first:"
    echo "  ./scripts/start_chromadb_macos.sh"
    exit 1
}

# Check embedding model exists
if [ ! -f "models/bge-m3.gguf" ]; then
    echo "WARNING: Embedding model not found at models/bge-m3.gguf"
    echo "Please download from: https://huggingface.co/lm-kit/bge-m3-gguf"
fi

# Start FastAPI server
echo "Starting RAG Service API on port 5001..."
python main.py

trap "echo 'Stopping RAG Service API...'; exit" SIGINT SIGTERM
