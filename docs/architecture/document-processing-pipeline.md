# Document Processing Pipeline

> Architecture reference for the Docling-based document ingestion pipeline.
> Last updated: 2026-03-13

---

## Overview

The document processing pipeline converts uploaded PDFs into structured JSON using [Docling](https://github.com/DS4SD/docling) and extracts embedded images. The Docling JSON is stored **as-is** — it is the canonical document representation and is never modified after creation.

This replaces the previous RAG pipeline (chunking, embeddings, BM25, reranking). The system now uses a **long-context approach**: full document content is loaded directly into the LLM context window at query time.

---

## High-Level Pipeline Flow

```mermaid
flowchart LR
    A[User uploads PDF] --> B[Next.js API saves file]
    B --> C[File saved to uploads/uuid.ext]
    B --> D[Job enqueued via Python API]
    D --> E[Redis Queue]
    E --> F[RQ Worker picks up job]
    F --> G[Docling converts PDF]
    G --> H[JSON + Images stored]
    H --> I[Worker calls back to Next.js]
    I --> J[File status → completed]
```

---

## Detailed Processing Sequence

```mermaid
sequenceDiagram
    participant User
    participant NextJS as Next.js Web Server
    participant DB as PostgreSQL
    participant PyAPI as Python API (FastAPI)
    participant Redis
    participant Worker as RQ Worker
    participant Docling
    participant Disk as File System

    User->>NextJS: POST /api/files (multipart upload)
    NextJS->>Disk: Save PDF to uploads/{uuid}.{ext}
    NextJS->>DB: Create File record (status: pending, ragStatus: none)
    NextJS->>PyAPI: POST /api/process {fileId, collectionId, fileName, filePath, mimeType, uuid}
    PyAPI->>Disk: Verify file exists
    PyAPI->>Redis: Enqueue job to "document-processing" queue
    PyAPI-->>NextJS: 200 {jobId, status: queued}
    NextJS-->>User: 200 File created

    Redis->>Worker: Job dequeued
    Worker->>NextJS: POST /api/internal/file-status {fileId, status: processing}
    NextJS->>DB: Update ragStatus → processing

    Worker->>Docling: convert_pdf(file_path)
    Docling-->>Worker: DoclingResult {document_json, images}

    Worker->>Disk: save_document(uuid, json, images)
    Note over Disk: storage/{uuid}/document.json<br/>storage/{uuid}/images/picture_1.png<br/>storage/{uuid}/images/table_1.png

    Worker->>NextJS: POST /api/internal/file-status {fileId, status: completed, processedAt}
    NextJS->>DB: Update ragStatus → completed
```

---

## Service Architecture

```mermaid
flowchart TB
    subgraph Docker["Docker Compose Network"]
        subgraph Web["Next.js (web)"]
            Upload["/api/files — Upload"]
            Status["/api/internal/file-status — Callback"]
        end

        subgraph Python["Python Services"]
            API["FastAPI (rag-api :5001)"]
            WKR["RQ Worker (rag-worker)"]
        end

        RD[(Redis)]
        PG[(PostgreSQL)]
    end

    subgraph Storage["Shared Volumes"]
        UPL[("uploads_data")]
        STR[("storage_data")]
    end

    Upload -->|POST /api/process| API
    API -->|Enqueue job| RD
    RD -->|Dequeue job| WKR
    WKR -->|POST /api/internal/file-status| Status
    Status -->|Update| PG
    Upload -->|Write PDF| UPL
    WKR -->|Read PDF| UPL
    WKR -->|Write JSON + images| STR
    Web -->|Read JSON + images| STR
    Upload -->|Create File record| PG
```

---

## Storage Layout

Each processed document is stored under a UUID-based directory:

```
storage/
└── {uuid}/
    ├── document.json          # Docling JSON — immutable after creation
    └── images/
        ├── picture_1.png      # Extracted figures/diagrams
        ├── picture_2.png
        ├── table_1.png        # Rendered table images
        └── table_2.png
```

```mermaid
flowchart TB
    subgraph Volume["storage_data volume"]
        direction TB
        UUID["storage/{uuid}/"]
        JSON["document.json"]
        IMG_DIR["images/"]
        P1["picture_1.png"]
        P2["picture_2.png"]
        T1["table_1.png"]

        UUID --> JSON
        UUID --> IMG_DIR
        IMG_DIR --> P1
        IMG_DIR --> P2
        IMG_DIR --> T1
    end

    subgraph Uploads["uploads_data volume"]
        RAW["uploads/{uuid}.pdf"]
    end

    RAW -.->|Docling reads| UUID
```

### Storage Rules

- **Immutability**: `document.json` is never modified after initial write.
- **UUID mapping**: The `File.uuid` field in PostgreSQL maps to the storage directory name.
- **Image naming**: Sequential counters — `picture_N.png` for figures, `table_N.png` for table renders.
- **Path traversal protection**: All image access functions reject `..`, `/`, and `\` in filenames.

---

## Docling Converter Module

**File**: `services/rag-service/src/ingestion/docling_converter.py`

```mermaid
flowchart LR
    PDF[PDF File] --> DC[DocumentConverter]
    DC --> CR[ConversionResult]
    CR --> JSON[export_to_dict → document_json]
    CR --> ITER[iterate_items]
    ITER --> PIC[PictureItem → PNG bytes]
    ITER --> TBL[TableItem → PNG bytes]
    JSON --> DR[DoclingResult]
    PIC --> DR
    TBL --> DR
```

### Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `images_scale` | 2.0 | High-resolution image extraction |
| `generate_picture_images` | True | Extract embedded figures |
| `generate_page_images` | False | Skip full-page renders |
| `allowed_formats` | PDF only | Restrict to PDF input |

### API

```python
@dataclass
class DoclingResult:
    document_json: dict           # Raw Docling export
    images: Dict[str, bytes]      # filename → PNG bytes

def convert_pdf(pdf_path: str) -> DoclingResult
```

---

## Document Store Module

**File**: `services/rag-service/src/storage/document_store.py`

| Function | Signature | Purpose |
|----------|-----------|---------|
| `save_document` | `(uuid, docling_json, images, document_id=None) → Path` | Write JSON and images to disk |
| `get_document` | `(uuid) → dict` | Read and return `document.json` |
| `get_image_path` | `(uuid, filename) → Optional[Path]` | Resolve image path with traversal protection |
| `list_images` | `(uuid) → List[str]` | List all image filenames |
| `document_exists` | `(uuid) → bool` | Check if `document.json` exists |

---

## Worker Job Flow

**File**: `services/rag-service/worker.py`

```mermaid
stateDiagram-v2
    [*] --> Dequeued: Job picked from Redis
    Dequeued --> Processing: Notify web (ragStatus → processing)
    Processing --> Validating: Check file exists
    Validating --> Converting: convert_pdf()
    Converting --> Saving: save_document()
    Saving --> Completed: Notify web (ragStatus → completed)
    Completed --> [*]

    Validating --> Failed: File not found
    Converting --> Failed: Docling error
    Saving --> Failed: Storage error
    Failed --> [*]: Notify web (ragStatus → failed)
```

### Progress Reporting

| Progress | Stage |
|----------|-------|
| 10% | Job started, notifying web |
| 20% | Starting Docling conversion |
| 70% | Docling conversion complete |
| 80% | Saving document and images |
| 95% | Document stored |
| 100% | Job complete |

---

## Python API Endpoints

**File**: `services/rag-service/main.py` — FastAPI on port 5001

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/process` | Submit document processing job |
| GET | `/api/jobs/{job_id}` | Query job status and progress |
| GET | `/health` | Health check (includes Redis status) |
| GET | `/` | Service info |

### Job Lifecycle States

```mermaid
stateDiagram-v2
    [*] --> queued: POST /api/process
    queued --> processing: Worker picks up
    processing --> completed: Success
    processing --> failed: Error
    completed --> [*]
    failed --> [*]
```

---

## Environment Variables

| Variable | Default | Service | Purpose |
|----------|---------|---------|---------|
| `RAG_REDIS_HOST` | `localhost` | API, Worker | Redis connection |
| `RAG_REDIS_PORT` | `6379` | API, Worker | Redis port |
| `RAG_PORT` | `5001` | API | FastAPI listen port |
| `RAG_WEB_CALLBACK_URL` | `http://localhost:3000` | Worker | Web server for status callbacks |
| `RAG_WEB_API_SECRET` | `changeme-in-production` | Worker | Auth header for callbacks |
| `DOCLING_STORAGE_PATH` | `storage` | Worker, Store | Base path for document storage |

---

## Volume Sharing (Docker)

```mermaid
flowchart LR
    subgraph Volumes
        UV[("uploads_data")]
        SV[("storage_data")]
    end

    WEB["web (Next.js)"] -->|RW| UV
    WEB -->|RO| SV
    API["rag-api"] -->|RO| UV
    API -->|RW| SV
    WKR["rag-worker"] -->|RO| UV
    WKR -->|RW| SV
```

---

## What Was Removed (Previous RAG Stack)

The following components were removed in favor of the long-context approach:

| Component | Purpose (Former) | Replacement |
|-----------|-----------------|-------------|
| ChromaDB | Vector store for embeddings | Removed — no embeddings needed |
| BGE-M3 | Embedding model | Removed |
| BM25 index | Keyword retrieval | Removed |
| Reranker | Result reranking | Removed |
| Chunking pipeline | Document splitting | Removed — full document in context |
| `/api/retrieve` endpoint | RAG retrieval | Removed — `document-loader.ts` reads JSON directly |
| LangChain | Orchestration | Removed |
| Sentence Transformers | Embedding generation | Removed |
| PyTorch | ML inference | Removed |
