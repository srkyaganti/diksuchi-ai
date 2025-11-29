# Python RAG Worker

Advanced RAG (Retrieval-Augmented Generation) service with hybrid retrieval, knowledge graphs, and cross-encoder reranking.

## Features

- **S1000D XML Parsing**: Native support for defense technical documentation
- **Hybrid Retrieval**: Combines vector search (ChromaDB), keyword search (BM25), and knowledge graph traversal
- **LlamaParse Integration**: Premium PDF parsing with table extraction
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

Download the BGE-M3 GGUF model (~2GB):

```bash
# Create models directory
mkdir -p models

# Download using huggingface-cli
huggingface-cli download \
  mradermacher/bge-m3-gguf \
  bge-m3.Q8_0.gguf \
  --local-dir models \
  --local-dir-use-symlinks False

# Rename for consistency
mv models/bge-m3.Q8_0.gguf models/bge-m3.gguf
```

**Alternative**: Manual download from [Hugging Face](https://huggingface.co/mradermacher/bge-m3-gguf)

### 3. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_HOST`, `REDIS_PORT`: Redis connection
- `CHROMADB_HOST`, `CHROMADB_PORT`: ChromaDB connection
- `OLLAMA_BASE_URL`: Ollama server URL (if using Ollama)
- `NEXTJS_CALLBACK_URL`: Next.js app URL for callbacks
- `NEXTJS_API_SECRET`: Shared secret for callback authentication
- `EMBEDDING_MODEL_PATH`: Path to BGE-M3 GGUF model

Optional:
- `LLAMAPARSE_API_KEY`: For advanced PDF parsing ([Get API key](https://cloud.llamaindex.ai/))

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
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### Start RQ Worker

In a separate terminal:
```bash
python worker.py
```

### Verify Service

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "diksuchi-rag-service",
  "redis": "connected",
  "embedding_model": "models/bge-m3.gguf"
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

- **PDF**: Parsed using LlamaParse or pdf-parse
- **S1000D XML**: Custom parser for defense documentation
- **Plain Text**: Direct ingestion with chunking

## Processing Pipeline

1. **Document Loading**: Extract text from PDF/XML/TXT
2. **Chunking**:
   - S1000D: Uses native section boundaries
   - PDF: Markdown-aware splitting (1000 chars, 200 overlap)
3. **Embedding**: BGE-M3 GGUF model via llama-cpp-python
4. **Storage**:
   - ChromaDB: Vector embeddings
   - NetworkX + SQLite: Knowledge graph
   - BM25S: Keyword index
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
FileNotFoundError: Model not found: models/bge-m3.gguf
```
**Solution**: Download the model following instructions in "Download Embedding Model" section.

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

### llama-cpp-python Build Error
**Solution**: Install build dependencies:
```bash
# Ubuntu/Debian
apt-get install build-essential cmake libopenblas-dev

# macOS
brew install cmake
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

### CPU vs GPU

The worker auto-detects available hardware:
- **CPU**: Uses llama-cpp-python with OpenBLAS
- **GPU (CUDA)**: Set `CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python`
- **GPU (Metal/Mac)**: Automatically uses Metal backend

### Embedding Model Quantization

- **Q8_0** (recommended): Best quality/speed balance
- **Q4_K_M**: Faster, less memory, slightly lower quality
- **F16**: Highest quality, slower, 2x size

### Concurrency

Adjust RQ worker concurrency in docker-compose.yml:
```yaml
command: >
  sh -c "
  uvicorn main:app --host 0.0.0.0 --port 5000 &
  rq worker --burst document-processing -w 4
  "
```

## License

Same as parent project.
