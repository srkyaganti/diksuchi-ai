# Python RAG Worker

Advanced RAG (Retrieval-Augmented Generation) service with hybrid retrieval, knowledge graphs, and cross-encoder reranking.

## Features

- **S1000D XML Parsing**: Native support for defense technical documentation
- **Hybrid Retrieval**: Combines vector search (ChromaDB), keyword search (BM25), and knowledge graph traversal
- **Offline PDF Parsing**: Local pdfplumber-based parsing with no internet required
- **Cross-Encoder Reranking**: Improves retrieval precision using BAAI/bge-reranker-v2-m3
- **Knowledge Graphs**: NetworkX-based graph database for contextual relationships
- **Background Job Processing**: RQ (Redis Queue) for async document processing

## Architecture

```
┌─────────────────┐
│   FastAPI API   │  ← Next.js calls /api/process, /api/retrieve
├─────────────────┤
│  Redis Queue    │  ← Job queueing
├─────────────────┤
│   RQ Worker     │  ← Background processing
├─────────────────┤
│ Ingestion       │  ← S1000D, PDF parsing
│ Pipeline        │  ← Chunking, embedding
├─────────────────┤
│   ChromaDB      │  ← Vector storage
│   BM25S         │  ← Keyword search
│   NetworkX      │  ← Knowledge graph
├─────────────────┤
│ Hybrid          │  ← Retrieval
│ Retriever       │  ← Reranking
└─────────────────┘
```

## Prerequisites

### 1. Python Dependencies

Install dependencies:
```bash
cd python-worker
pip install -r requirements.txt
```

### 2. Download Embedding Model

Download the BGE-M3 embedding model for offline use (~1.5-2.5GB):

```bash
# Run the download script (requires internet connection, one-time only)
python download_sentence_model.py
```

This downloads the sentence-transformers BGE-M3 model to `models/bge-m3/` for offline use.

**What's downloaded:**
- Full precision BGE-M3 model (BAAI/bge-m3) from Hugging Face
- Tokenizer and configuration files
- ~1.5-2.5GB of model weights

**After first download**: No internet required, model runs completely offline from local cache.

### 3. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `REDIS_HOST`, `REDIS_PORT`: Redis connection
- `CHROMADB_HOST`, `CHROMADB_PORT`: ChromaDB connection
- `RAG_OLLAMA_URL`: Ollama server URL
- `RAG_WEB_CALLBACK_URL`: Next.js app URL for callbacks
- `RAG_WEB_API_SECRET`: Shared secret for callback authentication

## Running Locally

### Start Dependencies

Ensure these services are running:
- PostgreSQL (port 5432)
- Redis (port 6379)
- ChromaDB (port 8000)

You can start them with:
```bash
# From frontend root
docker-compose up -d postgres redis chromadb
```

### Start FastAPI Service

```bash
python main.py
```

### Start RQ Worker

In a separate terminal:
```bash
python worker.py
```

### Verify Service

```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "diksuchi-rag-service",
  "redis": "connected",
  "embedding_model": "models/bge-m3"
}
```

## Running with Docker

The service is automatically started via docker-compose:

```bash
# From frontend root
docker-compose up -d python-worker
```

This runs both the FastAPI service and RQ worker in a single container.

## API Endpoints

### POST /api/process
Submit a document for processing.

**Request:**
```json
{
  "fileId": "string",
  "collectionId": "string",
  "fileName": "string",
  "filePath": "/app/uploads/file.pdf",
  "mimeType": "application/pdf"
}
```

**Response:**
```json
{
  "jobId": "collectionId-fileId",
  "status": "queued",
  "message": "Document processing job queued successfully"
}
```

### POST /api/retrieve
Perform hybrid retrieval with optional reranking.

**Request:**
```json
{
  "query": "How do I maintain the compressor?",
  "collectionId": "string",
  "limit": 5,
  "rerank": true
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "Compressor maintenance procedures...",
      "fileId": "string",
      "fileName": "manual.pdf",
      "similarity": 0.95,
      "metadata": {...}
    }
  ],
  "total": 5
}
```

### GET /api/jobs/{jobId}
Get job status.

**Response:**
```json
{
  "jobId": "string",
  "status": "completed",
  "progress": 100
}
```

### GET /health
Health check endpoint.

## Supported File Formats

- **PDF**: Parsed using local pdfplumber (offline, no internet required)
- **S1000D XML**: Custom parser for defense documentation
- **Plain Text**: Direct ingestion with chunking

## Processing Pipeline

1. **Document Loading**: Extract text from PDF/XML/TXT
2. **Chunking**:
   - S1000D: Uses native section boundaries
   - PDF: Recursive character splitting (1000 chars, 200 overlap)
3. **Embedding**: BGE-M3 model via sentence-transformers (offline, pure Python, auto-detects device)
4. **Storage**:
   - ChromaDB: Vector embeddings (collection-specific)
   - NetworkX + SQLite: Knowledge graph
   - BM25S: Keyword index (collection-specific)
5. **Callback**: Notify Next.js of completion

## Retrieval Pipeline

1. **Vector Search**: ChromaDB semantic similarity
2. **Keyword Search**: BM25S lexical matching
3. **Score Fusion**: Reciprocal Rank Fusion (RRF)
4. **Graph Expansion**: Fetch related warnings/tools
5. **Reranking**: Cross-encoder for precision
6. **Return**: Top-k results with metadata

## Troubleshooting

### Model Not Found Error
```
FileNotFoundError: Model not found: models/bge-m3
```
**Solution**: Download the model using:
```bash
python download_sentence_model.py
```

### ChromaDB Connection Error
```
ConnectionError: Unable to connect to ChromaDB
```
**Solution**: Ensure ChromaDB is running on the specified host and port.

### Redis Connection Error
```
redis.exceptions.ConnectionError
```
**Solution**: Ensure Redis is running and accessible.

### Sentence-transformers Installation Error
**Solution**: If you encounter issues installing sentence-transformers:
```bash
# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install sentence-transformers
pip install -r requirements.txt
```

## Development

### Project Structure
```
python-worker/
├── main.py              # FastAPI application
├── worker.py            # RQ worker
├── src/
│   ├── ingestion/       # Document parsing
│   ├── retrieval/       # Hybrid retrieval
│   ├── embeddings/      # Embedding functions
│   └── storage/         # Graph management
├── data/                # Runtime data
│   ├── chroma_db/       # Vector store
│   ├── bm25_index/      # Keyword index
│   └── graphs/          # Knowledge graphs
├── models/              # Embedding models
├── Dockerfile
├── requirements.txt
└── README.md
```

### Running Tests

```bash
pytest tests/
```

### Monitoring Jobs

View queued jobs:
```bash
rq info -u redis://localhost:6379
```

## Performance Tuning

### Hardware Acceleration

The worker auto-detects available hardware:
- **CPU**: Falls back to CPU computation (slowest)
- **CUDA (NVIDIA GPU)**: Auto-detected if CUDA is available
- **Metal (Apple Silicon)**: Auto-detected on macOS with Metal support (recommended)

Device auto-detection happens in `SentenceTransformerEmbeddingFunction.__init__()`.

### Memory Requirements

- **Full precision BGE-M3**: ~1.5-2.5GB model size
- **RAM during processing**: ~8-16GB recommended for production
- **GPU VRAM**: 4GB+ for CUDA acceleration

### Concurrency

Adjust RQ worker concurrency in docker-compose.yml:
```yaml
command: >
  sh -c "
  python3 main.py &
  rq worker --burst document-processing -w 4
  "
```

## License

Same as parent project.
