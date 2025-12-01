#!/bin/bash

# STT Service Startup Script for macOS

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
SERVICE_DIR="$PROJECT_ROOT/services/stt-service"

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
    echo "  pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu"
    echo "  pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate

# Set API port
export API_PORT=8001

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "WARNING: FFmpeg not found. Install with: brew install ffmpeg"
fi

# Start STT service
echo "Starting STT Service on port 8001..."
echo "Model: $WHISPER_MODEL"
echo "Device: CPU/MPS (macOS)"
echo ""
echo "Note: First run will download Whisper model (~6GB)"
echo "      Make sure HF_TOKEN is set in .env if needed"
echo ""

python stt_server.py
