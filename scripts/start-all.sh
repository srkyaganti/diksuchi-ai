#!/usr/bin/env bash
# ============================================================
# Diksuchi-AI — Unified Service Launcher
#
# Starts all 6 services with a single command:
#   1. Docker infra (Postgres + Redis)
#   2. Ollama (via Windows PowerShell)
#   3. RAG API (port 5001)
#   4. RAG Worker
#   5. Voice Service (port 8001)
#   6. Web — production build (port 3000)
#
# Usage:  bash scripts/start-all.sh
# Stop:   Ctrl+C (kills everything and stops Docker)
# ============================================================

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# --------------- Colors ---------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --------------- Service dirs ---------------
RAG_DIR="$ROOT_DIR/services/rag-service"
VOICE_DIR="$ROOT_DIR/services/voice-service"
WEB_DIR="$ROOT_DIR/services/web"

# --------------- Cleanup on exit ---------------
cleanup() {
    echo -e "\n${YELLOW}${BOLD}Shutting down all services...${NC}"

    # Kill all background jobs
    kill $(jobs -p) 2>/dev/null || true
    wait 2>/dev/null || true

    # Stop Docker containers
    echo -e "${YELLOW}  Stopping Docker containers...${NC}"
    cd "$ROOT_DIR" && docker compose stop postgres redis 2>/dev/null || true

    echo -e "${GREEN}${BOLD}All services stopped.${NC}"
}
trap cleanup EXIT INT TERM

# --------------- Prefixed log helper ---------------
# Pipes stdin with a colored prefix per service
prefix_log() {
    local color="$1" name="$2"
    sed -u "s/^/${color}[${name}]${NC} /"
}

echo -e "${GREEN}${BOLD}================================================${NC}"
echo -e "${GREEN}${BOLD} Diksuchi-AI — Starting All Services${NC}"
echo -e "${GREEN}${BOLD}================================================${NC}"

# ========== [1/6] Docker Infrastructure ==========
echo -e "\n${YELLOW}[1/6] Starting Postgres + Redis (Docker)...${NC}"
cd "$ROOT_DIR"
docker compose up -d postgres redis

echo -e "${CYAN}  Waiting for containers to be healthy...${NC}"
TIMEOUT=60
ELAPSED=0
while true; do
    PG_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' diksuchi-postgres 2>/dev/null || echo "missing")
    RD_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' diksuchi-redis 2>/dev/null || echo "missing")

    if [[ "$PG_HEALTH" == "healthy" && "$RD_HEALTH" == "healthy" ]]; then
        echo -e "${GREEN}  Postgres: healthy  |  Redis: healthy${NC}"
        break
    fi

    if (( ELAPSED >= TIMEOUT )); then
        echo -e "${RED}  Timed out waiting for Docker health checks (${TIMEOUT}s)${NC}"
        echo -e "${RED}  Postgres: ${PG_HEALTH}  |  Redis: ${RD_HEALTH}${NC}"
        exit 1
    fi

    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo -e "${CYAN}  Postgres: ${PG_HEALTH}  |  Redis: ${RD_HEALTH}  (${ELAPSED}s)${NC}"
done

# ========== [2/6] Ollama (Windows side) ==========
echo -e "\n${YELLOW}[2/6] Starting Ollama (Windows PowerShell)...${NC}"
if command -v powershell.exe &>/dev/null; then
    powershell.exe -NoProfile -Command "& { \$env:OLLAMA_HOST='0.0.0.0:11434'; ollama serve }" \
        2>&1 | prefix_log "$MAGENTA" "ollama" &
    # Give Ollama a moment to bind
    sleep 3
    echo -e "${GREEN}  Ollama :11434 (Windows)${NC}"
else
    echo -e "${RED}  powershell.exe not found — is this WSL2?${NC}"
    echo -e "${RED}  Continuing without Ollama...${NC}"
fi

# ========== [3/6] RAG API ==========
echo -e "\n${YELLOW}[3/6] Starting RAG API (port 5001)...${NC}"
if [ -d "$RAG_DIR/.venv" ]; then
    (cd "$RAG_DIR" && source .venv/bin/activate && python main.py) \
        2>&1 | prefix_log "$BLUE" "rag-api" &
    echo -e "${GREEN}  RAG API :5001${NC}"
else
    echo -e "${RED}  No .venv in $RAG_DIR — skipping${NC}"
    echo -e "${RED}  Setup: cd services/rag-service && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt${NC}"
fi

# ========== [4/6] RAG Worker ==========
echo -e "\n${YELLOW}[4/6] Starting RAG Worker...${NC}"
if [ -d "$RAG_DIR/.venv" ]; then
    (cd "$RAG_DIR" && source .venv/bin/activate && python worker.py) \
        2>&1 | prefix_log "$CYAN" "rag-wrk" &
    echo -e "${GREEN}  RAG Worker listening on Redis queue${NC}"
else
    echo -e "${RED}  No .venv in $RAG_DIR — skipping${NC}"
fi

# ========== [5/6] Voice Service ==========
echo -e "\n${YELLOW}[5/6] Starting Voice Service (port 8001)...${NC}"
if [ -d "$VOICE_DIR/.venv" ]; then
    (cd "$VOICE_DIR" && source .venv/bin/activate && python server.py) \
        2>&1 | prefix_log "$MAGENTA" "voice" &
    echo -e "${GREEN}  Voice Service :8001${NC}"
else
    echo -e "${RED}  No .venv in $VOICE_DIR — skipping${NC}"
    echo -e "${RED}  Setup: cd services/voice-service && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt${NC}"
fi

# ========== [6/6] Web (production build) ==========
echo -e "\n${YELLOW}[6/6] Building & starting Web (port 3000)...${NC}"
if command -v pnpm &>/dev/null; then
    (cd "$WEB_DIR" && pnpm build && pnpm start) \
        2>&1 | prefix_log "$GREEN" "web" &
    echo -e "${GREEN}  Web :3000 (production build)${NC}"
else
    echo -e "${RED}  pnpm not found — skipping web service${NC}"
fi

# ========== Summary ==========
echo -e "\n${GREEN}${BOLD}================================================${NC}"
echo -e "${GREEN}${BOLD} All services launched!${NC}"
echo -e "${GREEN}${BOLD}================================================${NC}"
echo -e "  ${BOLD}Web:${NC}           http://localhost:3000"
echo -e "  ${BOLD}RAG API:${NC}       http://localhost:5001"
echo -e "  ${BOLD}Voice:${NC}         http://localhost:8001"
echo -e "  ${BOLD}Ollama:${NC}        http://localhost:11434"
echo -e "  ${BOLD}Postgres:${NC}      localhost:5432"
echo -e "  ${BOLD}Redis:${NC}         localhost:6379"
echo -e "${GREEN}${BOLD}================================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services.${NC}\n"

wait
