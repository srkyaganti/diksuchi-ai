"""
RQ Worker for document processing.
Processes documents asynchronously and updates status via callbacks.
"""

from dotenv import load_dotenv

load_dotenv()

import os
import sys
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import httpx
from rq import get_current_job
from rq.worker import Worker
from redis import Redis

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ingestion.pipeline import IngestionPipeline

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

# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Global Pipeline Instance
# --------------------------------------------------

_pipeline = None


def get_pipeline():
    """Lazy initialization of IngestionPipeline with Ollama embeddings."""
    global _pipeline
    if _pipeline is None:
        logger.info("Initializing IngestionPipeline with Ollama...")
        _pipeline = IngestionPipeline(
            ollama_model=RAG_EMBEDDING_MODEL, ollama_url=RAG_OLLAMA_URL
        )
    return _pipeline


# --------------------------------------------------
# Callback Functions
# --------------------------------------------------


async def update_file_status(
    file_id: str, rag_status: str, rag_error: str = None, processed_at: str = None
):
    """
    Send status update callback to Next.js API.

    Args:
        file_id: The file ID to update
        rag_status: Status to set (none, processing, completed, failed)
        rag_error: Error message if failed
        processed_at: ISO timestamp when processing completed
    """
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
    file_id = job_data["fileId"]
    collection_id = job_data["collectionId"]
    file_name = job_data["fileName"]
    file_path = job_data["filePath"]
    mime_type = job_data["mimeType"]

    logger.info("=" * 60)
    logger.info(f"Processing document: {file_name}")
    logger.info(f"File ID: {file_id}")
    logger.info(f"Collection ID: {collection_id}")
    logger.info(f"File Path: {file_path}")
    logger.info(f"MIME Type: {mime_type}")
    logger.info("=" * 60)

    job_start_time = time.time()
    logger.info(f"Job start timestamp: {job_start_time}")

    try:
        asyncio.run(update_file_status(file_id, "processing"))
        update_job_progress(10, "Starting document processing")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        pipeline = get_pipeline()
        update_job_progress(25, "Initialized processing pipeline")

        if mime_type == "application/pdf" or file_path.endswith(".pdf"):
            logger.info(f"Processing as PDF for collection {collection_id}...")
            update_job_progress(30, "Parsing PDF document")
            asyncio.run(pipeline.process_pdf(file_path, collection_id, file_id))
            update_job_progress(75, "PDF processing completed")

        elif (
            mime_type == "application/xml"
            or mime_type == "text/xml"
            or file_path.endswith(".xml")
        ):
            logger.info(f"Processing as S1000D XML for collection {collection_id}...")
            update_job_progress(30, "Parsing S1000D XML document")
            asyncio.run(pipeline.process_s1000d(file_path, collection_id, file_id))
            update_job_progress(75, "S1000D processing completed")

        elif mime_type == "text/plain" or file_path.endswith(".txt"):
            logger.info(f"Processing as plain text for collection {collection_id}...")
            update_job_progress(30, "Parsing text document")
            asyncio.run(pipeline.process_pdf(file_path, collection_id, file_id))
            update_job_progress(75, "Text processing completed")

        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

        update_job_progress(85, "Building search indices")
        build_bm25_index(pipeline, collection_id)

        update_job_progress(100, "Document processing completed")
        processed_at = datetime.utcnow().isoformat() + "Z"
        asyncio.run(update_file_status(file_id, "completed", processed_at=processed_at))

        job_duration = time.time() - job_start_time
        logger.info(f"Processing completed in {job_duration:.2f} seconds")
        logger.info(f"Successfully processed document: {file_name}")

        return {
            "status": "completed",
            "fileId": file_id,
            "fileName": file_name,
            "processedAt": processed_at,
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


def build_bm25_index(pipeline: IngestionPipeline, collection_id: str):
    """
    Build or update BM25 keyword search index for a specific collection.

    Args:
        pipeline: IngestionPipeline instance
        collection_id: Collection ID to build index for

    This ensures BM25 indices are isolated per collection.
    """
    import bm25s

    index_path = f"data/bm25_index/collection_{collection_id}"

    if os.path.exists(index_path):
        logger.info(
            f"BM25 index already exists for collection {collection_id}, skipping rebuild"
        )
        return

    try:
        logger.info(f"Building BM25 index for collection {collection_id}...")

        collection = pipeline._get_collection(collection_id)

        results = collection.get(include=["documents", "metadatas"])

        if not results["ids"]:
            logger.warning(
                f"No documents found in collection {collection_id}, skipping BM25 index"
            )
            return

        documents = results["documents"]
        ids = results["ids"]
        metadatas = results["metadatas"]

        corpus_tokens = bm25s.tokenize(documents, stopwords="en")

        retriever = bm25s.BM25()
        retriever.index(corpus_tokens)

        os.makedirs(index_path, exist_ok=True)

        corpus_with_meta = [
            {"id": ids[i], "text": documents[i], "metadata": metadatas[i]}
            for i in range(len(ids))
        ]

        retriever.save(index_path, corpus=corpus_with_meta)
        logger.info(f"BM25 index built with {len(documents)} documents")

    except Exception as e:
        logger.error(f"Failed to build BM25 index: {e}")


# --------------------------------------------------
# Worker Main Function
# --------------------------------------------------


def main():
    """
    Start the RQ worker.

    This function initializes the worker and starts listening for jobs
    from the Redis queue.
    """
    logger.info("=" * 60)
    logger.info("RAG Worker Starting...")
    logger.info(f"Redis: {RAG_REDIS_HOST}:{RAG_REDIS_PORT}")
    logger.info(f"Ollama Model: {RAG_EMBEDDING_MODEL}")
    logger.info(f"Ollama URL: {RAG_OLLAMA_URL}")
    logger.info(f"ChromaDB: {RAG_CHROMADB_HOST}:{RAG_CHROMADB_PORT}")
    logger.info(f"Callback URL: {RAG_WEB_CALLBACK_URL}")
    logger.info("=" * 60)

    # Verify Ollama is running
    try:
        response = httpx.get(f"{RAG_OLLAMA_URL}/api/tags", timeout=10.0)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = [m.get("name", "").split(":")[0] for m in models]
        if RAG_EMBEDDING_MODEL in model_names:
            logger.info(f"Ollama model '{RAG_EMBEDDING_MODEL}' is available")
        else:
            logger.warning(
                f"Model '{RAG_EMBEDDING_MODEL}' not found. Available: {model_names}"
            )
            logger.warning(f"Pull with: ollama pull {RAG_EMBEDDING_MODEL}")
    except Exception as e:
        logger.error(f"Ollama not running at {RAG_OLLAMA_URL}: {e}")
        logger.error("Please start Ollama: ollama serve")
        sys.exit(1)

    # Connect to Redis
    try:
        redis_conn = Redis(host=RAG_REDIS_HOST, port=RAG_REDIS_PORT)
        redis_conn.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)

    logger.info("Worker initialized (SYNCHRONOUS MODE), listening for jobs...")
    logger.info("=" * 60)

    from rq import Queue
    from rq.job import Job

    queue = Queue("document-processing", connection=redis_conn)

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
