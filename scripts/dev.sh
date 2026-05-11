#!/usr/bin/env bash
# ============================================================
# Diksuchi-AI Development Startup Script
#
# Starts application services natively for fast iteration.
# Postgres + Redis run as system-level systemd services
# (apt-installed, auto-start at boot).
#
# Prerequisites:
#   - postgresql + redis-server installed via apt
#     (see scripts/install-native-pg-redis.sh)
#   - Python 3.11+ with venv at services/rag-service/.venv
#   - Node.js / pnpm (for the web service)
#   - Ollama installed natively (ollama.com)
# ============================================================

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    wait 2>/dev/null || true
    echo -e "${GREEN}All services stopped.${NC}"
}
trap cleanup EXIT INT TERM

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} Diksuchi-AI Dev Environment${NC}"
echo -e "${GREEN}========================================${NC}"

# --- 1. Infrastructure (native systemd) ---
echo -e "\n${YELLOW}[1/5] Checking Postgres + Redis...${NC}"
if pg_isready -h localhost -q 2>/dev/null; then
    echo -e "${GREEN}  Postgres :5432${NC}"
else
    echo -e "${RED}  Postgres unreachable -- run: sudo systemctl start postgresql${NC}"
fi
if redis-cli ping 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}  Redis :6379${NC}"
else
    echo -e "${RED}  Redis unreachable -- run: sudo systemctl start redis-server${NC}"
fi

# --- 2. Ollama (native) ---
echo -e "\n${YELLOW}[2/5] Starting Ollama...${NC}"
if command -v ollama &>/dev/null; then
    if ! pgrep -x "ollama" >/dev/null 2>&1; then
        ollama serve &>/dev/null &
        sleep 2
    fi
    echo -e "${GREEN}  Ollama :11434${NC}"
else
    echo -e "${RED}  Ollama not found -- install from https://ollama.com${NC}"
    echo -e "${RED}  Continuing without Ollama...${NC}"
fi

# --- 3. RAG API ---
echo -e "\n${YELLOW}[3/5] Starting RAG API (port 5001)...${NC}"
RAG_DIR="$ROOT_DIR/services/rag-service"
if [ -d "$RAG_DIR/.venv" ]; then
    (cd "$RAG_DIR" && source .venv/bin/activate && python main.py) &
    echo -e "${GREEN}  RAG API :5001${NC}"
else
    echo -e "${RED}  No .venv found in $RAG_DIR${NC}"
    echo -e "${RED}  Create one: cd services/rag-service && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt${NC}"
fi

# --- 4. RAG Worker ---
echo -e "\n${YELLOW}[4/5] Starting RAG Worker...${NC}"
if [ -d "$RAG_DIR/.venv" ]; then
    (cd "$RAG_DIR" && source .venv/bin/activate && python worker.py) &
    echo -e "${GREEN}  RAG Worker listening on Redis queue${NC}"
else
    echo -e "${RED}  Skipped -- no .venv${NC}"
fi

# --- 5. Web (Next.js) ---
echo -e "\n${YELLOW}[5/5] Starting Web (Next.js, port 3000)...${NC}"
WEB_DIR="$ROOT_DIR/services/web"
if command -v pnpm &>/dev/null; then
    (cd "$WEB_DIR" && pnpm dev) &
elif command -v npm &>/dev/null; then
    (cd "$WEB_DIR" && npm run dev) &
fi
echo -e "${GREEN}  Web :3000${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN} All services started!${NC}"
echo -e "${GREEN}   Web:     http://localhost:3000${NC}"
echo -e "${GREEN}   RAG API: http://localhost:5001${NC}"
echo -e "${GREEN}   Ollama:  http://localhost:11434${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services.${NC}\n"

wait
