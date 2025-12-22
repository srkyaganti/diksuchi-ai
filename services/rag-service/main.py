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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "bge-m3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

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
    """Lazy initialization of HybridRetriever with Ollama embeddings."""
    global _retriever
    if _retriever is None:
        from src.retrieval.hybrid_retriever import HybridRetriever
        logger.info("Initializing HybridRetriever with Ollama...")
        _retriever = HybridRetriever(
            ollama_model=OLLAMA_MODEL,
            ollama_url=OLLAMA_URL
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
        # Share existing retriever and reranker to prevent duplicate model loading
        _conversational_retriever = ConversationalRetriever(
            hybrid_retriever=get_retriever(),
            reranker=get_reranker(),
            use_query_agent=False
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
    import time

    try:
        request_start = time.time()
        logger.info("=" * 70)
        logger.info(f"📥 Retrieval Request: collection={request.collectionId}, query='{request.query[:60]}...'")
        logger.info(f"   Options: limit={request.limit}, rerank={request.rerank}, conversational={request.useConversationalRetrieval}")

        # Check if conversational retrieval is requested
        if request.useConversationalRetrieval and request.chatHistory:
            logger.info(f"🔄 Using conversational retrieval with {len(request.chatHistory)} history messages")
            conv_start = time.time()

            # Get conversational retriever
            retriever_load_start = time.time()
            conv_retriever = get_conversational_retriever()
            retriever_load_time = time.time() - retriever_load_start
            logger.info(f"   [Retriever] Loaded in {retriever_load_time:.3f}s")

            # Convert chat history to dict format
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.chatHistory
            ]

            # Perform conversation-aware retrieval (collection-specific)
            search_start = time.time()
            results = conv_retriever.retrieve_with_history(
                current_query=request.query,
                collection_id=request.collectionId,
                chat_history=chat_history,
                k=request.limit,
                rerank=request.rerank,
                conversation_depth=request.conversationDepth
            )
            search_time = time.time() - search_start
            logger.info(f"   [Search] Completed in {search_time:.3f}s, found {len(results)} results")

            conv_total = time.time() - conv_start
            logger.info(f"   [Total Conversational] {conv_total:.3f}s")
        else:
            # Standard hybrid retrieval (collection-specific)
            logger.info(f"🔍 Performing standard hybrid search")
            hybrid_start = time.time()

            # Get retriever instance
            retriever_load_start = time.time()
            retriever = get_retriever()
            retriever_load_time = time.time() - retriever_load_start
            logger.info(f"   [Retriever] Loaded in {retriever_load_time:.3f}s")

            # Perform hybrid search with collection isolation
            search_start = time.time()
            results = retriever.search(
                query=request.query,
                collection_id=request.collectionId,
                k=request.limit
            )
            search_time = time.time() - search_start
            logger.info(f"   [Hybrid Search] Completed in {search_time:.3f}s, found {len(results)} results")

            # Optional reranking
            if request.rerank and results:
                logger.info(f"   [Reranking] Applying cross-encoder reranking on {len(results)} results...")
                rerank_start = time.time()
                reranker = get_reranker()
                results = reranker.rerank(
                    query=request.query,
                    results=results,
                    top_k=request.limit
                )
                rerank_time = time.time() - rerank_start
                logger.info(f"   [Reranking] Completed in {rerank_time:.3f}s, final {len(results)} results")
            else:
                # Just take top k if no reranking
                results = results[:request.limit]
                logger.info(f"   [No Reranking] Using top {len(results)} results")

            hybrid_total = time.time() - hybrid_start
            logger.info(f"   [Total Hybrid] {hybrid_total:.3f}s")

        # Format results for Next.js
        format_start = time.time()
        formatted_results = []
        for result in results:
            formatted_results.append(RetrieveResult(
                content=result['content'],
                fileId=result['metadata'].get('fileId') if 'metadata' in result else None,
                fileName=result['metadata'].get('source', '').split('/')[-1] if 'metadata' in result else None,
                similarity=result['score'],
                metadata=result.get('metadata', {})
            ))
        format_time = time.time() - format_start
        logger.info(f"   [Formatting] {format_time:.3f}s")

        total_time = time.time() - request_start
        logger.info(f"✓ Retrieval completed in {total_time:.3f}s")
        logger.info("=" * 70)

        return RetrieveResponse(
            results=formatted_results,
            total=len(formatted_results)
        )

    except Exception as e:
        logger.error(f"❌ Retrieval failed: {e}", exc_info=True)
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
    """Application startup tasks with model warmup."""
    import time

    logger.info("=" * 70)
    logger.info("RAG Worker API Starting...")
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"Ollama Model: {OLLAMA_MODEL}")
    logger.info(f"Ollama URL: {OLLAMA_URL}")
    logger.info(f"Callback URL: {NEXTJS_CALLBACK_URL}")
    logger.info("=" * 70)

    # Verify Ollama is running
    try:
        import httpx
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=10.0)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = [m.get("name", "").split(":")[0] for m in models]
        if OLLAMA_MODEL in model_names:
            logger.info(f"✓ Ollama model '{OLLAMA_MODEL}' is available")
        else:
            logger.warning(f"⚠️  Model '{OLLAMA_MODEL}' not found in Ollama.")
            logger.warning(f"   Available: {model_names}")
            logger.warning(f"   Pull with: ollama pull {OLLAMA_MODEL}")
            return
    except Exception as e:
        logger.error(f"❌ Cannot connect to Ollama at {OLLAMA_URL}: {e}")
        logger.error("Please start Ollama: ollama serve")
        return

    logger.info("⏳ Warming up models during startup...")
    startup_start = time.time()

    # 1. Initialize HybridRetriever (uses Ollama for embeddings)
    try:
        logger.info("  [1/3] Connecting to Ollama for embeddings...")
        retriever_start = time.time()
        retriever = get_retriever()
        retriever_time = time.time() - retriever_start
        logger.info(f"  ✓ HybridRetriever initialized in {retriever_time:.2f}s")
    except Exception as e:
        logger.error(f"  ✗ Failed to initialize HybridRetriever: {e}")
        return

    # 2. Initialize Reranker (FP16 for memory efficiency)
    try:
        logger.info("  [2/3] Loading Reranker Model (FP16 cross-encoder)...")
        reranker_start = time.time()
        reranker = get_reranker()
        reranker_time = time.time() - reranker_start
        logger.info(f"  ✓ Reranker loaded in {reranker_time:.2f}s")
    except Exception as e:
        logger.error(f"  ✗ Failed to load Reranker: {e}")
        # Don't return - reranking is optional

    # 3. Initialize ConversationalRetriever (uses shared instances)
    try:
        logger.info("  [3/3] Initializing Conversational Retriever (shared instances)...")
        conv_retriever_start = time.time()
        conv_retriever = get_conversational_retriever()
        conv_retriever_time = time.time() - conv_retriever_start
        logger.info(f"  ✓ Conversational Retriever initialized in {conv_retriever_time:.2f}s")
    except Exception as e:
        logger.error(f"  ✗ Failed to initialize Conversational Retriever: {e}")
        # Don't return - conversational retrieval is optional

    total_startup_time = time.time() - startup_start
    logger.info("=" * 70)
    logger.info(f"✓ RAG Service startup complete in {total_startup_time:.2f}s")
    logger.info("  Models are warmed up and ready for requests")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("RAG Worker API shutting down...")
    if redis_conn:
        redis_conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")
