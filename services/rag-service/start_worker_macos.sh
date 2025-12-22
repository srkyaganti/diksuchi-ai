#!/bin/bash

# RAG Service Worker Startup Script for macOS
# Runs RQ worker only

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
SERVICE_DIR="$PROJECT_ROOT/services/rag-service"

cd "$SERVICE_DIR"

REDIS_HOST="127.0.0.1"
REDIS_PORT="6379"

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

# Check Ollama is running
echo "Checking Ollama connection..."
curl -s http://localhost:11434/api/tags > /dev/null 2>&1 || {
    echo "ERROR: Ollama not running. Start with:"
    echo "  ollama serve"
    echo ""
    echo "Then pull the embedding model:"
    echo "  ollama pull bge-m3"
    exit 1
}
echo "✓ Ollama is running"

# Check Redis connection
echo "Checking Redis connection..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping > /dev/null 2>&1 || {
    echo "ERROR: Redis not running. Start Redis first:"
    echo "  brew services start redis"
    exit 1
}
echo "✓ Redis is connected"

# Start RQ worker
echo "Starting RQ Worker..."
python worker.py

trap "echo 'Stopping RQ Worker...'; exit" SIGINT SIGTERM
