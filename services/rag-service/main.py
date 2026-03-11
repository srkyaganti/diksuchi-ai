"""
FastAPI application for RAG document processing and retrieval.
Provides endpoints for job submission and hybrid retrieval.
"""

from dotenv import load_dotenv

load_dotenv()

import os
import logging
import uuid
import time
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
import httpx

# --------------------------------------------------
# Configuration
# --------------------------------------------------

RAG_REDIS_HOST = os.getenv("RAG_REDIS_HOST", "localhost")
RAG_REDIS_PORT = int(os.getenv("RAG_REDIS_PORT", "6379"))
RAG_WEB_CALLBACK_URL = os.getenv("RAG_WEB_CALLBACK_URL", "http://localhost:3000")
RAG_WEB_API_SECRET = os.getenv("RAG_WEB_API_SECRET", "changeme-in-production")
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "bge-m3")
RAG_OLLAMA_URL = os.getenv("RAG_OLLAMA_URL", "http://localhost:11434")
RAG_CHROMADB_HOST = os.getenv("RAG_CHROMADB_HOST", "localhost")
RAG_CHROMADB_PORT = int(os.getenv("RAG_CHROMADB_PORT", "8000"))
RAG_PORT = int(os.getenv("RAG_PORT", "5001"))

# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Global Instances
# --------------------------------------------------

redis_conn: Redis | None = None
job_queue: Queue | None = None
_retriever = None
_reranker = None
_conversational_retriever = None


def get_retriever():
    """Lazy initialization of HybridRetriever with Ollama embeddings."""
    global _retriever
    if _retriever is None:
        from src.retrieval.hybrid_retriever import HybridRetriever

        logger.info("Initializing HybridRetriever with Ollama...")
        _retriever = HybridRetriever(
            ollama_model=RAG_EMBEDDING_MODEL, ollama_url=RAG_OLLAMA_URL
        )
    return _retriever


def get_reranker():
    """Lazy initialization of Reranker with FP16 for memory efficiency."""
    global _reranker
    if _reranker is None:
        from src.retrieval.reranker import Reranker

        logger.info("Initializing Reranker (FP16 enabled)...")
        _reranker = Reranker(use_fp16=True)
    return _reranker


def get_conversational_retriever():
    """Lazy initialization of ConversationalRetriever with shared instances."""
    global _conversational_retriever
    if _conversational_retriever is None:
        from src.retrieval.conversational_retriever import ConversationalRetriever

        logger.info("Initializing ConversationalRetriever with shared instances...")
        _conversational_retriever = ConversationalRetriever(
            hybrid_retriever=get_retriever(),
            reranker=get_reranker(),
            use_query_agent=False,
        )
    return _conversational_retriever


