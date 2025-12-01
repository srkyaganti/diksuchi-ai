#!/bin/bash

# Master Startup Script for All Services (macOS)
# Starts all 7 services in dependency order

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Starting Diksuchi-AI Platform (macOS)"
echo "=========================================="

# 1. Start PostgreSQL (if not already running)
echo "[1/7] Starting PostgreSQL..."
brew services start postgresql@16 2>/dev/null
sleep 2

# 2. Start Redis (if not already running)
echo "[2/7] Starting Redis..."
brew services start redis 2>/dev/null
sleep 2

# 3. Start ChromaDB
echo "[3/7] Starting ChromaDB..."
./scripts/start_chromadb_macos.sh > logs/chromadb.log 2>&1 &
CHROMADB_PID=$!
echo "$CHROMADB_PID" > .pids/chromadb.pid
echo "    PID: $CHROMADB_PID"
sleep 5

# 4. Start RAG Service
echo "[4/7] Starting RAG Service..."
cd services/rag-service
./start_rag_macos.sh > ../../logs/rag-service.log 2>&1 &
RAG_PID=$!
echo "$RAG_PID" > ../../.pids/rag.pid
echo "    PID: $RAG_PID"
cd "$PROJECT_ROOT"
sleep 5

# 5. Start STT Service
echo "[5/7] Starting STT Service..."
cd services/stt-service
./start_stt_macos.sh > ../../logs/stt-service.log 2>&1 &
STT_PID=$!
echo "$STT_PID" > ../../.pids/stt.pid
echo "    PID: $STT_PID"
cd "$PROJECT_ROOT"
sleep 10  # Wait for Whisper model to load

# 6. Start TTS Service
echo "[6/7] Starting TTS Service..."
cd services/tts-service
./start_tts_macos.sh > ../../logs/tts-service.log 2>&1 &
TTS_PID=$!
echo "$TTS_PID" > ../../.pids/tts.pid
echo "    PID: $TTS_PID"
cd "$PROJECT_ROOT"
sleep 5

# 7. Start Next.js Web App
echo "[7/7] Starting Next.js Web App..."
cd services/web
# Use pnpm dev directly instead of the interactive script
pnpm dev > ../../logs/web-app.log 2>&1 &
WEB_PID=$!
echo "$WEB_PID" > ../../.pids/web.pid
echo "    PID: $WEB_PID"
cd "$PROJECT_ROOT"
sleep 5

echo ""
echo "=========================================="
echo "All services started!"
echo "=========================================="
echo "Process IDs:"
echo "  ChromaDB:    $CHROMADB_PID"
echo "  RAG:         $RAG_PID"
echo "  STT:         $STT_PID"
echo "  TTS:         $TTS_PID"
echo "  Web:         $WEB_PID"
echo ""
echo "Service URLs:"
echo "  Web App:     http://localhost:3000"
echo "  ChromaDB:    http://localhost:8000"
echo "  RAG:         http://localhost:5001"
echo "  STT:         http://localhost:8001"
echo "  TTS:         http://localhost:8002"
echo ""
echo "Note: Using LM Studio for LLM inference (localhost:1234)"
echo ""
echo "Commands:"
echo "  Stop all:    ./scripts/stop_all_macos.sh"
echo "  Check logs:  tail -f logs/*.log"
echo "  Health:      ./scripts/health_check_macos.sh"
echo "=========================================="
