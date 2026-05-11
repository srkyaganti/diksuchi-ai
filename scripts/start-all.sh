#!/usr/bin/env bash
# ============================================================
# Diksuchi-AI — Unified Service Launcher
#
# Starts all services with a single command:
#   1. Verify Postgres + Redis (native systemd; apt-installed)
#   2. Ollama (via Windows PowerShell)
#   3. RAG API (port 5001)
#   4. RAG Worker
#   5. Database Migrations (Prisma)
#   6. Voice Service (port 8001)
#   7. Web — production build (port 3000)
#
# Usage:  bash scripts/start-all.sh
# Idempotent: Can be run multiple times — automatically restarts services
# Stop:   Ctrl+C (kills app services; postgres/redis keep running)
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

    # Postgres + Redis are systemd-managed; intentionally left running
    echo -e "${GREEN}${BOLD}All app services stopped (postgres + redis still running).${NC}"
}
trap cleanup EXIT INT TERM

# --------------- Pre-startup cleanup (make script idempotent) ---------------
pre_cleanup() {
    echo -e "${YELLOW}${BOLD}Cleaning up existing services...${NC}"

    # Kill any processes on our service ports
    for port in 3000 5001 8001 11434; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${CYAN}  Killing process on port $port...${NC}"
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            sleep 0.5
        fi
    done

    # Kill any background Python/Node services
    pkill -f "python.*main.py" 2>/dev/null || true
    pkill -f "python.*worker.py" 2>/dev/null || true
    pkill -f "python.*server.py" 2>/dev/null || true
    pkill -f "node.*pnpm" 2>/dev/null || true
    pkill -f "pnpm.*start" 2>/dev/null || true
    pkill -f "pnpm.*build" 2>/dev/null || true
    pkill -f "next.*build" 2>/dev/null || true
    pkill -f "next-server" 2>/dev/null || true
    sleep 1

    # Re-check ports after pkill — some services (e.g. voice) may not have died
    # with their parent shell. Force-kill anything still bound.
    for port in 3000 5001 8001 11434; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${CYAN}  Force-killing leftover process on port $port...${NC}"
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done

    # Remove stale Next.js build lock from interrupted previous runs
    if [ -f "$WEB_DIR/.next/lock" ]; then
        echo -e "${CYAN}  Removing stale .next/lock...${NC}"
        rm -f "$WEB_DIR/.next/lock"
    fi

    echo -e "${GREEN}  Cleanup complete${NC}"
}

# --------------- Prefixed log helper ---------------
# Pipes stdin with a colored prefix per service
prefix_log() {
    local color="$1" name="$2"
    sed -u "s/^/${color}[${name}]${NC} /"
}

echo -e "${GREEN}${BOLD}================================================${NC}"
echo -e "${GREEN}${BOLD} Diksuchi-AI — Starting All Services${NC}"
echo -e "${GREEN}${BOLD}================================================${NC}"

# Run pre-startup cleanup to make script idempotent
pre_cleanup

# ========== [1/7] Infrastructure (native systemd) ==========
echo -e "\n${YELLOW}[1/7] Verifying Postgres + Redis (native systemd)...${NC}"
TIMEOUT=60
ELAPSED=0
while true; do
    PG_OK=0; RD_OK=0
    pg_isready -h localhost -q 2>/dev/null && PG_OK=1
    redis-cli ping 2>/dev/null | grep -q PONG && RD_OK=1

    if [[ $PG_OK -eq 1 && $RD_OK -eq 1 ]]; then
        echo -e "${GREEN}  Postgres: ready  |  Redis: ready${NC}"
        break
    fi

    if (( ELAPSED >= TIMEOUT )); then
        echo -e "${RED}  Timed out (${TIMEOUT}s). Postgres=$PG_OK  Redis=$RD_OK${NC}"
        echo -e "${RED}  Check: sudo systemctl status postgresql redis-server${NC}"
        exit 1
    fi

    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo -e "${CYAN}  Postgres: $PG_OK  Redis: $RD_OK  (${ELAPSED}s)${NC}"
done

# ========== [2/7] Ollama (Windows side) ==========
echo -e "\n${YELLOW}[2/7] Starting Ollama (Windows PowerShell)...${NC}"
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

# ========== [3/7] RAG API ==========
echo -e "\n${YELLOW}[3/7] Starting RAG API (port 5001)...${NC}"
if [ -d "$RAG_DIR/.venv" ]; then
    (cd "$RAG_DIR" && source .venv/bin/activate && python main.py) \
        2>&1 | prefix_log "$BLUE" "rag-api" &
    echo -e "${GREEN}  RAG API :5001${NC}"
else
    echo -e "${RED}  No .venv in $RAG_DIR — skipping${NC}"
    echo -e "${RED}  Setup: cd services/rag-service && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt${NC}"
fi

# ========== [4/7] RAG Worker ==========
echo -e "\n${YELLOW}[4/7] Starting RAG Worker...${NC}"
if [ -d "$RAG_DIR/.venv" ]; then
    (cd "$RAG_DIR" && source .venv/bin/activate && python worker.py) \
        2>&1 | prefix_log "$CYAN" "rag-wrk" &
    echo -e "${GREEN}  RAG Worker listening on Redis queue${NC}"
else
    echo -e "${RED}  No .venv in $RAG_DIR — skipping${NC}"
fi

# ========== [5/7] Database Migrations ==========
echo -e "\n${YELLOW}[5/7] Running database migrations...${NC}"
(cd "$WEB_DIR" && npx prisma migrate deploy && npm run seed) || {
    echo -e "${RED}  Database migration failed${NC}"
    exit 1
}
echo -e "${GREEN}  Database migrations complete${NC}"

# ========== [6/7] Voice Service ==========
echo -e "\n${YELLOW}[6/7] Starting Voice Service (port 8001)...${NC}"
if [ -d "$VOICE_DIR/.venv" ]; then
    (cd "$VOICE_DIR" && source .venv/bin/activate && python server.py) \
        2>&1 | prefix_log "$MAGENTA" "voice" &
    echo -e "${GREEN}  Voice Service :8001${NC}"
else
    echo -e "${RED}  No .venv in $VOICE_DIR — skipping${NC}"
    echo -e "${RED}  Setup: cd services/voice-service && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt${NC}"
fi

# ========== [7/7] Web (production build) ==========
echo -e "\n${YELLOW}[7/7] Building & starting Web (port 3000)...${NC}"
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
