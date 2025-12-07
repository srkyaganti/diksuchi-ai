# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Diksuchi-AI is a multi-tenant RAG (Retrieval-Augmented Generation) platform with voice I/O and multi-language support for document intelligence. The platform is designed for offline/on-premises deployment with organization-based access control and collection-specific data isolation.

## Architecture

### Services & Ports

The application uses a microservices architecture with 4 main services:

1. **Web App** (`services/web/`) - Port 3000
   - Next.js 16 full-stack application with React 19
   - API routes for backend logic
   - Better Auth for multi-tenant authentication
   - Prisma ORM with PostgreSQL

2. **RAG Service** (`services/rag-service/`) - Port 5001
   - Python FastAPI worker for document processing
   - Hybrid retrieval (vector + BM25 + knowledge graphs)
   - Redis Queue for background job processing
   - Cross-encoder reranking

3. **STT Service** (whisper.cpp) - Port 8080
   - Speech-to-text transcription (managed separately)

4. **TTS Service** (`services/tts-service/`) - Port 8002
   - ParlerTTS for text-to-speech
   - 18+ Indian languages supported

### Infrastructure

- **PostgreSQL 16** - Relational data (users, organizations, files metadata)
- **Redis 8.4** - Job queue (RQ) and session management
- **ChromaDB** - Vector database (port 8000)
- **LM Studio** - Local LLM inference (port 1234, external)

## Data Isolation Architecture

**CRITICAL**: The platform implements collection-specific data isolation:

- Each collection in the web app maps to a separate ChromaDB collection named `collection_{collectionId}`
- BM25 indices are per-collection: `data/bm25_index/collection_{collectionId}`
- All retrieval operations MUST include `collection_id` parameter
- Files belong to collections, which belong to organizations
- Users access collections through organization membership

**Key files for understanding isolation:**
- `services/rag-service/src/ingestion/pipeline.py` - `_get_collection()` method
- `services/rag-service/src/retrieval/hybrid_retriever.py` - Collection-specific search
- `services/web/prisma/schema.prisma` - Data model relationships

## Common Development Commands

### Web App (Next.js)

```bash
cd services/web

# Development
pnpm install              # Install dependencies
pnpm dev                  # Start dev server (port 3000)
pnpm build                # Build for production
pnpm start                # Start production server
pnpm lint                 # Run ESLint

# Database
pnpm exec prisma migrate dev --name <name>    # Create migration
pnpm exec prisma migrate deploy               # Apply migrations (production)
pnpm exec prisma generate                     # Generate Prisma client
pnpm seed                                     # Seed super admin user (requires dev server running)

# Note: Prisma client output is in services/web/src/generated/prisma
# Import as: import { PrismaClient } from "@/generated/prisma/client"
```

### RAG Service (Python)

```bash
cd services/rag-service

# Setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
bash download-model.sh    # Download BGE-M3 embedding model

# Development
python main.py            # Start FastAPI server (port 5001)
python worker.py          # Start RQ worker for background jobs

# On macOS
./start_rag_macos.sh     # Starts both FastAPI server and worker

# On Windows
start_rag_windows.bat    # Starts both server and worker
```

### Database Operations

**Initial Setup (Fresh Database):**
```bash
cd services/web
pnpm exec prisma migrate dev --name init
pnpm dev                 # Start dev server first
pnpm seed                # In new terminal - seed super admin
```

**Default Credentials:**
- Email: `admin@example.com`
- Password: `Admin123!`
- Override with env vars: `SUPER_ADMIN_EMAIL` and `SUPER_ADMIN_PASSWORD`

**Important**: The seed script requires the dev server to be running because it uses Better Auth API endpoints.

### Testing

```bash
# Run single test file (Next.js)
cd services/web
pnpm test <test-file-path>

# Run all tests
pnpm test
```

## Key Code Patterns

### Authentication & Authorization

Authentication is handled by Better Auth (v1.4.3) with organization and admin plugins:

- Super admins can access all organizations
- Regular users must be members of an organization
- Organizations cannot be created by users (admin-only)
- Session includes `activeOrganizationId` for current context

**Key files:**
- `services/web/src/lib/auth.ts` - Better Auth configuration
- `services/web/src/lib/auth-client.ts` - Client-side auth utilities
- `services/web/src/lib/permissions.ts` - Permission checks
- `services/web/src/lib/org-context.ts` - Organization context

### RAG Processing Pipeline

Document processing follows this flow:

