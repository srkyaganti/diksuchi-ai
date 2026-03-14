"""
Document Processing Worker

Processes documents asynchronously via Redis (RQ) queue.
Full pipeline: Docling PDF -> Markdown -> Section Map -> Chunks ->
               ChromaDB Embeddings + BM25 Index.
"""

from dotenv import load_dotenv

load_dotenv()

import os
import sys
import logging
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any
import httpx
from rq import get_current_job
from redis import Redis

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ingestion.docling_converter import convert_pdf
from src.ingestion.document_mapper import build_section_map
from src.ingestion.chunker import chunk_document
from src.storage.document_store import save_document
from src.storage.vector_store import VectorStore
from src.storage.bm25_store import BM25Store

# --------------------------------------------------
# Configuration
# --------------------------------------------------

RAG_REDIS_HOST = os.getenv("RAG_REDIS_HOST", "localhost")
RAG_REDIS_PORT = int(os.getenv("RAG_REDIS_PORT", "6379"))
RAG_WEB_CALLBACK_URL = os.getenv("RAG_WEB_CALLBACK_URL", "http://localhost:3000")
RAG_WEB_API_SECRET = os.getenv("RAG_WEB_API_SECRET", "changeme-in-production")

# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Singletons (initialised lazily on first job)
# --------------------------------------------------

_vector_store: VectorStore | None = None
_bm25_store: BM25Store | None = None


def _get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def _get_bm25_store() -> BM25Store:
    global _bm25_store
    if _bm25_store is None:
        _bm25_store = BM25Store()
    return _bm25_store


# --------------------------------------------------
# Callback Functions
# --------------------------------------------------


async def update_file_status(
    file_id: str, rag_status: str, rag_error: str = None, processed_at: str = None
):
    """Send status update callback to Next.js API."""
    callback_url = f"{RAG_WEB_CALLBACK_URL}/api/internal/file-status"

    payload = {
        "fileId": file_id,
        "ragStatus": rag_status,
    }

    if rag_error:
        payload["ragError"] = rag_error

    if processed_at:
        payload["processedAt"] = processed_at

    headers = {}
    if RAG_WEB_API_SECRET:
        headers["x-api-secret"] = RAG_WEB_API_SECRET

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(callback_url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Status update sent for file {file_id}: {rag_status}")
    except httpx.HTTPError as e:
        logger.error(f"Failed to send status update: {e}")


def update_job_progress(progress: int, message: str = ""):
    """Update the current RQ job's progress metadata."""
    try:
        job = get_current_job()
        if job:
            job.meta["progress"] = progress
            if message:
                job.meta["message"] = message
            job.save_meta()
            logger.info(f"Job progress: {progress}% - {message}")
    except Exception as e:
        logger.warning(f"Failed to update job progress: {e}")


# --------------------------------------------------
# Document Processing Job
# --------------------------------------------------


def process_document_job(job_data: Dict[str, Any]):
    """
    Full ingestion pipeline:
      1. Docling conversion  (PDF -> Markdown + images)
      2. Build section map   (markdown headers -> hierarchy)
      3. Chunk by sections   (section-aware splitting)
      4. Embed & store       (ChromaDB via Ollama)
      5. Build BM25 index    (keyword search)
    """
    file_id = job_data["fileId"]
    collection_id = job_data["collectionId"]
    file_name = job_data["fileName"]
    file_path = job_data["filePath"]
    mime_type = job_data["mimeType"]
    file_uuid = job_data["uuid"]

    logger.info("=" * 60)
    logger.info(f"Processing document: {file_name}")
    logger.info(f"  File ID: {file_id}  UUID: {file_uuid}")
    logger.info(f"  Collection: {collection_id}")
    logger.info("=" * 60)

    job_start_time = time.time()

    try:
        asyncio.run(update_file_status(file_id, "processing"))
        update_job_progress(5, "Starting document processing")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not (mime_type == "application/pdf" or file_path.endswith(".pdf")):
            raise ValueError(f"Unsupported file type: {mime_type}")

        # --- Step 1: Docling conversion ---
        update_job_progress(10, "Running Docling PDF conversion")
        result = convert_pdf(file_path)
        update_job_progress(40, "Docling conversion complete")

        # --- Step 2: Build section map ---
        update_job_progress(45, "Building section map")
        section_map = build_section_map(result.markdown)

        # --- Step 3: Store markdown + section map + images ---
        update_job_progress(50, "Saving document to storage")
        save_document(
            uuid=file_uuid,
            markdown=result.markdown,
            images=result.images,
            section_map=section_map,
            document_id=file_uuid,
        )

        # --- Step 4: Chunk by sections ---
        update_job_progress(60, "Chunking document by sections")
        chunks = chunk_document(
            markdown=result.markdown,
            section_map=section_map,
            document_uuid=file_uuid,
            collection_id=collection_id,
        )

        if not chunks:
            logger.warning(f"No chunks produced for {file_name}")

        # --- Step 5: Embed chunks -> ChromaDB ---
        update_job_progress(70, "Embedding chunks via Ollama")
        vector_store = _get_vector_store()
        vector_store.add_chunks(collection_id, chunks)

        # --- Step 6: Build BM25 index ---
        update_job_progress(85, "Building BM25 keyword index")
        bm25_store = _get_bm25_store()
        bm25_store.build_index(collection_id, chunks)

        # --- Done ---
        update_job_progress(100, "Document processing completed")
        processed_at = datetime.now(timezone.utc).isoformat()
        asyncio.run(update_file_status(file_id, "completed", processed_at=processed_at))

        job_duration = time.time() - job_start_time
        logger.info(
            f"Processing completed in {job_duration:.2f}s  "
            f"chunks={len(chunks)}  file={file_name}"
        )

        return {
            "status": "completed",
            "fileId": file_id,
            "uuid": file_uuid,
            "fileName": file_name,
            "processedAt": processed_at,
            "chunks": len(chunks),
            "message": "Document processed successfully",
        }

    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg)
        asyncio.run(update_file_status(file_id, "failed", rag_error=error_msg))
        raise

    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        asyncio.run(update_file_status(file_id, "failed", rag_error=error_msg))
        raise


# --------------------------------------------------
# Worker Main Function
# --------------------------------------------------


def main():
    """Start the document processing worker."""
    logger.info("=" * 60)
    logger.info("Document Processing Worker Starting...")
    logger.info(f"Redis: {RAG_REDIS_HOST}:{RAG_REDIS_PORT}")
    logger.info(f"Callback URL: {RAG_WEB_CALLBACK_URL}")
    logger.info("=" * 60)

    try:
        redis_conn = Redis(host=RAG_REDIS_HOST, port=RAG_REDIS_PORT)
        redis_conn.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)

    logger.info("Worker initialized, listening for jobs...")
    logger.info("=" * 60)

    from rq.job import Job

    while True:
        try:
            job_id = redis_conn.lpop("rq:queue:document-processing")

            if job_id:
                job_id = job_id.decode("utf-8") if isinstance(job_id, bytes) else job_id
                logger.info(f"Processing job: {job_id}")

                try:
                    job = Job.fetch(job_id, connection=redis_conn)
                    job.set_status("started")
                    job.perform()
                    job.set_status("finished")
                    logger.info(f"Job completed: {job_id}")
                except Exception as job_error:
                    logger.error(f"Job failed: {job_error}", exc_info=True)
                    job.set_status("failed")
            else:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in job loop: {e}", exc_info=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
