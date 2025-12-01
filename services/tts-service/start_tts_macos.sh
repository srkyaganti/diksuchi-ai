#!/bin/bash

# TTS Service Startup Script for macOS

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
SERVICE_DIR="$PROJECT_ROOT/services/tts-service"

cd "$SERVICE_DIR"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source <(cat "$PROJECT_ROOT/.env" | grep -v '^#' | grep -v '^$' | sed 's/#.*$//')
    set +a
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Please create it first:"
    echo "  python3.11 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate

# Set API port
export API_PORT=8002

# Start TTS service
echo "Starting TTS Service on port 8002..."
echo "Default Language: $TTS_DEFAULT_LANGUAGE"
echo ""
echo "Note: First run will download ParlerTTS model (~2-3GB)"
echo "      Make sure HF_TOKEN is set in .env if needed"
echo ""

python server.py