1. **Web App**: File upload → Save to disk → Create File record in DB
2. **Web App**: Submit job to RAG service via `PythonRAGClient`
3. **RAG Service**: Enqueue job in Redis Queue (RQ)
4. **Worker**: Process document asynchronously
   - Parse document (PDF/S1000D XML)
   - Chunk text intelligently
   - Generate embeddings (BGE-M3)
   - Store in ChromaDB (collection-specific)
   - Extract knowledge graph entities
   - Build BM25 index (collection-specific)
   - Callback to Web App with status updates
5. **Web App**: Update file status in database

**Key files:**
- `services/web/src/lib/python-client.ts` - Client for RAG service
- `services/rag-service/main.py` - FastAPI endpoints
- `services/rag-service/worker.py` - RQ worker job handler
- `services/rag-service/src/ingestion/pipeline.py` - Document processing

### Hybrid Retrieval

Retrieval combines three strategies:

1. **Vector Search**: ChromaDB with BGE-M3 embeddings
2. **Keyword Search**: BM25S for exact term matching
3. **Graph Expansion**: NetworkX knowledge graph for entity relationships

Optional cross-encoder reranking with BAAI/bge-reranker-v2-m3 for precision.

**Conversational Retrieval**: When chat history is provided, the system can:
- Expand queries based on conversation context
- Use query agent for reformulation (optional)
- Consider last N conversation turns (default: 3)

**Key files:**
- `services/rag-service/src/retrieval/hybrid_retriever.py` - Main retrieval logic
- `services/rag-service/src/retrieval/conversational_retriever.py` - Chat-aware retrieval
- `services/rag-service/src/retrieval/reranker.py` - Cross-encoder reranking

### File Paths & Storage

- Uploaded files: `services/web/uploads/{uuid}.{ext}`
- RAG data: `services/rag-service/data/`
  - ChromaDB: `data/chroma_db/`
  - BM25 indices: `data/bm25_index/collection_{collectionId}/`
  - Knowledge graphs: `data/graphs/`
- Embedding models: `services/rag-service/models/`

## Important Notes

### Multi-Tenancy & Security

- Always check organization membership before accessing resources
- File operations must validate user has access to the collection
- Chat sessions are scoped to collections and organizations
- Use `Session.activeOrganizationId` to determine current context

### Performance Considerations

- RAG service components are lazy-loaded (embeddings, retriever, reranker)
- BM25 indices are loaded per-collection on first use
- ChromaDB uses persistent storage, not in-memory
- Consider memory requirements: ~16GB RAM recommended

### Environment Configuration

Critical environment variables (see `.env.example`):
- `DATABASE_URL` - PostgreSQL connection
- `PYTHON_WORKER_URL` - RAG service endpoint
- `BETTER_AUTH_SECRET` - Generate with: `openssl rand -base64 32`
- `INTERNAL_API_SECRET` - Shared secret for RAG→Web callbacks
- `EMBEDDING_MODEL_PATH` - Path to BGE-M3 GGUF model
- `LLM_SERVICE_BASE_URL` - LM Studio endpoint
- `HF_TOKEN` - Required for downloading STT/TTS models

### Testing RAG Service

```bash
# Health check
curl http://localhost:5001/health

# Test retrieval
curl -X POST http://localhost:5001/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the maintenance procedure?",
    "collectionId": "clxxx",
    "limit": 5,
    "rerank": true
  }'
```

### Common Issues

1. **Seed script fails**: Make sure `pnpm dev` is running first
2. **Prisma import errors**: Check import path uses `@/generated/prisma/client`
3. **RAG service 404s**: Verify embedding model is downloaded
4. **Collection not found**: Ensure documents have been processed for that collection
5. **BM25 index missing**: Index is built after first document is processed

## Development Workflow

When adding new features:

1. **Database changes**: Update `schema.prisma` → `prisma migrate dev` → `prisma generate`
2. **API endpoints**: Add route in `services/web/src/app/api/` (Next.js 16 app router)
3. **RAG features**: Modify Python service, restart both `main.py` and `worker.py`
4. **UI components**: Use Shadcn UI components from `services/web/src/components/ui/`
5. **Type safety**: Leverage Zod for validation, TypeScript for types

## Architecture Decisions

- **Why Better Auth**: Offline-capable, built-in organization support, no external auth provider needed
- **Why separate RAG service**: Python ML ecosystem, background processing, resource isolation
- **Why ChromaDB per collection**: Complete data isolation, security for multi-tenant environment
- **Why Redis Queue**: Reliable background jobs, failure handling, progress tracking
- **Why local models**: Offline deployment requirement, data privacy, defense sector use case


## Additional Important Instructions
Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.