# --------------------------------------------------
# Lifespan Event Handler
# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_conn, job_queue

    logger.info("=" * 70)
    logger.info("RAG Worker API Starting...")
    logger.info(f"Redis: {RAG_REDIS_HOST}:{RAG_REDIS_PORT}")
    logger.info(f"Ollama Model: {RAG_EMBEDDING_MODEL}")
    logger.info(f"Ollama URL: {RAG_OLLAMA_URL}")
    logger.info(f"ChromaDB: {RAG_CHROMADB_HOST}:{RAG_CHROMADB_PORT}")
    logger.info(f"Callback URL: {RAG_WEB_CALLBACK_URL}")
    logger.info("=" * 70)

    # Initialize Redis connection
    try:
        redis_conn = Redis(
            host=RAG_REDIS_HOST, port=RAG_REDIS_PORT, decode_responses=True
        )
        redis_conn.ping()
        logger.info(f"Connected to Redis at {RAG_REDIS_HOST}:{RAG_REDIS_PORT}")
        job_queue = Queue("document-processing", connection=redis_conn)
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_conn = None
        job_queue = None

    # Verify Ollama is running
    try:
        response = httpx.get(f"{RAG_OLLAMA_URL}/api/tags", timeout=10.0)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = [m.get("name", "").split(":")[0] for m in models]
        if RAG_EMBEDDING_MODEL in model_names:
            logger.info(f"Ollama model '{RAG_EMBEDDING_MODEL}' is available")
        else:
            logger.warning(f"Model '{RAG_EMBEDDING_MODEL}' not found in Ollama.")
            logger.warning(f"Available: {model_names}")
            logger.warning(f"Pull with: ollama pull {RAG_EMBEDDING_MODEL}")
    except Exception as e:
        logger.error(f"Cannot connect to Ollama at {RAG_OLLAMA_URL}: {e}")
        logger.error("Please start Ollama: ollama serve")

    # Warm up models
    logger.info("Warming up models during startup...")
    startup_start = time.time()

    try:
        logger.info("  [1/3] Connecting to Ollama for embeddings...")
        retriever_start = time.time()
        get_retriever()
        logger.info(
            f"  HybridRetriever initialized in {time.time() - retriever_start:.2f}s"
        )
    except Exception as e:
        logger.error(f"  Failed to initialize HybridRetriever: {e}")

    try:
        logger.info("  [2/3] Loading Reranker Model (FP16 cross-encoder)...")
        reranker_start = time.time()
        get_reranker()
        logger.info(f"  Reranker loaded in {time.time() - reranker_start:.2f}s")
    except Exception as e:
        logger.error(f"  Failed to load Reranker: {e}")

    try:
        logger.info("  [3/3] Initializing Conversational Retriever...")
        conv_start = time.time()
        get_conversational_retriever()
        logger.info(
            f"  Conversational Retriever initialized in {time.time() - conv_start:.2f}s"
        )
    except Exception as e:
        logger.error(f"  Failed to initialize Conversational Retriever: {e}")

    logger.info("=" * 70)
    logger.info(f"RAG Service startup complete in {time.time() - startup_start:.2f}s")
    logger.info("=" * 70)

    yield

    # Cleanup
    logger.info("RAG Worker API shutting down...")
    if redis_conn:
        redis_conn.close()


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="RAG Worker API",
    description="Document processing and hybrid retrieval service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Request/Response Models
# --------------------------------------------------


class ProcessJobRequest(BaseModel):
    """Request model for document processing."""

    fileId: str
    collectionId: str
    fileName: str
    filePath: str
    mimeType: str


class ProcessJobResponse(BaseModel):
    """Response model for job submission."""

    jobId: str
    status: str
    message: str


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str
    content: str


class RetrieveRequest(BaseModel):
    """Request model for hybrid retrieval."""

    query: str
    collectionId: str
    limit: int = 5
    rerank: bool = True
    chatHistory: Optional[List[ChatMessage]] = None
    useConversationalRetrieval: bool = False
    conversationDepth: int = 3


class RetrieveResult(BaseModel):
    """Individual retrieval result."""

    content: str
    fileId: Optional[str] = None
    fileName: Optional[str] = None
    similarity: float
    metadata: dict


class RetrieveResponse(BaseModel):
    """Response model for retrieval."""

    results: List[RetrieveResult]
    total: int


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    jobId: str
    status: str
    progress: Optional[int] = None
    error: Optional[str] = None


# --------------------------------------------------
# Health Endpoints
# --------------------------------------------------


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Diksuchi AI RAG Worker",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "process": "POST /api/process",
            "retrieve": "POST /api/retrieve",
            "job_status": "GET /api/jobs/{job_id}",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_status = "connected" if redis_conn and redis_conn.ping() else "disconnected"

    return {
        "status": "healthy",
        "service": "diksuchi-rag-service",
        "redis": redis_status,
        "ollama_model": RAG_EMBEDDING_MODEL,
        "chromadb": f"{RAG_CHROMADB_HOST}:{RAG_CHROMADB_PORT}",
    }


# --------------------------------------------------
# Job Processing Endpoints
# --------------------------------------------------


