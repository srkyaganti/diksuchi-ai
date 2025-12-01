#!/bin/bash

# Stop All Services Script (macOS)

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Stopping Diksuchi-AI Platform (macOS)"
echo "=========================================="

# Function to kill process by PID file
kill_by_pidfile() {
    local pidfile=$1
    local service_name=$2

    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping $service_name (PID: $pid)..."
            kill $pid 2>/dev/null
            sleep 2
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo "  Force stopping $service_name..."
                kill -9 $pid 2>/dev/null
            fi
        else
            echo "$service_name (PID: $pid) not running"
        fi
        rm -f "$pidfile"
    fi
}

# Stop services in reverse order
kill_by_pidfile ".pids/web.pid" "Web App"
kill_by_pidfile ".pids/tts.pid" "TTS Service"
kill_by_pidfile ".pids/stt.pid" "STT Service"
kill_by_pidfile ".pids/rag.pid" "RAG Service"
kill_by_pidfile ".pids/chromadb.pid" "ChromaDB"

# Optional: Stop infrastructure services
echo ""
read -p "Stop Redis and PostgreSQL? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping Redis..."
    brew services stop redis 2>/dev/null
    echo "Stopping PostgreSQL..."
    brew services stop postgresql@16 2>/dev/null
fi

# Clean up PID directory
rm -f .pids/*.pid

echo ""
echo "=========================================="
echo "All services stopped!"
echo "=========================================="
