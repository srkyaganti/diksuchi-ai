# Diksuchi-AI Platform

> Multi-tenant RAG platform with voice I/O and multi-language support for document intelligence

## Overview

Diksuchi-AI is a comprehensive document intelligence platform that combines advanced retrieval-augmented generation (RAG), multi-language voice processing, and intelligent knowledge management.

## Architecture

### Services

- **Web App** (`services/web/`) - Next.js 16 full-stack application
  - Frontend UI with React 19 + Shadcn UI + Tailwind CSS
  - API routes for backend logic
  - Better Auth for multi-tenant authentication
  - Prisma ORM for PostgreSQL
  - **Port:** 3000

- **RAG Service** (`services/rag-service/`) - Python FastAPI worker
  - Document processing (PDF, S1000D technical documents)
  - Hybrid retrieval (vector + BM25 + knowledge graphs)
  - Cross-encoder reranking for precision
  - Background job processing via Redis Queue
  - **Port:** 5001

- **STT Service** (whisper.cpp) - Speech-to-Text
  - Whisper.cpp native transcription
  - Multi-language support
  - Real-time audio processing
  - **Port:** 8080 (managed separately)

- **TTS Service** (`services/tts-service/`) - Text-to-Speech
  - ParlerTTS synthesis
  - 18+ Indian languages supported
  - Customizable voice parameters
  - **Port:** 8002

### Infrastructure

- **PostgreSQL 16** - Primary database (relational data only)
- **Redis 8.4** - Job queue and session management
- **ChromaDB** - Vector database for semantic search and embeddings

## Quick Start

### Prerequisites

- Docker Desktop (with WSL2 on Windows)
- Git
- 16GB+ RAM recommended

### Installation

```bash
# Clone repository
git clone https://github.com/srkyaganti/diksuchi-ai.git
cd diksuchi-ai

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Access application
open http://localhost:3000
```

### Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| Web Application | http://localhost:3000 | Main UI |
| RAG Service API | http://localhost:5001 | Document processing |
| STT Service (whisper.cpp) | http://localhost:8080 | Speech-to-text |
| TTS Service | http://localhost:8002 | Text-to-speech |
| ChromaDB | http://localhost:8000 | Vector database |
| PostgreSQL | localhost:5432 | Database |

## Features

### Document Intelligence
- Multi-format support (PDF, DOCX, S1000D XML)
- Intelligent chunking and preprocessing
- Hybrid retrieval combining vector, keyword, and graph-based search
- Cross-encoder reranking for improved accuracy
- Knowledge graph extraction from documents

### Voice Capabilities
- Multi-language speech-to-text with Whisper
- Text-to-speech with 18+ Indian languages
- Real-time voice processing
- Audio format conversion and optimization

### Multi-Tenancy
- Organization-based access control
- User role management (admin, member)
- Collection-based document organization
- Secure authentication with Better Auth

### Conversational RAG
- Context-aware document retrieval
- Chat history tracking
- Real-time streaming responses
- Source attribution and citations

## Technology Stack

### Frontend
- **Framework:** Next.js 16 with React 19
- **UI:** Radix UI, Shadcn UI, Tailwind CSS 4
- **State:** React hooks, Server Components
- **Auth:** Better Auth 1.4.3

### Backend
- **API:** Next.js API Routes, FastAPI
- **Database:** PostgreSQL 16 + Prisma ORM
- **Vector DB:** ChromaDB
- **Search:** BM25S + Sentence Transformers
- **Queue:** Redis + RQ (Redis Queue)
- **Knowledge Graphs:** NetworkX

### AI/ML
- **LLM:** LM Studio (local), OpenAI-compatible APIs
- **Embeddings:** BGE-M3, Sentence Transformers
- **STT:** Whisper Large-v3
- **TTS:** ParlerTTS
- **Reranking:** BAAI/bge-reranker-v2-m3

## Development

### Local Setup

```bash
# Install Next.js dependencies
cd services/web
pnpm install

# Install Python dependencies
cd ../rag-service
pip install -r requirements.txt

# Download embedding models
bash download-model.sh

# Run Prisma migrations
cd ../web
pnpm exec prisma migrate dev
```

### Docker Development

```bash
# Build services
docker-compose build

# Start with logs
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Restart specific service
docker-compose restart [service-name]
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed Windows deployment instructions.

### Health Checks

Verify all services are running:

```bash
# Check service status
docker-compose ps

# All services should show "healthy" status
curl http://localhost:3000       # Web app
curl http://localhost:5001/health # RAG service
curl http://localhost:8080/inference # STT service (whisper.cpp)
curl http://localhost:8002/health # TTS service
```

## Configuration

### Environment Variables

Key configuration options (see `.env.example` for complete list):

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_HOST`, `REDIS_PORT` - Redis configuration
- `PYTHON_WORKER_URL` - RAG service endpoint
- `STT_SERVICE_URL` - Speech-to-text endpoint
- `TTS_SERVICE_URL` - Text-to-speech endpoint
- `LLM_MODEL` - Language model identifier
- `HF_TOKEN` - Hugging Face token for model downloads

### Database Setup & Migrations

**Initial Setup (Fresh Database):**
```bash
cd services/web

# 1. Create and apply migrations
pnpm exec prisma migrate dev --name init

# 2. Start the dev server (required for seed to work)
pnpm dev

# 3. In a new terminal, seed the super admin user
pnpm seed
```

**Creating New Migrations:**
```bash
# Create new migration after schema changes
pnpm exec prisma migrate dev --name migration_name

# Apply migrations (production)
pnpm exec prisma migrate deploy

# Generate Prisma client (after schema changes)
pnpm exec prisma generate
```

**Important Notes:**
- The seed script requires the dev server to be running (it uses Better Auth API)
- Default credentials: `admin@example.com` / `Admin123!`
- Override with env vars: `SUPER_ADMIN_EMAIL` and `SUPER_ADMIN_PASSWORD`

## Troubleshooting

### Services not starting

```bash
# Check logs for errors
docker-compose logs [service-name]

# Rebuild specific service
docker-compose build --no-cache [service-name]

# Reset everything
docker-compose down -v
docker-compose up -d
```

### Database issues

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres

# Re-initialize database
cd services/web
pnpm exec prisma migrate deploy
pnpm seed  # Don't forget to seed the super admin user!
```

### Model download issues

```bash
# Manually download embedding models
cd services/rag-service
bash download-model.sh

# Check model files
ls -lh models/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add your license here]

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/srkyaganti/diksuchi-ai/issues)
- Documentation: See `/docs` directory

## Acknowledgments

- Whisper by OpenAI
- ParlerTTS for multi-language synthesis
- ChromaDB for vector storage
- Better Auth for authentication
- All open-source contributors
