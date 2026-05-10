#!/bin/bash
# wait-infra.sh — Wait for Ollama + Docker Desktop, start compose, wait healthy
set -euo pipefail

PROJECT_DIR="/home/avision/workspace/diksuchi-ai"
OLLAMA_URL="http://localhost:11434"
MAX_WAIT=180  # seconds (Docker Desktop can be slow to start)

log() { echo "[infra] $(date '+%H:%M:%S') $*"; }

# --- 1. Wait for Ollama on Windows host ---
log "Waiting for Ollama at $OLLAMA_URL ..."
elapsed=0
until curl -sf "$OLLAMA_URL/api/tags" >/dev/null 2>&1; do
    sleep 3
    elapsed=$((elapsed + 3))
    if [ "$elapsed" -ge "$MAX_WAIT" ]; then
        log "ERROR: Ollama not reachable after ${MAX_WAIT}s"
        exit 1
    fi
done
log "Ollama is up (${elapsed}s)"

# --- 2. Wait for Docker Desktop WSL integration ---
# Docker Desktop creates this socket when its WSL integration is ready
log "Waiting for Docker Desktop WSL integration ..."
elapsed=0
until [ -S /var/run/docker.sock ] && docker info >/dev/null 2>&1; do
    sleep 3
    elapsed=$((elapsed + 3))
    if [ "$elapsed" -ge "$MAX_WAIT" ]; then
        log "ERROR: Docker not available after ${MAX_WAIT}s"
        log "Ensure Docker Desktop is running with WSL integration enabled"
        exit 1
    fi
done
log "Docker is up (${elapsed}s)"

# --- 3. Start docker compose ---
log "Starting postgres & redis via docker compose ..."
cd "$PROJECT_DIR"
docker compose up -d postgres redis

# --- 4. Wait for postgres healthy ---
log "Waiting for postgres ..."
elapsed=0
until docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge 60 ]; then
        log "ERROR: Postgres not healthy after 60s"
        exit 1
    fi
done
log "Postgres is healthy (${elapsed}s)"

# --- 5. Wait for redis healthy ---
log "Waiting for redis ..."
elapsed=0
until docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge 60 ]; then
        log "ERROR: Redis not healthy after 60s"
        exit 1
    fi
done
log "Redis is healthy (${elapsed}s)"

log "All infrastructure ready."
