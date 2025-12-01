#!/bin/bash

# ChromaDB Startup Script for macOS

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv_chromadb" ]; then
    echo "ERROR: ChromaDB virtual environment not found. Please create it first:"
    echo "  python3.11 -m venv venv_chromadb"
    echo "  source venv_chromadb/bin/activate"
    echo "  pip install chromadb==1.3.5"
    exit 1
fi

# Activate virtual environment
source venv_chromadb/bin/activate

# Set data directory
export CHROMA_DATA_PATH="$PROJECT_ROOT/data/chromadb_data"
export IS_PERSISTENT="TRUE"
export ANONYMIZED_TELEMETRY="FALSE"

# Create data directory if it doesn't exist
mkdir -p "$CHROMA_DATA_PATH"

# Start ChromaDB server
echo "Starting ChromaDB on port 8000..."
echo "Data path: $CHROMA_DATA_PATH"
echo ""

chroma run --host 0.0.0.0 --port 8000 --path "$CHROMA_DATA_PATH"
