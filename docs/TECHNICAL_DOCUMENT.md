---
title: "Diksuchi-AI Platform — Technical Document"
subtitle: "Architecture, Design, and Implementation Details"
version: "1.0"
date: "April 2025"
prepared-for: "Avision Team"
prepared-by: "Srikar Yaganti"
classification: "Internal"
---

---

# Table of Contents

1. [Document Information](#1-document-information)
2. [Introduction to AI/ML Concepts](#2-introduction-to-aiml-concepts)
   - 2.1 [What is Artificial Intelligence?](#21-what-is-artificial-intelligence)
   - 2.2 [What is Machine Learning?](#22-what-is-machine-learning)
   - 2.3 [What is a Large Language Model (LLM)?](#23-what-is-a-large-language-model-llm)
   - 2.4 [What are Embeddings?](#24-what-are-embeddings)
   - 2.5 [What is RAG (Retrieval-Augmented Generation)?](#25-what-is-rag-retrieval-augmented-generation)
   - 2.6 [What is a Vector Database?](#26-what-is-a-vector-database)
   - 2.7 [What is Semantic Search vs. Keyword Search?](#27-what-is-semantic-search-vs-keyword-search)
   - 2.8 [What is Reranking?](#28-what-is-reranking)
   - 2.9 [What is Speech-to-Text (STT)?](#29-what-is-speech-to-text-stt)
   - 2.10 [What is Text-to-Speech (TTS)?](#210-what-is-text-to-speech-tts)
3. [System Architecture](#3-system-architecture)
   - 3.1 [High-Level Architecture](#31-high-level-architecture)
   - 3.2 [Service Overview](#32-service-overview)
   - 3.3 [Technology Stack](#33-technology-stack)
4. [Service Details](#4-service-details)
   - 4.1 [Web Application Service](#41-web-application-service)
   - 4.2 [RAG Service](#42-rag-service)
   - 4.3 [Voice Service](#43-voice-service)
   - 4.4 [Infrastructure Services](#44-infrastructure-services)
5. [Document Processing Pipeline](#5-document-processing-pipeline)
   - 5.1 [Pipeline Overview](#51-pipeline-overview)
   - 5.2 [Step 1: PDF Upload](#52-step-1-pdf-upload)
   - 5.3 [Step 2: Docling Conversion (PDF to Markdown)](#53-step-2-docling-conversion-pdf-to-markdown)
   - 5.4 [Step 3: Section Mapping](#54-step-3-section-mapping)
   - 5.5 [Step 4: Image Extraction & Captioning](#55-step-4-image-extraction--captioning)
   - 5.6 [Step 5: Section-Aware Chunking](#56-step-5-section-aware-chunking)
   - 5.7 [Step 6: Embedding & Vector Storage](#57-step-6-embedding--vector-storage)
   - 5.8 [Step 7: BM25 Keyword Indexing](#58-step-7-bm25-keyword-indexing)
   - 5.9 [Step 8: Status Callback](#59-step-8-status-callback)
6. [Retrieval Pipeline (How Queries Work)](#6-retrieval-pipeline-how-queries-work)
   - 6.1 [Query Flow Overview](#61-query-flow-overview)
   - 6.2 [Step 1: Hybrid Search](#62-step-1-hybrid-search)
   - 6.3 [Step 2: Reciprocal Rank Fusion (RRF)](#63-step-2-reciprocal-rank-fusion-rrf)
   - 6.4 [Step 3: Cross-Encoder Reranking](#64-step-3-cross-encoder-reranking)
   - 6.5 [Step 4: Section Expansion](#65-step-4-section-expansion)
   - 6.6 [Step 5: LLM Answer Generation](#66-step-5-llm-answer-generation)
7. [Chat & Conversation System](#7-chat--conversation-system)
   - 7.1 [Chat Session Management](#71-chat-session-management)
   - 7.2 [Streaming Response Architecture](#72-streaming-response-architecture)
   - 7.3 [Source Citation System](#73-source-citation-system)
   - 7.4 [Image Delivery in Chat](#74-image-delivery-in-chat)
8. [Voice Processing System](#8-voice-processing-system)
   - 8.1 [Speech-to-Text Pipeline](#81-speech-to-text-pipeline)
   - 8.2 [Text-to-Speech Pipeline](#82-text-to-speech-pipeline)
   - 8.3 [Language & Speaker System](#83-language--speaker-system)
9. [Database Schema](#9-database-schema)
   - 9.1 [Entity-Relationship Overview](#91-entity-relationship-overview)
   - 9.2 [Data Models](#92-data-models)
10. [Authentication & Authorization](#10-authentication--authorization)
    - 10.1 [Authentication System](#101-authentication-system)
    - 10.2 [Authorization Model](#102-authorization-model)
11. [API Reference](#11-api-reference)
    - 11.1 [Web Application API Routes](#111-web-application-api-routes)
    - 11.2 [RAG Service API](#112-rag-service-api)
    - 11.3 [Voice Service API](#113-voice-service-api)
12. [File & Storage Architecture](#12-file--storage-architecture)
   - 12.1 [Uploaded File Storage](#121-uploaded-file-storage)
   - 12.2 [Processed Document Storage](#122-processed-document-storage)
   - 12.3 [Vector Database Storage](#123-vector-database-storage)
   - 12.4 [BM25 Index Storage](#124-bm25-index-storage)
13. [Deployment Architecture](#13-deployment-architecture)
    - 13.1 [Development Setup](#131-development-setup)
    - 13.2 [Production Deployment](#132-production-deployment)
    - 13.3 [Service Launcher Script](#133-service-launcher-script)
14. [AI/ML Models Used](#14-aiml-models-used)
15. [Configuration Reference](#15-configuration-reference)
16. [Glossary of Technical Terms](#16-glossary-of-technical-terms)

---

---

# 1. Document Information

| Field | Value |
|---|---|
| **Document Title** | Diksuchi-AI Platform — Technical Document |
| **Version** | 1.0 |
| **Date** | April 2025 |
| **Prepared For** | Avision Team |
| **Prepared By** | Srikar Yaganti |
| **Classification** | Internal Use |
| **Prerequisites** | Basic familiarity with web applications and databases |

---

# 2. Introduction to AI/ML Concepts

This section explains the key AI and machine learning concepts used in the Diksuchi-AI platform. If you come from a hardware background, think of these concepts as building blocks — similar to how transistors, logic gates, and processors build up to create a computer.

## 2.1 What is Artificial Intelligence?

Artificial Intelligence (AI) is a broad field of computer science focused on creating systems that can perform tasks that typically require human intelligence — such as understanding language, recognizing images, or making decisions.

**Analogy for hardware engineers**: If a traditional software program is like a fixed circuit that always produces the same output for a given input, an AI system is like a reconfigurable circuit that has been "trained" on many examples to produce useful outputs for new inputs it has never seen before.

## 2.2 What is Machine Learning?

Machine Learning (ML) is a subset of AI where systems learn patterns from data rather than being explicitly programmed with rules.

**Traditional programming**: You write rules (code) → Input data → Output
**Machine learning**: You provide input data + desired outputs → The system learns the rules (model) → New input → New output

**Analogy**: Think of it like calibrating a sensor. Instead of programming every temperature-resistance relationship by hand, you feed the system many calibration points, and it learns the curve. Later, it can interpolate for values it has never seen.

### Types of ML relevant to this platform:

| Type | What It Does | Used In Diksuchi-AI |
|---|---|---|
| **Natural Language Processing (NLP)** | Understanding and generating human language | Chat, document understanding |
| **Representation Learning** | Converting text/images into mathematical vectors (numbers) | Embeddings, search |
| **Sequence-to-Sequence** | Converting one sequence (audio) to another (text) | Speech-to-Text |
| **Generative AI** | Creating new content (text, audio) based on learned patterns | LLM answers, Text-to-Speech |

## 2.3 What is a Large Language Model (LLM)?

A Large Language Model (LLM) is a neural network trained on vast amounts of text data. It learns the statistical patterns of language — grammar, facts, reasoning patterns, and context — enabling it to generate human-like text.

**Key concepts**:
- **Training**: The model reads billions of words and learns to predict the next word in a sequence. Through this process, it learns facts, reasoning, and language patterns.
- **Inference**: When you give it a prompt (input text), it generates the most likely continuation — word by word.
- **Context window**: The amount of text the model can consider at once (like working memory). Larger context windows allow processing longer documents.

**Analogy**: Think of an LLM like an incredibly well-read technician who has studied thousands of manuals. When you ask a question, it draws on all that knowledge to formulate an answer. However, like any technician, it can only recall what it has studied — which is why we combine it with a retrieval system (RAG) that provides the specific documents for each query.

**In Diksuchi-AI**: We use a locally-running LLM (via Ollama) — no data is sent to the cloud. The LLM generates answers based on document sections that are retrieved for each query.

## 2.4 What are Embeddings?

An embedding is a way to represent text as a list of numbers (a vector) that captures its **meaning**. Texts with similar meanings get similar number patterns.

**Example**:
```
"How to replace the brake pads" → [0.23, -0.15, 0.89, 0.42, ...] (768 numbers)
"Brake pad replacement procedure" → [0.22, -0.14, 0.88, 0.43, ...] (768 numbers)
                                    ↑ Very similar numbers = similar meaning
"Weather forecast for tomorrow"   → [0.91, 0.33, -0.55, 0.12, ...] (768 numbers)
                                    ↑ Very different numbers = different meaning
```

**Analogy**: Think of it as assigning coordinates on a map. Concepts that are related end up close together on the map, while unrelated concepts are far apart. "Brake pads" and "disc brakes" would be neighbors, while "brake pads" and "weather" would be in different countries.

**Why this matters**: Embeddings enable **semantic search** — finding content by meaning rather than exact keywords. A search for "how to fix brakes" can find a section titled "Brake Maintenance Procedure" even though the words don't match exactly.

**In Diksuchi-AI**: We use the **BGE-M3** embedding model (via Ollama) which supports multiple languages and produces 1024-dimensional vectors.

## 2.5 What is RAG (Retrieval-Augmented Generation)?

RAG is the core technique that makes Diksuchi-AI accurate. It combines two steps:

```
┌─────────────────────────────────────────────────────┐
│                    RAG Process                      │
│                                                     │
│  User Question                                      │
│       │                                             │
│       ▼                                             │
│  ┌──────────┐     ┌──────────────────┐              │
│  │ RETRIEVE │ ──→ │ Find relevant    │              │
│  │          │     │ document sections│              │
│  └──────────┘     └──────────────────┘              │
│       │                                             │
│       ▼                                             │
│  ┌──────────┐     ┌──────────────────┐              │
│  │ GENERATE │ ──→ │ LLM writes       │              │
│  │          │     │ answer using     │              │
│  │          │     │ ONLY retrieved   │              │
│  │          │     │ sections         │              │
│  └──────────┘     └──────────────────┘              │
│       │                                             │
│       ▼                                             │
│  Answer with citations                              │
└─────────────────────────────────────────────────────┘
```

**Why not just use an LLM directly?**

An LLM's knowledge is frozen at training time and is general-purpose. It does not know your specific equipment manuals. RAG solves this by:
1. **Retrieving** the exact relevant sections from YOUR documents first
2. **Providing** those sections as context to the LLM
3. **Instructing** the LLM to answer ONLY from the provided context

This ensures answers are accurate, traceable, and never fabricated.

**Analogy**: Instead of asking a general engineer "How do I fix this?", you first find the exact pages in the manual, hand those pages to the engineer, and say "Answer based on these pages only." That's RAG.

## 2.6 What is a Vector Database?

A vector database is a specialized database that stores and searches embeddings (the number vectors from section 2.4). It can quickly find vectors that are "close" to a query vector — meaning they have similar meaning.

**Analogy**: A regular database (like PostgreSQL) is like a filing cabinet where you search by exact labels (file name, date). A vector database is like a map where you search by location — "find everything near this point." Since related concepts have similar embeddings (nearby coordinates), vector search finds semantically related content.

**In Diksuchi-AI**: We use **ChromaDB** — a lightweight, open-source vector database that runs embedded within the RAG service process (no separate server needed). It stores document chunk embeddings and their metadata, and supports fast similarity search.

## 2.7 What is Semantic Search vs. Keyword Search?

Diksuchi-AI uses **both** types of search combined (called "hybrid search"):

| Aspect | Keyword Search (BM25) | Semantic Search (Vector) |
|---|---|---|
| **How it works** | Matches exact words or word fragments | Matches meaning using embeddings |
| **Example query** | "brake pad" | "how to stop the vehicle safely" |
| **Finds** | Documents containing "brake" and "pad" | Documents about braking systems, even if those exact words aren't used |
| **Strength** | Precise for specific terms (part numbers, NSNs) | Understands synonyms and intent |
| **Weakness** | Misses synonyms and paraphrases | May miss exact part numbers |

**Why use both?**: Keyword search is excellent for finding exact part numbers (e.g., "NSN 2530-01-123-4567") while semantic search is better for conceptual queries (e.g., "how does the cooling system work"). Combining them gives the best of both worlds.

## 2.8 What is Reranking?

After the initial hybrid search returns candidate results, a **reranker** re-evaluates them with a more sophisticated (but slower) model that considers both the query and each result together.

**Analogy**: The initial search is like a quick triage — "these 20 sections might be relevant." The reranker is like a senior engineer carefully reading each of the 20 sections and scoring how well each one actually answers the question.

**Why is this needed?**: The initial search uses fast but approximate scoring. Reranking uses a more expensive cross-encoder model that jointly processes the query and each candidate, producing a more accurate relevance score.

**In Diksuchi-AI**: We use the **cross-encoder/ms-marco-MiniLM-L-6-v2** model for reranking. It runs on GPU when available for faster processing.

## 2.9 What is Speech-to-Text (STT)?

Speech-to-Text converts spoken language into written text. It involves:
1. **Audio capture** — Recording sound waves from a microphone
2. **Feature extraction** — Converting sound waves into spectrograms (visual representation of audio frequencies over time)
3. **Decoding** — A neural network processes the spectrograms and outputs text with timestamps

**In Diksuchi-AI**: We use **Faster Whisper** (an optimized version of OpenAI's Whisper model) running on GPU. It supports:
- Automatic language detection (or you can specify the language)
- Voice Activity Detection (VAD) to filter out silence
- Timestamps for each spoken segment
- 99 languages supported (10 exposed in the UI)

## 2.10 What is Text-to-Speech (TTS)?

Text-to-Speech converts written text into natural-sounding speech. It involves:
1. **Text analysis** — Breaking text into sentences and words, handling pronunciation
2. **Acoustic generation** — A neural network generates audio waveforms
3. **Voice selection** — Choosing the speaker characteristics (pitch, speed, tone)

**In Diksuchi-AI**: We use **Indic Parler TTS** by AI4Bharat, specifically designed for Indian languages with:
- 18+ Indian language support
- Multiple speaker voices per language (male and female)
- Natural-sounding speech output
- GPU-accelerated generation

---

# 3. System Architecture

## 3.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                              │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Chat UI  │  │ Data      │  │ PDF      │  │ Voice Controls   │   │
│  │          │  │ Library   │  │ Viewer   │  │ (Mic + Speaker)  │   │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
└───────┼──────────────┼──────────────┼─────────────────┼────────────┘
        │              │              │                 │
        └──────────────┴──────────────┴─────────────────┘
                              │
                    HTTP / WebSocket
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                    WEB APPLICATION (Port 3000)                     │
│                    Next.js 16 + React 19                           │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ API      │  │ Auth      │  │ Prisma   │  │ Voice API        │   │
│  │ Routes   │  │ (Better   │  │ ORM      │  │ Proxy Routes     │   │
│  │          │  │  Auth)    │  │          │  │                  │   │
│  └────┬─────┘  └───────────┘  └────┬─────┘  └────────┬─────────┘   │
└───────┼─────────────────────────────┼─────────────────┼────────────┘
        │                             │                 │
        │ HTTP                        │ SQL             │ HTTP
        │                             │                 │
┌───────▼──────────┐  ┌──────────────▼──────┐  ┌───────▼───────────┐
│  RAG SERVICE     │  │  POSTGRESQL 16      │  │  VOICE SERVICE    │
│  (Port 5001)     │  │  (Port 5432)        │  │  (Port 8000)      │
│  FastAPI+Python  │  │                      │  │  FastAPI+Python  │
│                  │  │  • Users            │  │                   │
│  • /api/process  │  │  • Organizations    │  │  • /stt/transcribe│
│  • /api/retrieve │  │  • Collections      │  │  • /tts/generate  │
│  • /api/jobs     │  │  • Files            │  │  • /tts/languages │
│                  │  │  • Chat Sessions    │  │                   │
└───────┬──────────┘  │  • Chat Messages    │  │  Models:          │
        │             │                     │  │  • Whisper (STT)  │
   ┌────┴────┐        └─────────────────────┘  │  • ParlerTTS(TTS) │
   │         │                                 └───────────────────┘
   ▼         ▼
┌────────┐ ┌──────────┐
│REDIS 8 │ │ ChromaDB │
│(6379)  │ │(Embedded)│
│        │ │          │
│• Job   │ │• Vector  │
│  Queue │ │  Search  │
│• Cache │ │• Chunk   │
└────────┘ │  Store   │
           └──────────┘
        ┌───────────────┐
        │    OLLAMA     │
        │  (Port 11434) │
        │               │
        │ • LLM Model   │
        │   (Llama 3.2) │
        │ • Embed Model │
        │   (BGE-M3)    │
        └───────────────┘
```

## 3.2 Service Overview

| Service | Technology | Port | Purpose |
|---|---|---|---|
| **Web Application** | Next.js 16, React 19, TypeScript | 3000 | Frontend UI + Backend API routes + Authentication |
| **RAG Service** | Python, FastAPI | 5001 | Document processing, embedding, retrieval |
| **RAG Worker** | Python, RQ (Redis Queue) | — | Background document processing (runs alongside RAG Service) |
| **Voice Service** | Python, FastAPI | 8000 | Speech-to-text and text-to-speech |
| **PostgreSQL** | PostgreSQL 16 | 5432 | Primary relational database |
| **Redis** | Redis 8 | 6379 | Job queue for document processing |
| **ChromaDB** | Embedded (in-process) | — | Vector database for semantic search |
| **Ollama** | Go binary | 11434 | Local LLM and embedding model serving |

## 3.3 Technology Stack

### Frontend (Web Application)

| Technology | Version | Purpose |
|---|---|---|
| Next.js | 16 | Full-stack React framework (pages, API routes, SSR) |
| React | 19 | UI component library |
| TypeScript | 5 | Type-safe JavaScript |
| Tailwind CSS | 4 | Utility-first CSS styling |
| Shadcn UI | latest | Pre-built accessible UI components |
| Radix UI | latest | Headless UI primitives (dialogs, dropdowns, etc.) |
| AI SDK (Vercel) | latest | Chat streaming, message management |
| Better Auth | 1.4.3 | Authentication (email/password, sessions, organizations) |

### Backend (Web Application)

| Technology | Purpose |
|---|---|
| Next.js API Routes | Server-side API endpoints (REST) |
| Prisma ORM | Type-safe database access layer |
| Server Actions | Server-side functions called from client components |

### RAG Service

| Technology | Purpose |
|---|---|
| FastAPI | High-performance async Python web framework |
| Docling | IBM's PDF-to-Markdown converter with structure extraction |
| ChromaDB | Embedded vector database for similarity search |
| BM25S | Fast BM25 keyword search implementation |
| Sentence Transformers | Cross-encoder model for reranking |
| NetworkX | Graph operations for section hierarchy |
| Redis + RQ | Background job processing queue |
| Ollama | Embedding generation (BGE-M3 model) |

### Voice Service

| Technology | Purpose |
|---|---|
| FastAPI | Web framework for STT/TTS endpoints |
| Faster Whisper | GPU-accelerated speech recognition (CTranslate2 backend) |
| Indic Parler TTS | Multi-language text-to-speech by AI4Bharat |
| PyTorch | Deep learning framework (GPU acceleration) |
| SoundFile | Audio file I/O |

### Infrastructure

| Technology | Purpose |
|---|---|
| PostgreSQL 16 | Primary relational database (users, files, chats) |
| Redis 8 | Job queue + session management |
| Docker Compose | Container orchestration for infrastructure services |
| Ollama | Local LLM serving (OpenAI-compatible API) |

---

# 4. Service Details

## 4.1 Web Application Service

**Directory**: `services/web/`
**Port**: 3000
**Framework**: Next.js 16 (App Router)

The web application is a full-stack Next.js application that serves both the frontend UI and backend API:

### Frontend Pages

| Route | Component | Purpose |
|---|---|---|
| `/` | Landing page | Public homepage with features, pricing, documentation |
| `/login` | Login page | Email/password authentication |
| `/select-organization` | Org selector | Choose which organization to work in |
| `/org/[slug]/chat` | Chat interface | Main RAG chat with collection selector, voice I/O |
| `/org/[slug]/data-library` | Data library | Manage collections and upload files |
| `/org/[slug]/data-library/[id]` | Collection detail | View files in a collection |
| `/org/[slug]/chat-history` | Chat history | Browse past conversations |
| `/org/[slug]/members` | Members list | View organization members |
| `/org/[slug]/settings` | Settings | Organization settings |
| `/viewer` | PDF viewer | View source documents with page navigation |
| `/admin` | Admin dashboard | Super admin: users, organizations, stats |
| `/admin/users` | User management | View and manage all users |
| `/admin/organizations` | Org management | Create and manage organizations |
| `/admin/organizations/[id]/members` | Org members | Manage organization membership |
| `/change-password` | Password change | Update user password |

### Key API Routes

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/chat` | Send a message and receive a streaming RAG response |
| GET | `/api/chat/sessions/[id]` | Get a chat session with all messages |
| POST | `/api/chat/sessions` | Create a new chat session |
| GET | `/api/collections` | List collections for the active organization |
| POST | `/api/collections` | Create a new collection |
| GET | `/api/collections/[id]` | Get collection details |
| DELETE | `/api/collections/[id]` | Delete a collection |
| POST | `/api/collections/[id]/files` | Upload files to a collection |
| GET | `/api/files/[id]/view` | Stream a file for viewing (PDF) |
| GET | `/api/files/[id]/download` | Download the original file |
| GET | `/api/files/[id]/images/[filename]` | Get an extracted document image |
| POST | `/api/voice/transcribe` | Proxy: send audio to Voice Service for STT |
| POST | `/api/voice/synthesize` | Proxy: send text to Voice Service for TTS |
| POST | `/api/voice/summarize` | Use LLM to break long text into TTS-friendly sentences |
| POST | `/api/internal/file-status` | Internal callback for RAG worker status updates |
| GET | `/api/organizations/[id]/members` | List organization members |
| POST | `/api/admin/organizations` | Create organization (admin only) |
| POST | `/api/admin/invite-member` | Invite a user to an organization |

## 4.2 RAG Service

**Directory**: `services/rag-service/`
**Port**: 5001
**Framework**: FastAPI (Python)

The RAG service has two components that run as separate processes:

### RAG API (`main.py`)
- Exposes REST endpoints for document processing and retrieval
- Manages the Redis job queue for background processing
- Lazy-initializes retrieval components (vector store, BM25, reranker) on first request

### RAG Worker (`worker.py`)
- Listens to the Redis job queue and processes documents in the background
- Runs the full ingestion pipeline: Docling conversion → section mapping → chunking → embedding → indexing
- Reports progress updates back to the web application via HTTP callback

### Module Structure

```
services/rag-service/
├── main.py                          # FastAPI API server
├── worker.py                        # Background document processing worker
├── requirements.txt                 # Python dependencies
├── src/
│   ├── embeddings/
│   │   └── ollama_embeddings.py     # Ollama-based embedding function for ChromaDB
│   ├── ingestion/
│   │   ├── docling_converter.py     # PDF → Markdown conversion (Docling)
│   │   ├── document_mapper.py       # Build section hierarchy from markdown
│   │   ├── chunker.py               # Section-aware text chunking
│   │   └── image_captioner.py       # AI vision-based image captioning
│   ├── retrieval/
│   │   ├── hybrid_retriever.py      # Vector + BM25 hybrid search with RRF
│   │   ├── reranker.py              # Cross-encoder reranking
│   │   └── section_expander.py      # Expand chunks to full parent sections
│   └── storage/
│       ├── document_store.py        # On-disk markdown + section map + images
│       ├── vector_store.py          # ChromaDB vector store wrapper
│       └── bm25_store.py            # BM25 keyword index management
├── data/
│   ├── chroma_db/                   # ChromaDB persistent storage
│   └── bm25_index/                  # BM25 index files per collection
└── tests/                           # Unit and integration tests
```

## 4.3 Voice Service

**Directory**: `services/voice-service/`
**Port**: 8000
**Framework**: FastAPI (Python)

A combined STT and TTS service with namespaced endpoints:

### STT (Speech-to-Text) — `/stt/*`
- Uses **Faster Whisper** (Whisper Large-v3) with CTranslate2 backend
- GPU-accelerated with CUDA support (float16 compute)
- Supports Voice Activity Detection (VAD) to filter silence
- Returns language detection, full transcription, and segment timestamps

### TTS (Text-to-Speech) — `/tts/*`
- Uses **Indic Parler TTS** by AI4Bharat
- Supports 18+ Indian languages with multiple speaker voices each
- Generates WAV audio at the model's native sampling rate
- Auto-selects best available device (CUDA > MPS > CPU)

### Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | Combined health check (STT + TTS) |
| GET | `/stt/health` | STT model status |
| POST | `/stt/transcribe` | Transcribe audio file to text |
| GET | `/tts/health` | TTS model status |
| POST | `/tts/generate` | Generate speech audio from text |
| GET | `/tts/languages` | List all supported languages and speakers |
| GET | `/tts/languages/{code}` | Get speakers for a specific language |

## 4.4 Infrastructure Services

### PostgreSQL 16 (`docker-compose.yml`)
- Primary relational database for all application data
- Runs in Docker container (`diksuchi-postgres`)
- Data persisted at `./data/postgres/`
- Health check via `pg_isready`

### Redis 8 (`docker-compose.yml`)
- Job queue for document processing (RQ library)
- Runs in Docker container (`diksuchi-redis`)
- Append-only persistence enabled
- Health check via `redis-cli ping`

### Ollama (Native)
- Serves LLM and embedding models locally
- Provides OpenAI-compatible API at `http://localhost:11434/v1`
- Models used:
  - **LLM**: Configurable (default: `llama3.2:3b`)
  - **Embeddings**: `bge-m3` (1024-dimensional vectors)
  - **Vision** (optional): For image captioning

---

# 5. Document Processing Pipeline

## 5.1 Pipeline Overview

When a user uploads a PDF, it goes through an 8-step processing pipeline:

```
Upload → Docling → Section Map → Image Extraction → Chunking → Embedding → BM25 Index → Callback
 (Web)    (RAG)     (RAG)        (RAG)              (RAG)      (RAG)       (RAG)         (RAG→Web)
```

## 5.2 Step 1: PDF Upload

**Service**: Web Application
**Code**: `services/web/src/app/api/collections/[id]/files/route.ts`

1. User selects a collection and uploads one or more PDF files
2. Each file is saved to disk at `storage/{uuid}/{filename}`
3. A database record is created with status `pending`
4. A processing request is sent to the RAG Service API (`POST /api/process`)
5. The RAG Service enqueues the job in Redis for background processing

## 5.3 Step 2: Docling Conversion (PDF to Markdown)

**Service**: RAG Worker
**Code**: `services/rag-service/src/ingestion/docling_converter.py`

The **Docling** library (by IBM) converts the PDF into structured Markdown:

1. PDF is loaded and analyzed for layout structure
2. Text is extracted with formatting preserved (headings, lists, tables)
3. **Section headers** are identified with their hierarchy levels
4. **Images** (pictures and tables) are extracted as PNG files
5. **Page numbers** are captured from provenance data
6. **Table images** are rendered as high-quality PNGs
7. **Figure captions** are extracted from the PDF

**Output**: `DoclingResult` containing:
- `markdown`: Full document as Markdown text
- `images`: Dictionary of `{filename: PNG bytes}`
- `image_info`: Metadata for each image (type, section, caption, page)
- `section_pages`: Mapping of section titles to page numbers

## 5.4 Step 3: Section Mapping

**Service**: RAG Worker
**Code**: `services/rag-service/src/ingestion/document_mapper.py`

The Markdown text is parsed to build a **hierarchical section map**:

1. All headers (`#`, `##`, `###`, etc.) are identified
2. A tree structure is built: chapters → sections → subsections
3. Each section records:
   - `id`: Unique identifier (e.g., "section-3")
   - `path`: Full path (e.g., "Chapter 2 > Engine > Cylinder Head")
   - `start_line` / `end_line`: Line positions in the Markdown
   - `page_no`: PDF page number
   - `children`: Sub-sections
4. Images are mapped to their nearest parent section

**Output**: JSON section map stored at `storage/{uuid}/section_map.json`

## 5.5 Step 4: Image Extraction & Captioning

**Service**: RAG Worker
**Code**: `services/rag-service/src/ingestion/image_captioner.py`

Each extracted image gets a descriptive caption using a three-tier priority system:

1. **Priority 1 — Docling caption**: If the PDF contains figure captions, they are used directly
2. **Priority 2 — Vision model**: If an Ollama vision model is available, the image is analyzed and a caption is generated using AI
3. **Priority 3 — Section fallback**: If neither is available, a generic caption like "Image from section: Cylinder Head Maintenance" is used

Images are also mapped to their parent sections so they can be displayed alongside relevant answers.

**Output**: `image_map.json` stored at `storage/{uuid}/image_map.json`

## 5.6 Step 5: Section-Aware Chunking

**Service**: RAG Worker
**Code**: `services/rag-service/src/ingestion/chunker.py`

The document is divided into **chunks** (small segments) for search and retrieval:

1. The section map is **flattened** into a list of leaf sections
2. For each section:
   - If the text fits within **512 tokens** (~2000 characters), it becomes a single chunk
   - If it exceeds the limit, it is split at **paragraph boundaries**
   - Adjacent paragraphs are grouped to stay within the token limit
   - An **overlap of 50 tokens** is maintained between consecutive chunks for context continuity
3. Image captions are appended to chunk text so image content becomes searchable
4. Each chunk carries metadata: `section_id`, `section_path`, `document_uuid`, `collection_id`, `page_no`, `image_filenames`

**Key design choice**: Chunks are aligned with section boundaries, not arbitrary character positions. This ensures that retrieved content is always coherent and contextually complete.

## 5.7 Step 6: Embedding & Vector Storage

**Service**: RAG Worker
**Code**: `services/rag-service/src/storage/vector_store.py`, `src/embeddings/ollama_embeddings.py`

Each chunk is converted into an embedding (vector of numbers) and stored in ChromaDB:

1. The **Ollama embedding API** (`/api/embed`) is called for each chunk
2. The **BGE-M3 model** produces a 1024-dimensional float vector per chunk
3. Chunks are upserted into a **per-collection ChromaDB collection** in batches of 64
4. ChromaDB stores: chunk ID, raw text, embedding vector, and metadata

**Error handling**: If embedding fails for a chunk (e.g., empty text), a zero vector is used as a fallback. Dimension mismatches are auto-corrected.

## 5.8 Step 7: BM25 Keyword Indexing

**Service**: RAG Worker
**Code**: `services/rag-service/src/storage/bm25_store.py`

A **BM25 keyword index** is built from the same chunks for exact-term matching:

1. Chunk texts are tokenized
2. A sparse term-document matrix is constructed
3. BM25 scoring parameters (term frequency, inverse document frequency, document length) are computed
4. The index is persisted to disk at `data/bm25_index/collection_{id}/`

This index enables fast keyword search as a complement to vector search.

## 5.9 Step 8: Status Callback

**Service**: RAG Worker → Web Application
**Code**: `worker.py` → `services/web/src/app/api/internal/file-status/route.ts`

After processing (success or failure), the worker sends a status update to the web application:

1. A `POST` request is sent to `/api/internal/file-status` with:
   - `fileId`: The database ID of the processed file
   - `ragStatus`: "completed" or "failed"
   - `ragError`: Error message (if failed)
   - `processedAt`: Timestamp (if completed)
2. The web application updates the database record
3. The file status badge in the UI updates accordingly

---

# 6. Retrieval Pipeline (How Queries Work)

## 6.1 Query Flow Overview

When a user asks a question in chat, the following pipeline executes:

```
User Question
     │
     ▼
┌──────────────────────────┐
│ 1. Hybrid Search         │
│    • Vector Search       │  ← ChromaDB (semantic)
│    • BM25 Search         │  ← BM25S (keyword)
│    • RRF Merge           │  ← Reciprocal Rank Fusion
└──────────┬───────────────┘
           │ ~20 candidates
           ▼
┌──────────────────────────┐
│ 2. Cross-Encoder Rerank  │  ← MiniLM-L-6-v2
│    Score each candidate  │
│    against the query     │
└──────────┬───────────────┘
           │ Top 10 reranked
           ▼
┌──────────────────────────┐
│ 3. Section Expansion     │  ← Load full parent sections
│    Expand chunks to full │     from document store
│    parent sections       │
└──────────┬───────────────┘
           │ Top 5 sections (deduplicated)
           ▼
┌──────────────────────────┐
│ 4. System Prompt Build   │  ← Inject sections + images
│    + LLM Generation      │     into prompt
└──────────┬───────────────┘
           │ Streaming response
           ▼
       Chat UI
```

## 6.2 Step 1: Hybrid Search

**Code**: `services/rag-service/src/retrieval/hybrid_retriever.py`

Two independent searches run in parallel against the same collection:

### Vector Search (Semantic)
1. The user's question is embedded using the same BGE-M3 model
2. ChromaDB performs a similarity search to find the top-K chunks with the closest embeddings
3. Results are ranked by vector distance (cosine similarity)

### BM25 Search (Keyword)
1. The user's question is tokenized
2. The BM25 index is queried for chunks containing matching terms
3. Results are ranked by BM25 score (term frequency + document frequency + length normalization)

## 6.3 Step 2: Reciprocal Rank Fusion (RRF)

Results from both search methods are merged using **Reciprocal Rank Fusion**:

```
RRF_score(chunk) = Σ  1 / (K + rank_i)
```

Where `K = 60` (standard constant) and `rank_i` is the position of the chunk in search method `i`.

- Chunks that appear in **both** search results get a higher combined score
- Chunks from only one method still contribute, but with lower scores
- This naturally boosts results that multiple methods agree on

## 6.4 Step 3: Cross-Encoder Reranking

**Code**: `services/rag-service/src/retrieval/reranker.py`

The top ~20 merged results are re-scored using a **cross-encoder model**:

1. Each (query, chunk_text) pair is fed into the cross-encoder together
2. The model produces a fine-grained relevance score
3. Results are re-sorted by this score
4. Top-K results are kept (typically `topK * 2 = 10`)

**Why cross-encoder?**: Unlike the bi-encoder used for initial search (which encodes query and document separately), a cross-encoder processes both together, allowing it to capture subtle relationships between the question and content.

**Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2` — a lightweight but effective reranking model that runs efficiently on GPU with float16 precision.

## 6.5 Step 4: Section Expansion

**Code**: `services/rag-service/src/retrieval/section_expander.py`

The top reranked **chunks** are expanded back to their **full parent sections**:

1. For each chunk, its `section_id` and `document_uuid` are read from metadata
2. The full section map and markdown are loaded from disk (`storage/{uuid}/`)
3. The complete section text is extracted (not just the chunk)
4. Duplicate sections (from multiple chunks in the same section) are deduplicated
5. Section-specific images and captions are attached

**Why expand?**: Chunks are small segments optimized for search, but the LLM needs full context to write a complete answer. Expanding to full sections ensures:
- Complete procedural steps are included
- All safety warnings are present
- Tables and specifications are complete
- No critical context is lost

## 6.6 Step 5: LLM Answer Generation

**Code**: `services/web/src/app/api/chat/route.ts`

The final step generates the answer:

1. A **system prompt** is constructed with:
   - Role definition (senior technical publications specialist)
   - The retrieved sections as context
   - Detailed instructions for response format, safety handling, and accuracy
   - Image references (markdown image syntax with URLs)
2. The conversation history (previous messages) is included for context
3. The LLM (via Ollama) generates the response with **temperature 0.0** (deterministic, no creativity)
4. The response is **streamed** token-by-token to the browser
5. Document images are streamed as file parts before the text
6. The complete message (text + images + sources) is saved to the database

---

# 7. Chat & Conversation System

## 7.1 Chat Session Management

**Code**: `services/web/src/app/api/chat/route.ts`, `api/chat/sessions/`

- **Sessions** are created on the first message of a new conversation
- The session title is auto-generated from the first user message (first 50 characters)
- Each session is tied to a **collection** and an **organization**
- Messages are stored in the `chat_messages` table with:
  - `content`: Plain text content
  - `parts`: Full structured message (text parts, file parts, tool parts) as JSON
  - `sources`: Structured source references with fileId, fileName, sectionPath, pageNo, documentUuid

## 7.2 Streaming Response Architecture

The chat uses the **Vercel AI SDK** for streaming:

1. Client sends a `POST /api/chat` request with message history and collection ID
2. Server creates a `UIMessageStream` that combines:
   - Document images (streamed as file parts)
   - LLM text generation (streamed as text parts)
3. The stream is returned as a Server-Sent Events (SSE) response
4. The client renders each token/image as it arrives
5. On completion, the full message is saved to the database

## 7.3 Source Citation System

**Code**: `services/web/src/app/api/chat/route.ts` (sources construction)

Each AI response includes structured source references:

```json
{
  "fileId": "cmabc123",
  "fileName": "T-72_Maintenance_Manual.pdf",
  "sectionPath": "Chapter 3 > Engine > Cylinder Head Removal",
  "pageNo": 147,
  "documentUuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

These citations are:
- Displayed as clickable source cards above the AI response
- Clicking opens the PDF viewer at the exact page
- File names are resolved from document UUIDs via database lookup

## 7.4 Image Delivery in Chat

Images referenced in AI responses are served via API routes:

1. During retrieval, each section's images are collected
2. Image URLs are constructed as `/api/files/{fileId}/images/{filename}`
3. These URLs are included in the system prompt so the LLM can reference them
4. The route `api/files/[id]/images/[filename]/route.ts` serves the stored image from `storage/{uuid}/images/{filename}`
5. In the chat UI, `DocumentImage` components render these with zoom capability

---

# 8. Voice Processing System

## 8.1 Speech-to-Text Pipeline

**Code**: `services/voice-service/server.py` (STT section), `services/web/src/components/chat/voice-input.tsx`

### Client-side processing:
1. User clicks **Record** → browser captures audio via `MediaRecorder` API
2. Audio is recorded in the browser's preferred format (WebM/MP4)
3. On stop, audio is converted to **WAV format** (16kHz mono) using Web Audio API
4. User previews the recording, then clicks **Transcribe**
5. Audio is sent to `/api/voice/transcribe` (web app proxy)

### Server-side processing:
1. Web app proxies the request to Voice Service `POST /stt/transcribe`
2. Audio is loaded and converted to float32 numpy array
3. Faster Whisper transcribes with beam size 5
4. Optional VAD (Voice Activity Detection) filters silence
5. Optional language parameter skips auto-detection
6. Returns: detected language, full text, and timestamped segments

## 8.2 Text-to-Speech Pipeline

**Code**: `services/voice-service/server.py` (TTS section), `services/web/src/components/chat/voice-output.tsx`

### Text summarization:
1. Long AI responses are summarized into key sentences via LLM (`POST /api/voice/summarize`)
2. This avoids generating audio for very long responses

### Audio generation:
1. Each sentence is sent to `/api/voice/synthesize` (web app proxy)
2. Web app proxies to Voice Service `POST /tts/generate`
3. Voice Service:
   - Builds a voice description from the language and speaker
   - Tokenizes the description and text
   - Generates audio using Indic Parler TTS
   - Returns WAV audio
4. **Prefetching**: The client prefetches the next 3 sentences while the current one plays
5. Audio cache (max 5 entries) avoids re-generating already-heard sentences

## 8.3 Language & Speaker System

Each language has a set of available speakers with recommended defaults:

| Language | Available Speakers | Recommended |
|---|---|---|
| English (en) | Thoma, Mary, Swapna, ... (21 speakers) | Thoma, Mary |
| Hindi (hi) | Rohit, Divya, Aman, Rani | Rohit, Divya |
| Tamil (ta) | Kavitha, Jaya | Jaya |
| Bengali (bn) | Arjun, Aditi, Tapan, Rashmi, Arnav, Riya | Arjun, Aditi |
| ... | ... | ... |

Speaker descriptions are auto-generated as: `"{name} speaks with a clear voice with slow speed with a moderate speed and pitch. The recording is of very high quality, with the speaker's voice sounding clear and very close up."`

---

# 9. Database Schema

## 9.1 Entity-Relationship Overview

```
┌──────────┐     ┌──────────────────┐     ┌──────────────┐
│   User   │────<│   Member         │>────│ Organization │
│          │     │ (role, org_id)   │     │              │
└────┬─────┘     └──────────────────┘     └──────┬───────┘
     │                                           │
     │              ┌──────────────┐              │
     ├─────────────>│  Collection  │<─────────────┤
     │              │              │              │
     │              └──────┬───────┘              │
     │                     │                      │
     │              ┌──────▼───────┐     ┌────────▼───────┐
     │              │    File      │     │  ChatSession   │
     │              │ (status,     │     │  (title)       │
     │              │  ragStatus)  │     └────────┬───────┘
     │              └──────────────┘              │
     │                                      ┌─────▼──────┐
     └─────────────────────────────────────>│ ChatMessage │
                                            │ (content,   │
                                            │  parts,     │
                                            │  sources)   │
                                            └─────────────┘

Additional:
  • Session (auth sessions)
  • Account (auth credentials)
  • Verification (email verification tokens)
  • Invitation (org invite tracking)
```

## 9.2 Data Models

### User
| Field | Type | Description |
|---|---|---|
| id | String (CUID) | Primary key (from Better Auth) |
| name | String | Display name |
| email | String (unique) | Login email |
| role | String? | User role |
| isSuperAdmin | Boolean | Platform admin flag |
| mustChangePassword | Boolean | Force password change on next login |
| banned | Boolean? | Account ban status |

### Organization
| Field | Type | Description |
|---|---|---|
| id | String | Primary key (from Better Auth) |
| name | String | Display name |
| slug | String (unique) | URL-friendly identifier |
| logo | String? | Organization logo URL |

### Member
| Field | Type | Description |
|---|---|---|
| id | String | Primary key |
| organizationId | String (FK) | References Organization |
| userId | String (FK) | References User |
| role | String | "admin" or "member" |

### Collection
| Field | Type | Description |
|---|---|---|
| id | String (CUID) | Primary key |
| name | String | Collection name |
| description | String? | Optional description |
| organizationId | String (FK) | Owning organization |
| userId | String (FK) | Creator |

### File
| Field | Type | Description |
|---|---|---|
| id | String (CUID) | Primary key |
| name | String | Original filename |
| uuid | String (unique) | Storage identifier |
| fileSize | BigInt | File size in bytes |
| mimeType | String | MIME type |
| status | String | Upload status: pending/processing/completed/failed |
| ragStatus | String? | RAG processing status: none/processing/completed/failed |
| ragError | String? | Error message if processing failed |
| collectionId | String (FK) | Parent collection |

### ChatSession
| Field | Type | Description |
|---|---|---|
| id | String (CUID) | Primary key |
| title | String? | Auto-generated from first message |
| collectionId | String (FK) | Queried collection |
| organizationId | String (FK) | Owning organization |
| userId | String (FK) | Session owner |

### ChatMessage
| Field | Type | Description |
|---|---|---|
| id | String (CUID) | Primary key |
| sessionId | String (FK) | Parent session |
| role | String | "user" or "assistant" |
| content | String (Text) | Plain text content |
| parts | JSON? | Structured message parts (text, files, tools) |
| sources | JSON? | Source references [{fileId, fileName, sectionPath, pageNo, documentUuid}] |

---

# 10. Authentication & Authorization

## 10.1 Authentication System

**Library**: Better Auth v1.4.3
**Code**: `services/web/src/lib/auth.ts`, `src/lib/auth-client.ts`

- **Email/password** authentication (no OAuth in offline environments)
- Email verification is disabled (offline/air-gapped deployment)
- Sessions are encrypted with `BETTER_AUTH_SECRET`
- Session duration: **7 days**, refreshed every 1 day
- Sessions store the `activeOrganizationId` for quick org context

### Super Admin Setup
- Created via seed script (`prisma/seed.ts`)
- Default credentials: `admin@example.com` / `Admin123!`
- Override via `SUPER_ADMIN_EMAIL` and `SUPER_ADMIN_PASSWORD` env vars

## 10.2 Authorization Model

Three-tier authorization:

1. **Authentication**: Is the user logged in? (checked on every API route)
2. **Organization membership**: Is the user a member of the organization they are accessing?
3. **Role-based access**:
   - **Super Admin**: Full access to all resources, Admin Dashboard
   - **Org Admin**: Manage members, all org-level operations
   - **Org Member**: Use existing org resources (collections, chat)

**Enforcement**: Each API route checks:
- Session validity (via `auth.api.getSession()`)
- Active organization (via `getActiveOrganizationId()`)
- Resource ownership (collection belongs to the active org)
- Super admin override (can access any resource)

---

# 11. API Reference

## 11.1 Web Application API Routes

### Authentication
| Method | Route | Auth | Description |
|---|---|---|---|
| * | `/api/auth/[...all]` | Public | Better Auth catch-all (login, register, logout, session) |

### Chat
| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/api/chat` | Required | Send message, receive streaming RAG response |
| POST | `/api/chat/sessions` | Required | Create new chat session |
| GET | `/api/chat/sessions/[id]` | Required | Get session with messages |
| DELETE | `/api/chat/sessions/[id]` | Required | Delete a chat session |
| GET | `/api/org/[slug]/chat-sessions` | Required | List sessions for an organization |

### Collections & Files
| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/api/collections` | Required | List collections for active org |
| POST | `/api/collections` | Required | Create a new collection |
| GET | `/api/collections/[id]` | Required | Get collection details |
| DELETE | `/api/collections/[id]` | Required | Delete a collection |
| POST | `/api/collections/[id]/files` | Required | Upload files to a collection |
| GET | `/api/files/[id]` | Required | Get file metadata |
| DELETE | `/api/files/[id]` | Required | Delete a file |
| GET | `/api/files/[id]/view` | Required | Stream file for inline viewing |
| GET | `/api/files/[id]/download` | Required | Download original file |
| GET | `/api/files/[id]/images/[filename]` | Required | Get extracted document image |

### Voice
| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/api/voice/transcribe` | Required | Proxy: audio → text (STT) |
| POST | `/api/voice/synthesize` | Required | Proxy: text → audio (TTS) |
| POST | `/api/voice/summarize` | Required | LLM-based text summarization for TTS |

### Admin
| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/api/admin/organizations` | Super Admin | List all organizations |
| POST | `/api/admin/organizations` | Super Admin | Create organization |
| POST | `/api/admin/invite-member` | Super Admin | Invite user to organization |
| GET | `/api/organizations/[id]/members` | Required | List org members |
| POST | `/api/organizations/[id]/switch` | Required | Switch active organization |

### Internal
| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/api/internal/file-status` | API Secret | RAG worker status callback |

## 11.2 RAG Service API

**Base URL**: `http://localhost:5001`

| Method | Route | Description |
|---|---|---|
| GET | `/` | Service info |
| GET | `/health` | Health check (includes Redis status) |
| POST | `/api/process` | Submit document processing job |
| GET | `/api/jobs/{job_id}` | Get job status and progress |
| POST | `/api/retrieve` | Hybrid retrieval (vector + BM25 → rerank → section expand) |

### Process Job Request
```json
{
  "fileId": "cmabc123",
  "collectionId": "cmxyz789",
  "fileName": "manual.pdf",
  "filePath": "/path/to/storage/uuid/manual.pdf",
  "mimeType": "application/pdf",
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Retrieve Request
```json
{
  "query": "What is the torque specification for cylinder head bolts?",
  "collectionId": "cmxyz789",
  "topK": 5
}
```

### Retrieve Response
```json
{
  "sections": [
    {
      "content": "Full section text...",
      "sectionPath": "Chapter 3 > Engine > Cylinder Head",
      "sectionId": "section-12",
      "documentUuid": "550e8400-...",
      "score": 0.892,
      "pageNo": 147,
      "images": ["picture_3.png"],
      "imageCaptions": {"picture_3.png": "Cylinder head bolt torque sequence"}
    }
  ],
  "timingMs": 342.5
}
```

## 11.3 Voice Service API

**Base URL**: `http://localhost:8000`

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Combined STT+TTS health check |
| GET | `/stt/health` | STT model status |
| POST | `/stt/transcribe` | Transcribe audio (multipart form: audio file) |
| GET | `/tts/health` | TTS model status |
| POST | `/tts/generate` | Generate speech audio |
| GET | `/tts/languages` | List all supported languages and speakers |
| GET | `/tts/languages/{code}` | Get speakers for a specific language |

### TTS Generate Request
```json
{
  "text": "The cylinder head bolts should be tightened to 120 Nm.",
  "language_code": "en",
  "speaker_name": "Thoma",
  "custom_description": null
}
```

### STT Transcribe Response
```json
{
  "language": "en",
  "language_probability": 0.98,
  "text": "What is the torque specification for cylinder head bolts?",
  "segments": [
    {"start": 0.0, "end": 3.2, "text": "What is the torque specification for cylinder head bolts?"}
  ]
}
```

---

# 12. File & Storage Architecture

## 12.1 Uploaded File Storage

```
storage/
└── {file-uuid}/
    ├── {original-filename}.pdf     # Original uploaded PDF
    ├── document.md                  # Converted Markdown (from Docling)
    ├── section_map.json             # Section hierarchy with page numbers
    ├── image_map.json               # Image metadata (section, caption, type)
    └── images/
        ├── picture_1.png            # Extracted figures/diagrams
        ├── picture_2.png
        ├── table_1.png              # Rendered table images
        └── ...
```

## 12.2 Processed Document Storage

Each processed document is stored on disk by the `document_store.py` module:

| File | Content | Used By |
|---|---|---|
| `document.md` | Full Markdown text from Docling conversion | Section expansion (retrieval) |
| `section_map.json` | Hierarchical section structure with IDs, paths, line positions, page numbers | Chunking, section expansion |
| `image_map.json` | Image metadata: filename, section_id, caption, caption_source, image_type | Image delivery in chat |
| `images/` | Extracted PNG images (pictures and tables) | Image display in chat responses |

## 12.3 Vector Database Storage

```
services/rag-service/data/chroma_db/
└── (ChromaDB SQLite files)
    └── collection_{collection-id}/
        └── (chunk embeddings + metadata)
```

- **Per-collection isolation**: Each document collection gets its own ChromaDB collection
- **Persistent storage**: ChromaDB uses SQLite as its backend — data survives restarts
- **Embedding dimensions**: 1024 (BGE-M3 model)

## 12.4 BM25 Index Storage

```
services/rag-service/data/bm25_index/
└── collection_{collection-id}/
    ├── corpus.jsonl          # Chunk texts
    ├── corpus.mmindex.json   # Memory-mapped index
    ├── data.csc.index.npy    # Sparse term-document matrix
    ├── indices.csc.index.npy # Column indices
    ├── indptr.csc.index.npy  # Row pointers
    ├── params.index.json     # BM25 parameters (k1, b)
    └── vocab.index.json      # Term vocabulary
```

---

# 13. Deployment Architecture

## 13.1 Development Setup

### Prerequisites
- **Docker Desktop** (with WSL2 on Windows)
- **Node.js** 18+ and **pnpm**
- **Python** 3.11+ and **pip**
- **Git**
- **Ollama** (for LLM and embedding models)
- **NVIDIA GPU** with CUDA 12.x (recommended for voice services)

### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/srkyaganti/diksuchi-ai.git
cd diksuchi-ai

# 2. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 3. Start infrastructure (PostgreSQL + Redis)
docker compose up -d

# 4. Install web application dependencies
cd services/web
pnpm install

# 5. Run database migrations
pnpm exec prisma migrate dev --name init

# 6. Start dev server (in separate terminal)
pnpm dev

# 7. Seed super admin user (dev server must be running)
pnpm seed

# 8. Install RAG service dependencies
cd ../rag-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 9. Install Voice service dependencies
cd ../voice-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 10. Start Ollama and pull models
ollama serve
ollama pull llama3.2:3b
ollama pull bge-m3

# 11. Start RAG service (separate terminal)
cd services/rag-service
source .venv/bin/activate
python main.py      # API server (port 5001)
python worker.py    # Background worker

# 12. Start Voice service (separate terminal)
cd services/voice-service
source .venv/bin/activate
python server.py    # Port 8000
```

## 13.2 Production Deployment

```bash
# Start all services with one command
bash scripts/start-all.sh
```

This script:
1. Starts Docker infrastructure (PostgreSQL + Redis)
2. Starts Ollama via Windows PowerShell
3. Starts RAG API (port 5001)
4. Starts RAG Worker (background)
5. Starts Voice Service (port 8000)
6. Builds and starts Web application (port 3000)

Press **Ctrl+C** to stop all services gracefully.

## 13.3 Service Launcher Script

**File**: `scripts/start-all.sh`

The unified launcher provides:
- **Colored, prefixed log output** per service
- **Health check waiting** for Docker containers
- **Graceful shutdown** (kills all background processes, stops Docker)
- **Missing dependency detection** (warns if .venv directories don't exist)
- **Summary panel** showing all service URLs

---

# 14. AI/ML Models Used

| Model | Type | Purpose | Size | Runs On |
|---|---|---|---|---|
| **Llama 3.2 (3B)** | LLM | Answer generation from retrieved context | ~2 GB | Ollama (CPU/GPU) |
| **BGE-M3** | Embedding | Convert text to vectors for semantic search | ~560 MB | Ollama (CPU/GPU) |
| **MiniLM-L-6-v2** (Cross-encoder) | Reranker | Re-score search results for accuracy | ~80 MB | Python (GPU preferred) |
| **Whisper Large-v3** | STT | Convert speech to text | ~3 GB | Python (GPU, CUDA) |
| **Indic Parler TTS** | TTS | Convert text to speech in Indian languages | ~1.5 GB | Python (GPU/CPU) |
| **Docling** | Document AI | PDF structure analysis and conversion | ~500 MB | Python (CPU/GPU) |
| **Optional Vision Model** | Vision | Generate image captions | Varies | Ollama (CPU/GPU) |

---

# 15. Configuration Reference

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `REDIS_HOST` | localhost | Redis server host |
| `REDIS_PORT` | 6379 | Redis server port |
| `BETTER_AUTH_SECRET` | — | Session encryption secret (32+ chars) |
| `BETTER_AUTH_URL` | http://localhost:3000 | Public URL for auth callbacks |
| `PYTHON_WORKER_URL` | http://localhost:5001 | RAG service endpoint |
| `VOICE_SERVICE_URL` | http://localhost:8000 | Voice service endpoint |
| `LLM_SERVICE_BASE_URL` | http://localhost:11434/v1 | Ollama API URL (OpenAI-compatible) |
| `LLM_MODEL` | llama3.2:3b | LLM model name in Ollama |
| `RAG_EMBEDDING_MODEL` | bge-m3 | Embedding model name in Ollama |
| `RAG_PORT` | 5001 | RAG service port |
| `RAG_REDIS_HOST` | localhost | Redis host for RAG worker |
| `RAG_WEB_CALLBACK_URL` | http://localhost:3000 | Web app URL for status callbacks |
| `RAG_WEB_API_SECRET` | — | Secret for internal API authentication |
| `STT_MODEL_NAME` | large-v3 | Whisper model for STT |
| `STT_DEVICE` | cuda | STT compute device (cuda/cpu) |
| `STT_COMPUTE_TYPE` | float16 | STT computation precision |
| `TTS_MODEL_NAME` | ai4bharat/indic-parler-tts | TTS model |
| `TTS_DEVICE` | auto | TTS compute device (auto/cuda/cpu) |
| `VOICE_SERVICE_PORT` | 8000 | Voice service port |
| `HF_TOKEN` | — | HuggingFace token for gated models |
| `INTERNAL_API_SECRET` | — | Service-to-service authentication secret |
| `CHROMA_DB_PATH` | data/chroma_db | ChromaDB storage path |
| `CHROMA_TELEMETRY` | FALSE | Disable ChromaDB telemetry |
| `VISION_MODEL` | (empty) | Optional Ollama vision model for image captions |

---

# 16. Glossary of Technical Terms

| Term | Definition |
|---|---|
| **API** | Application Programming Interface — a set of rules that allows different software services to communicate with each other |
| **Async/Await** | A programming pattern that allows a program to continue other work while waiting for a slow operation (like a network request) to complete |
| **BM25** | Best Matching 25 — a ranking algorithm used by search engines to estimate the relevance of documents to a given search query based on term frequency |
| **ChromaDB** | An open-source vector database designed for storing and querying AI embeddings |
| **Chunk** | A small segment of a document (typically ~500 tokens) used as the unit for search and retrieval |
| **CUID** | Collision-resistant Unique Identifier — a type of ID that is guaranteed to be unique without requiring a central coordinator |
| **Cross-Encoder** | A type of model that processes two texts together (question + candidate answer) to produce a single relevance score — more accurate but slower than bi-encoders |
| **CUDA** | Compute Unified Device Architecture — NVIDIA's parallel computing platform that enables GPU acceleration |
| **Docker** | A platform for packaging applications into containers — standardized, lightweight environments that run consistently across different machines |
| **Docling** | An open-source library by IBM for converting documents (especially PDFs) into structured formats like Markdown |
| **Embedding** | A mathematical representation of text as a vector (list of numbers) that captures semantic meaning — similar meanings produce similar vectors |
| **FastAPI** | A modern, high-performance Python web framework for building APIs |
| **Float16** | A 16-bit floating point number format used in GPU computing to reduce memory usage and increase speed with minimal accuracy loss |
| **GPU** | Graphics Processing Unit — a specialized processor originally designed for graphics but now widely used for AI/ML computations due to parallel processing capability |
| **HTTP** | HyperText Transfer Protocol — the standard protocol for communication between web browsers and servers |
| **JSON** | JavaScript Object Notation — a lightweight data format commonly used for APIs and configuration |
| **LLM** | Large Language Model — an AI model trained on vast amounts of text that can generate human-like text responses |
| **Markdown** | A lightweight text format that uses simple syntax (like `#` for headings, `**` for bold) to add formatting to plain text |
| **MIME Type** | Multipurpose Internet Mail Extensions — a standard that indicates the nature and format of a file (e.g., `application/pdf`) |
| **NLP** | Natural Language Processing — a branch of AI focused on enabling computers to understand and generate human language |
| **ORM** | Object-Relational Mapping — a technique that lets developers interact with a database using programming language objects instead of raw SQL |
| **PostgreSQL** | A powerful, open-source relational database system |
| **RAG** | Retrieval-Augmented Generation — an AI technique that first retrieves relevant documents and then generates an answer based on those documents |
| **Redis** | An in-memory data store used as a database, cache, and message broker |
| **Reranking** | A second-pass scoring process that re-evaluates search results with a more sophisticated model for better accuracy |
| **REST API** | Representational State Transfer API — a standard way of designing web APIs using HTTP methods (GET, POST, PUT, DELETE) |
| **RRF** | Reciprocal Rank Fusion — an algorithm for merging ranked lists from multiple search methods by combining their rank positions |
| **RQ** | Redis Queue — a simple Python library for enqueueing and processing background jobs using Redis |
| **S1000D** | An international standard for producing technical publications using a common source database — widely used in defence and aerospace |
| **SSE** | Server-Sent Events — a standard for pushing real-time updates from a server to a client over HTTP |
| **STT** | Speech-to-Text — the process of converting spoken language into written text |
| **TTS** | Text-to-Speech — the process of converting written text into spoken audio |
| **UIMessage** | A structured message format used by the Vercel AI SDK that supports multiple part types (text, files, tools) |
| **Vector** | A list of numbers representing a point in multi-dimensional space — used to encode the meaning of text for similarity comparison |
| **VAD** | Voice Activity Detection — a technique for detecting when speech is present in an audio signal (filtering out silence) |
| **VRAM** | Video RAM — memory on a GPU used for storing model weights and intermediate computations |

---

*End of Technical Document*
