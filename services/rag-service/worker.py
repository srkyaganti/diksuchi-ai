"""
Document Processing Worker

Processes documents asynchronously via Redis (RQ) queue.
Converts PDFs to structured JSON using Docling and stores the result
alongside extracted images.
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
from src.storage.document_store import save_document

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
    Main worker function to process a document via Docling.

    Converts the PDF to structured JSON, extracts images, and stores
    both to disk under storage/{uuid}/.

    Args:
        job_data: Dictionary containing:
            - fileId: Database ID of the file
            - collectionId: Collection the file belongs to
            - fileName: Original filename
            - filePath: Absolute path to the uploaded file
            - mimeType: MIME type of the file
            - uuid: Unique storage identifier for the file

    Returns:
        dict: Processing result with status and metadata
    """
    file_id = job_data["fileId"]
    collection_id = job_data["collectionId"]
    file_name = job_data["fileName"]
    file_path = job_data["filePath"]
    mime_type = job_data["mimeType"]
    file_uuid = job_data["uuid"]

    logger.info("=" * 60)
    logger.info(f"Processing document: {file_name}")
    logger.info(f"File ID: {file_id}")
    logger.info(f"UUID: {file_uuid}")
    logger.info(f"Collection ID: {collection_id}")
    logger.info(f"File Path: {file_path}")
    logger.info(f"MIME Type: {mime_type}")
    logger.info("=" * 60)

    job_start_time = time.time()

    try:
        asyncio.run(update_file_status(file_id, "processing"))
        update_job_progress(10, "Starting document processing")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if mime_type == "application/pdf" or file_path.endswith(".pdf"):
            update_job_progress(20, "Running Docling conversion")

            result = convert_pdf(file_path)
            update_job_progress(70, "Docling conversion complete")

            update_job_progress(80, "Saving document and images")
            save_document(
                uuid=file_uuid,
                docling_json=result.document_json,
                images=result.images,
                document_id=file_uuid,
            )
            update_job_progress(95, "Document stored")

        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

        update_job_progress(100, "Document processing completed")
        processed_at = datetime.now(timezone.utc).isoformat()
        asyncio.run(update_file_status(file_id, "completed", processed_at=processed_at))

        job_duration = time.time() - job_start_time
        logger.info(f"Processing completed in {job_duration:.2f} seconds")
        logger.info(f"Successfully processed document: {file_name}")

        return {
            "status": "completed",
            "fileId": file_id,
            "uuid": file_uuid,
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