@app.post("/api/process", response_model=ProcessJobResponse)
async def process_document(job: ProcessJobRequest):
    """
    Queue a document processing job.

    The job will be processed asynchronously by an RQ worker.
    Progress updates will be sent back to Next.js via callback.
    """
    if not job_queue:
        raise HTTPException(status_code=503, detail="Job queue not available")

    if not os.path.exists(job.filePath):
        raise HTTPException(status_code=404, detail=f"File not found: {job.filePath}")

    try:
        job_id = f"{job.collectionId}-{job.fileId}"

        rq_job = job_queue.enqueue(
            "worker.process_document_job",
            job.model_dump(),
            job_id=job_id,
            job_timeout="30m",
            result_ttl=3600,
            failure_ttl=86400,
        )

        logger.info(f"Enqueued job {job_id} for file {job.fileName}")

        return ProcessJobResponse(
            jobId=rq_job.id,
            status="queued",
            message="Document processing job queued successfully",
        )

    except Exception as e:
        logger.error(f"Failed to enqueue job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    if not job_queue:
        raise HTTPException(status_code=503, detail="Job queue not available")

    try:
        from rq.job import Job

        job = Job.fetch(job_id, connection=redis_conn)

        status_map = {
            "queued": "queued",
            "started": "processing",
            "finished": "completed",
            "failed": "failed",
        }

        return JobStatusResponse(
            jobId=job.id,
            status=status_map.get(job.get_status(), "unknown"),
            progress=job.meta.get("progress"),
            error=str(job.exc_info) if job.is_failed else None,
        )

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")


# --------------------------------------------------
# Retrieval Endpoints
# --------------------------------------------------


@app.post("/api/retrieve", response_model=RetrieveResponse)
async def retrieve_context(request: RetrieveRequest):
    """
    Perform hybrid retrieval with optional reranking.

    Combines vector search, BM25 keyword search, and knowledge graph expansion.
    Optionally applies cross-encoder reranking for improved precision.

    Supports conversational retrieval when chatHistory is provided.
    """
    try:
        request_start = time.time()
        logger.info("=" * 70)
        logger.info(
            f"Retrieval Request: collection={request.collectionId}, query='{request.query[:60]}...'"
        )
        logger.info(
            f"   Options: limit={request.limit}, rerank={request.rerank}, conversational={request.useConversationalRetrieval}"
        )

        if request.useConversationalRetrieval and request.chatHistory:
            logger.info(
                f"Using conversational retrieval with {len(request.chatHistory)} history messages"
            )

            conv_retriever = get_conversational_retriever()

            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.chatHistory
            ]

            results = conv_retriever.retrieve_with_history(
                current_query=request.query,
                collection_id=request.collectionId,
                chat_history=chat_history,
                k=request.limit,
                rerank=request.rerank,
                conversation_depth=request.conversationDepth,
            )
        else:
            logger.info("Performing standard hybrid search")

            retriever = get_retriever()

            results = retriever.search(
                query=request.query, collection_id=request.collectionId, k=request.limit
            )

            if request.rerank and results:
                logger.info(
                    f"Applying cross-encoder reranking on {len(results)} results..."
                )
                reranker = get_reranker()
                results = reranker.rerank(
                    query=request.query, results=results, top_k=request.limit
                )
            else:
                results = results[: request.limit]

        formatted_results = []
        for result in results:
            formatted_results.append(
                RetrieveResult(
                    content=result["content"],
                    fileId=result["metadata"].get("fileId")
                    if "metadata" in result
                    else None,
                    fileName=result["metadata"].get("source", "").split("/")[-1]
                    if "metadata" in result
                    else None,
                    similarity=result["score"],
                    metadata=result.get("metadata", {}),
                )
            )

        total_time = time.time() - request_start
        logger.info(f"Retrieval completed in {total_time:.3f}s")
        logger.info("=" * 70)

        return RetrieveResponse(results=formatted_results, total=len(formatted_results))

    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


# --------------------------------------------------
# Main Entry Point
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print(f"Starting RAG service on port {RAG_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=RAG_PORT, log_level="info")
