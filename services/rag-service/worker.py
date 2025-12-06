"""
RQ Worker for document processing.
Processes documents asynchronously and updates status via callbacks.
"""
import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
import httpx
from rq import get_current_job
from rq.worker import Worker
from redis import Redis

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ingestion.pipeline import IngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
NEXTJS_CALLBACK_URL = os.getenv("NEXTJS_CALLBACK_URL", "http://localhost:3000")
NEXTJS_API_SECRET = os.getenv("NEXTJS_API_SECRET", "")
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "models/bge-m3.gguf")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Global pipeline instance (lazy-loaded)
_pipeline = None

def get_pipeline():
    """Lazy initialization of IngestionPipeline."""
    global _pipeline
    if _pipeline is None:
        logger.info("Initializing IngestionPipeline...")
        _pipeline = IngestionPipeline(embedding_model_path=EMBEDDING_MODEL_PATH)
    return _pipeline


async def update_file_status(
    file_id: str,
    rag_status: str,
    rag_error: str = None,
    processed_at: str = None
):
    """
    Send status update callback to Next.js API.

    Args:
        file_id: The file ID to update
        rag_status: Status to set (none, processing, completed, failed)
        rag_error: Error message if failed
        processed_at: ISO timestamp when processing completed
    """
    callback_url = f"{NEXTJS_CALLBACK_URL}/api/internal/file-status"

    payload = {
        "fileId": file_id,
        "ragStatus": rag_status,
    }

    if rag_error:
        payload["ragError"] = rag_error

    if processed_at:
        payload["processedAt"] = processed_at

    headers = {}
    if NEXTJS_API_SECRET:
        headers["x-api-secret"] = NEXTJS_API_SECRET

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(callback_url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Status update sent for file {file_id}: {rag_status}")
    except httpx.HTTPError as e:
        logger.error(f"Failed to send status update: {e}")
        # Don't raise - we don't want callback failures to fail the job


def update_job_progress(progress: int, message: str = ""):
    """Update the current RQ job's progress metadata."""
    try:
        job = get_current_job()
        if job:
            job.meta['progress'] = progress
            if message:
                job.meta['message'] = message
            job.save_meta()
            logger.info(f"Job progress: {progress}% - {message}")
    except Exception as e:
        logger.warning(f"Failed to update job progress: {e}")


def process_document_job(job_data: Dict[str, Any]):
    """
    Main worker function to process a document.

    This function is called by RQ workers and processes documents through
    the complete ingestion pipeline.

    Args:
        job_data: Dictionary containing:
            - fileId: Database ID of the file
            - collectionId: Collection the file belongs to
            - fileName: Original filename
            - filePath: Absolute path to the uploaded file
            - mimeType: MIME type of the file

    Returns:
        dict: Processing result with status and metadata
    """
    file_id = job_data['fileId']
    collection_id = job_data['collectionId']
    file_name = job_data['fileName']
    file_path = job_data['filePath']
    mime_type = job_data['mimeType']

    logger.info("=" * 60)
    logger.info(f"Processing document: {file_name}")
    logger.info(f"File ID: {file_id}")
    logger.info(f"Collection ID: {collection_id}")
    logger.info(f"File Path: {file_path}")
    logger.info(f"MIME Type: {mime_type}")
    logger.info("=" * 60)

    try:
        # Update status to processing
        asyncio.run(update_file_status(file_id, "processing"))
        update_job_progress(10, "Starting document processing")

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get pipeline instance
        pipeline = get_pipeline()
        update_job_progress(25, "Initialized processing pipeline")

        # Determine file type and process accordingly
        if mime_type == "application/pdf" or file_path.endswith(".pdf"):
            logger.info("Processing as PDF...")
            update_job_progress(30, "Parsing PDF document")
            asyncio.run(pipeline.process_pdf(file_path))
            update_job_progress(75, "PDF processing completed")

        elif mime_type == "application/xml" or mime_type == "text/xml" or file_path.endswith(".xml"):
            logger.info("Processing as S1000D XML...")
            update_job_progress(30, "Parsing S1000D XML document")
            asyncio.run(pipeline.process_s1000d(file_path))
            update_job_progress(75, "S1000D processing completed")

        elif mime_type == "text/plain" or file_path.endswith(".txt"):
            logger.info("Processing as plain text...")
            update_job_progress(30, "Parsing text document")
            # Process as PDF for now (will chunk and embed plain text)
            asyncio.run(pipeline.process_pdf(file_path))
            update_job_progress(75, "Text processing completed")

        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Build BM25 index (if not already built)
        update_job_progress(85, "Building search indices")
        build_bm25_index(pipeline)

        # Mark as completed
        update_job_progress(100, "Document processing completed")
        processed_at = datetime.utcnow().isoformat() + "Z"
        asyncio.run(update_file_status(
            file_id,
            "completed",
            processed_at=processed_at
        ))

        logger.info(f"✓ Successfully processed document: {file_name}")

        return {
            "status": "completed",
            "fileId": file_id,
            "fileName": file_name,
            "processedAt": processed_at,
            "message": "Document processed successfully"
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


def build_bm25_index(pipeline: IngestionPipeline):
    """
    Build or update BM25 keyword search index.

    This is a placeholder implementation. In production, you would:
    1. Extract all documents from ChromaDB
    2. Tokenize them
    3. Build BM25S index
    4. Save to disk

    For now, we'll skip if the index already exists.
    """
    import bm25s

    index_path = "data/bm25_index"

    # Skip if index already exists
    if os.path.exists(index_path):
        logger.info("BM25 index already exists, skipping rebuild")
        return

    try:
        logger.info("Building BM25 index...")

        # Get all documents from ChromaDB
        results = pipeline.collection.get(include=["documents", "metadatas"])

        if not results['ids']:
            logger.warning("No documents found in collection, skipping BM25 index")
            return

        documents = results['documents']
        ids = results['ids']
        metadatas = results['metadatas']

        # Tokenize documents
        corpus_tokens = bm25s.tokenize(documents, stopwords="en")

        # Create BM25 index
        retriever = bm25s.BM25()
        retriever.index(corpus_tokens)

        # Save index with corpus for retrieval
        os.makedirs(index_path, exist_ok=True)

        # Prepare corpus with metadata for retrieval
        corpus_with_meta = [
            {"id": ids[i], "text": documents[i], "metadata": metadatas[i]}
            for i in range(len(ids))
        ]

        retriever.save(index_path, corpus=corpus_with_meta)
        logger.info(f"✓ BM25 index built with {len(documents)} documents")

    except Exception as e:
        logger.error(f"Failed to build BM25 index: {e}")
        # Don't fail the job if BM25 indexing fails
        # Vector search will still work


def main():
    """
    Start the RQ worker.

    This function initializes the worker and starts listening for jobs
    from the Redis queue.
    """
    # Redis connection
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    logger.info("=" * 60)
    logger.info("RAG Worker Starting...")
    logger.info(f"Redis: {redis_host}:{redis_port}")
    logger.info(f"Embedding Model: {EMBEDDING_MODEL_PATH}")
    logger.info(f"Callback URL: {NEXTJS_CALLBACK_URL}")
    logger.info("=" * 60)

    # Verify embedding model exists
    if not os.path.exists(EMBEDDING_MODEL_PATH):
        logger.error(f"❌ Embedding model not found at {EMBEDDING_MODEL_PATH}")
        logger.error("Please download BGE-M3 GGUF model before starting worker")
        sys.exit(1)

    try:
        redis_conn = Redis(host=redis_host, port=redis_port)
        redis_conn.ping()
        logger.info("✓ Connected to Redis")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        sys.exit(1)

    # Create worker with queue
    worker = Worker(
        ["document-processing"],
        connection=redis_conn,
        name="rag-worker"
    )

    logger.info("✓ Worker initialized, listening for jobs...")
    logger.info("=" * 60)

    # Start working
    worker.work(with_scheduler=True, logging_level="INFO")


if __name__ == "__main__":
    main()
