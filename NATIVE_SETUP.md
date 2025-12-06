# Diksuchi-AI Native Setup Guide

Docker has been completely removed. All services now run natively on macOS and Windows.

## What's Been Completed

✅ **Phase 1: Pre-Migration** (DONE)
- Deleted all Docker files (docker-compose.yml, all Dockerfiles)
- Updated .env file with localhost URLs
- Created data directories for native storage
- Created startup scripts for all services

## Next Steps: Installation & Setup

### For macOS Development

**1. Install Infrastructure** (Manual - see plan for details)
```bash
# Install via Homebrew
brew install postgresql@16 redis python@3.11 node@22 ffmpeg

# PostgreSQL uses default port 5432
# Note: pgvector NOT needed - all vectors stored in ChromaDB
# See: ~/.claude/plans/clever-wishing-hammock.md (Section 2.1)

# Create ChromaDB virtual environment
python3.11 -m venv venv_chromadb
source venv_chromadb/bin/activate
pip install chromadb==1.3.5
deactivate
```

**2. Setup Each Service** (Manual)
```bash
# For each Python service (rag, stt, tts):
cd services/<service-name>
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

# For Next.js:
cd services/web
pnpm install

# Database setup (IMPORTANT - run in this order):
pnpm prisma migrate dev --name init  # Create and apply migrations
pnpm dev                              # Start dev server (required for seed)
pnpm seed                             # In a new terminal: Create super admin user
```

**3. Download Models** (Manual)
- **LLM**: Use LM Studio for local LLM inference (recommended)
- **RAG**: BGE-M3 GGUF already at `services/rag-service/models/bge-m3.gguf` ✓
- **STT**: Use whisper.cpp (run separately on port 8080)
- **TTS**: ParlerTTS (downloads automatically, ~2-3GB)

**4. Start Services**
```bash
# Start external services first:
# - LM Studio (for LLM inference on port 1234)
# - whisper.cpp (for STT on port 8080)

# Then start all managed services
./scripts/start_all_macos.sh

# Or start individually:
./scripts/start_chromadb_macos.sh
./services/rag-service/start_rag_macos.sh
./services/tts-service/start_tts_macos.sh
./services/web/start_web_macos.sh

# Check health
./scripts/health_check_macos.sh

# Stop all
./scripts/stop_all_macos.sh
```

### For Windows Production (with GPU)

**1. Install Infrastructure** (Manual - see plan for details)
- PostgreSQL 16 (default port 5432) - **No pgvector needed**
- Redis for Windows
- **CUDA Toolkit 12.1** (Critical for GPU!)
- Node.js 22, Python 3.11, FFmpeg
- ChromaDB virtual environment (handles all vector operations)

See detailed steps in: `~/.claude/plans/clever-wishing-hammock.md` (Section 2.2)

**2. Setup Each Service** (Manual)
```powershell
# For each Python service (rag, stt, tts):
cd services\<service-name>
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
deactivate

# For Next.js:
cd services\web
pnpm install

# Database setup (IMPORTANT - run in this order):
pnpm prisma migrate dev --name init  # Create and apply migrations
pnpm dev                              # Start dev server (required for seed)
pnpm seed                             # In a new terminal: Create super admin user
```

**3. Download Models & External Services**
- **LLM**: Use LM Studio for local LLM inference (recommended)
- **STT**: Use whisper.cpp for speech-to-text (run on port 8080)
- Download RAG/TTS models as needed

**4. Start Services**
```batch
REM Edit PROJECT_ROOT in all .bat files first!
REM Update: C:\path\to\diksuchi-ai

REM Start all services
scripts\start_all_windows.bat

REM Check health
scripts\health_check_windows.bat

REM Stop all
scripts\stop_all_windows.bat
```

## Scripts Created

### Service Startup Scripts
- `services/rag-service/start_rag_macos.sh` / `start_rag_windows.bat`
- `services/tts-service/start_tts_macos.sh` / `start_tts_windows.bat`
- `services/web/start_web_macos.sh` / `start_web_windows.bat`

### Master Control Scripts
- `scripts/start_chromadb_macos.sh` / `start_chromadb_windows.bat`
- `scripts/start_all_macos.sh` / `start_all_windows.bat`
- `scripts/stop_all_macos.sh` / `stop_all_windows.bat`
- `scripts/health_check_macos.sh` / `health_check_windows.bat`

## Service URLs

### Managed Services
- **Web App**: http://localhost:3000
- **ChromaDB**: http://localhost:8000
- **RAG Service**: http://localhost:5001
- **TTS Service**: http://localhost:8002

### External Services (manage separately)
- **LM Studio** (LLM): http://localhost:1234
- **whisper.cpp** (STT): http://localhost:8080

## Configuration

**Key .env Updates:**
- ✅ All URLs changed from container names to `localhost`
- ✅ Added `NEXTJS_CALLBACK_URL` and `NEXTJS_API_SECRET`
- ✅ LLM inference now handled by LM Studio (no MODEL_PATH needed)

## Data Directories

Created (replacing Docker volumes):
```
data/
├── postgres_data/
├── redis_data/
├── chromadb_data/
├── uploads/
├── bm25_index/
└── graph_data/

models/
├── whisper/
├── parler/
└── llm/

logs/          # Service logs
.pids/         # Process IDs for service management
```

## Detailed Setup Instructions

For complete installation instructions including:
- PostgreSQL configuration with pgvector
- CUDA 12.1 installation for Windows GPU
- Virtual environment setup for each service
- Troubleshooting common issues

See the detailed plan: `~/.claude/plans/clever-wishing-hammock.md`

## Testing

**Individual Service Testing:**
```bash
# Test each service endpoint
curl http://localhost:5001/health  # RAG
curl http://localhost:8002/health  # TTS
curl http://localhost:8080/inference  # whisper.cpp (STT)
curl http://localhost:1234/v1/models  # LM Studio
curl http://localhost:3000  # Web App
```

**Integrated Testing:**
1. Start external services (LM Studio + whisper.cpp)
2. Start all managed services
3. Run health check
4. Open web app: http://localhost:3000
5. Upload a document
6. Test chat with document
7. Test audio transcription/synthesis

## Next Actions Required

1. ⚠️ **Install infrastructure** on your system (PostgreSQL, Redis, etc.)
2. ⚠️ **Setup virtual environments** for all Python services
3. ⚠️ **Install and configure LM Studio** for LLM inference
4. ⚠️ **Update .env** to use LM Studio endpoint (localhost:1234)
5. ✅ **Test services** using health check scripts

## Support

- **Full plan**: `~/.claude/plans/clever-wishing-hammock.md`
- **Logs**: `tail -f logs/*.log` (macOS) or `type logs\*.log` (Windows)
- **Troubleshooting**: See plan Section 6 (Troubleshooting Guide)

---

**Status**: Phase 1 Complete ✅
**Next**: Manual infrastructure installation and service setup
