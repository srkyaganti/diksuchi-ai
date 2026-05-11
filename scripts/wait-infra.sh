#!/bin/bash
# wait-infra.sh — Wait for Ollama (Windows host) and native postgres + redis
#
# postgres + redis run as system-level systemd services (postgresql,
# redis-server) installed via apt. They start at boot, so this script
# only needs to confirm they are reachable before app services start.
set -euo pipefail

OLLAMA_URL="http://localhost:11434"
MAX_WAIT=180  # seconds (allow time for Windows-side Ollama to come up)

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

# --- 2. Wait for postgres ---
log "Waiting for postgres ..."
elapsed=0
until pg_isready -h localhost -U postgres -d diksuchi -q 2>/dev/null; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge 60 ]; then
        log "ERROR: Postgres not ready after 60s. Check: sudo systemctl status postgresql"
        exit 1
    fi
done
log "Postgres is healthy (${elapsed}s)"

# --- 3. Wait for redis ---
log "Waiting for redis ..."
elapsed=0
until redis-cli ping 2>/dev/null | grep -q PONG; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge 60 ]; then
        log "ERROR: Redis not ready after 60s. Check: sudo systemctl status redis-server"
        exit 1
    fi
done
log "Redis is healthy (${elapsed}s)"

log "All infrastructure ready."
