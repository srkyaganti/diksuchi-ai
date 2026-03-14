"""
RAG Service API

Provides endpoints for:
  - Submitting PDF processing jobs (Docling conversion + indexing)
  - Checking job status
  - Hybrid retrieval (vector + BM25 + reranking + section expansion)
"""

from dotenv import load_dotenv

load_dotenv()

import os
import sys
import logging
import time
from typing import List, Optional
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue

# --------------------------------------------------
# Configuration
# --------------------------------------------------

RAG_REDIS_HOST = os.getenv("RAG_REDIS_HOST", "localhost")
RAG_REDIS_PORT = int(os.getenv("RAG_REDIS_PORT", "6379"))
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

# Retrieval components (lazy-initialised on first /api/retrieve call)
_hybrid_retriever = None
_reranker = None


def _get_retriever():
    global _hybrid_retriever
    if _hybrid_retriever is None:
        from src.retrieval.hybrid_retriever import HybridRetriever
        from src.storage.vector_store import VectorStore
        from src.storage.bm25_store import BM25Store

        _hybrid_retriever = HybridRetriever(
            vector_store=VectorStore(),
            bm25_store=BM25Store(),
        )
    return _hybrid_retriever


def _get_reranker():
    global _reranker
    if _reranker is None:
        from src.retrieval.reranker import Reranker

        _reranker = Reranker()
    return _reranker


# --------------------------------------------------
# Lifespan Event Handler
# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_conn, job_queue

    logger.info("=" * 70)
    logger.info("RAG Service API Starting...")
    logger.info(f"Redis: {RAG_REDIS_HOST}:{RAG_REDIS_PORT}")
    logger.info("=" * 70)

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

    logger.info("=" * 70)
    logger.info("RAG Service API ready")
    logger.info("=" * 70)

    yield

    logger.info("RAG Service API shutting down...")
    if redis_conn:
        redis_conn.close()


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="Diksuchi RAG Service",
    description="Document processing and hybrid retrieval service",
    version="3.0.0",
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
    fileId: str
    collectionId: str
    fileName: str
    filePath: str
    mimeType: str
    uuid: str


class ProcessJobResponse(BaseModel):
    jobId: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    jobId: str
    status: str
    progress: Optional[int] = None
    error: Optional[str] = None


class RetrieveRequest(BaseModel):
    query: str
    collectionId: str
    topK: int = 5


class SectionResult(BaseModel):
    content: str
    sectionPath: str
    sectionId: str
    documentUuid: str
    score: float


class RetrieveResponse(BaseModel):
    sections: List[SectionResult]
    timingMs: float


# --------------------------------------------------
# Health Endpoints
# --------------------------------------------------


@app.get("/")
async def root():
    return {
        "service": "Diksuchi AI RAG Service",
        "version": "3.0.0",
        "endpoints": {
            "health": "/health",
            "process": "POST /api/process",
            "job_status": "GET /api/jobs/{job_id}",
            "retrieve": "POST /api/retrieve",
        },
    }


@app.get("/health")
async def health_check():
    redis_status = "connected" if redis_conn and redis_conn.ping() else "disconnected"

    return {
        "status": "healthy",
        "service": "diksuchi-rag-service",
        "redis": redis_status,
    }


# --------------------------------------------------
# Job Processing Endpoints
# --------------------------------------------------


@app.post("/api/process", response_model=ProcessJobResponse)
async def process_document(job: ProcessJobRequest):
    """Queue a document processing job."""
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
# Retrieval Endpoint
# --------------------------------------------------


@app.post("/api/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest):
    """
    Hybrid retrieval: vector + BM25 -> RRF merge -> rerank -> section expansion.

    Returns full parent sections so the LLM has complete context.
    """
    t0 = time.time()

    try:
        retriever = _get_retriever()
        reranker = _get_reranker()
    except Exception as exc:
        logger.error(f"Failed to initialise retrieval components: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"Retrieval service not ready: {exc}",
        )

    from src.retrieval.section_expander import expand_to_sections

    # Step 1: Hybrid search (vector + BM25 with RRF)
    merged_results = retriever.search(
        query=req.query,
        collection_id=req.collectionId,
        k=20,
    )

    if not merged_results:
        elapsed_ms = (time.time() - t0) * 1000
        return RetrieveResponse(sections=[], timingMs=round(elapsed_ms, 1))

    # Step 2: Rerank top candidates
    reranked = reranker.rerank(
        query=req.query,
        results=merged_results,
        top_k=req.topK * 2,
    )

    # Step 3: Expand to full sections
    sections = expand_to_sections(reranked, top_k=req.topK)

    elapsed_ms = (time.time() - t0) * 1000

    logger.info(
        f"Retrieve: query='{req.query[:60]}' "
        f"collection={req.collectionId} "
        f"sections={len(sections)} "
        f"time={elapsed_ms:.0f}ms"
    )

    return RetrieveResponse(
        sections=[
            SectionResult(
                content=s["content"],
                sectionPath=s["section_path"],
                sectionId=s["section_id"],
                documentUuid=s["document_uuid"],
                score=s["score"],
            )
            for s in sections
        ],
        timingMs=round(elapsed_ms, 1),
    )


# --------------------------------------------------
# Main Entry Point
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print(f"Starting RAG Service on port {RAG_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=RAG_PORT, log_level="info")
