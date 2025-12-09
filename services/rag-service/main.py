"""
FastAPI application for RAG document processing and retrieval.
Provides endpoints for job submission and hybrid retrieval.
"""
import os
import logging
import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
NEXTJS_CALLBACK_URL = os.getenv("NEXTJS_CALLBACK_URL", "http://localhost:3000")
NEXTJS_API_SECRET = os.getenv("NEXTJS_API_SECRET", "V4M73S6UetRTScIyQRfQCfNqG17HYESjMeh4T5XOBDQ=")
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "models/bge-m3")

# Initialize FastAPI app
app = FastAPI(
    title="RAG Worker API",
    description="Document processing and hybrid retrieval service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis connection
try:
    redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_conn.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_conn = None

# Initialize RQ Queue
job_queue = Queue("document-processing", connection=redis_conn) if redis_conn else None

# Lazy-load retrieval components (expensive initialization)
_retriever = None
_reranker = None
_conversational_retriever = None

def get_retriever():
    """Lazy initialization of HybridRetriever."""
    global _retriever
    if _retriever is None:
        from src.retrieval.hybrid_retriever import HybridRetriever
        logger.info("Initializing HybridRetriever...")
        _retriever = HybridRetriever(embedding_model_path=EMBEDDING_MODEL_PATH)
    return _retriever

def get_reranker():
    """Lazy initialization of Reranker."""
    global _reranker
    if _reranker is None:
        from src.retrieval.reranker import Reranker
        logger.info("Initializing Reranker...")
        _reranker = Reranker()
    return _reranker

def get_conversational_retriever():
    """Lazy initialization of ConversationalRetriever."""
    global _conversational_retriever
    if _conversational_retriever is None:
        from src.retrieval.conversational_retriever import ConversationalRetriever
        logger.info("Initializing ConversationalRetriever...")
        _conversational_retriever = ConversationalRetriever(
            embedding_model_path=EMBEDDING_MODEL_PATH,
            use_query_agent=False  # Disabled by default (requires additional model)
        )
    return _conversational_retriever


# Request/Response Models
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
    role: str  # "user" or "assistant"
    content: str

class RetrieveRequest(BaseModel):
    """Request model for hybrid retrieval."""
    query: str
    collectionId: str
    limit: int = 5
    rerank: bool = True
    chatHistory: Optional[List[ChatMessage]] = None  # For conversational retrieval
    useConversationalRetrieval: bool = False  # Enable conversation-aware retrieval
    conversationDepth: int = 3  # How many turns to consider

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


# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_status = "connected" if redis_conn and redis_conn.ping() else "disconnected"

    return {
        "status": "healthy",
        "service": "diksuchi-rag-service",
        "redis": redis_status,
        "embedding_model": EMBEDDING_MODEL_PATH
    }

@app.post("/api/process", response_model=ProcessJobResponse)
async def process_document(job: ProcessJobRequest):
    """
    Queue a document processing job.

    The job will be processed asynchronously by an RQ worker.
    Progress updates will be sent back to Next.js via callback.
    """
    if not job_queue:
        raise HTTPException(status_code=503, detail="Job queue not available")

    # Validate file exists
    if not os.path.exists(job.filePath):
        raise HTTPException(status_code=404, detail=f"File not found: {job.filePath}")

    try:
        # Enqueue job with job data
        job_id = f"{job.collectionId}-{job.fileId}"

        rq_job = job_queue.enqueue(
            "worker.process_document_job",
            job.model_dump(),
            job_id=job_id,
            job_timeout="30m",  # 30 minutes timeout
            result_ttl=3600,    # Keep result for 1 hour
            failure_ttl=86400   # Keep failed jobs for 1 day
        )

        logger.info(f"Enqueued job {job_id} for file {job.fileName}")

        return ProcessJobResponse(
            jobId=rq_job.id,
            status="queued",
            message=f"Document processing job queued successfully"
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
            "failed": "failed"
        }

        return JobStatusResponse(
            jobId=job.id,
            status=status_map.get(job.get_status(), "unknown"),
            progress=job.meta.get("progress"),
            error=str(job.exc_info) if job.is_failed else None
        )

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")

@app.post("/api/retrieve", response_model=RetrieveResponse)
async def retrieve_context(request: RetrieveRequest):
    """
    Perform hybrid retrieval with optional reranking.

    Combines vector search, BM25 keyword search, and knowledge graph expansion.
    Optionally applies cross-encoder reranking for improved precision.

    Supports conversational retrieval when chatHistory is provided.
    """
    try:
        # Check if conversational retrieval is requested
        if request.useConversationalRetrieval and request.chatHistory:
            logger.info(f"Using conversational retrieval with {len(request.chatHistory)} history messages")

            # Get conversational retriever
            conv_retriever = get_conversational_retriever()

            # Convert chat history to dict format
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.chatHistory
            ]

            # Perform conversation-aware retrieval (collection-specific)
            results = conv_retriever.retrieve_with_history(
                current_query=request.query,
                collection_id=request.collectionId,
                chat_history=chat_history,
                k=request.limit,
                rerank=request.rerank,
                conversation_depth=request.conversationDepth
            )
        else:
            # Standard hybrid retrieval (collection-specific)
            logger.info(f"Performing standard hybrid search for collection {request.collectionId}, query: {request.query[:50]}...")

            # Get retriever instance
            retriever = get_retriever()

            # Perform hybrid search with collection isolation
            results = retriever.search(
                query=request.query,
                collection_id=request.collectionId,
                k=request.limit
            )

            # Optional reranking
            if request.rerank and results:
                logger.info("Applying cross-encoder reranking...")
                reranker = get_reranker()
                results = reranker.rerank(
                    query=request.query,
                    results=results,
                    top_k=request.limit
                )
            else:
                # Just take top k if no reranking
                results = results[:request.limit]

        # Format results for Next.js
        formatted_results = []
        for result in results:
            formatted_results.append(RetrieveResult(
                content=result['content'],
                fileId=result['metadata'].get('fileId') if 'metadata' in result else None,
                fileName=result['metadata'].get('source', '').split('/')[-1] if 'metadata' in result else None,
                similarity=result['score'],
                metadata=result.get('metadata', {})
            ))

        return RetrieveResponse(
            results=formatted_results,
            total=len(formatted_results)
        )

    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

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
            "job_status": "GET /api/jobs/{job_id}"
        }
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("=" * 50)
    logger.info("RAG Worker API Starting...")
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"Embedding Model: {EMBEDDING_MODEL_PATH}")
    logger.info(f"Callback URL: {NEXTJS_CALLBACK_URL}")
    logger.info("=" * 50)

    # Verify embedding model exists
    if not os.path.exists(EMBEDDING_MODEL_PATH):
        logger.warning(f"⚠️  Embedding model not found at {EMBEDDING_MODEL_PATH}")
        logger.warning("Please run: python download_sentence_model.py")
    elif not os.path.isdir(EMBEDDING_MODEL_PATH):
        logger.error(f"❌ EMBEDDING_MODEL_PATH must be a directory, not a file: {EMBEDDING_MODEL_PATH}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("RAG Worker API shutting down...")
    if redis_conn:
        redis_conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")
