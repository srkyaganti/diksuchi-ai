import os
from typing import List, Dict
import logging
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class PDFParser:
    """
    Local PDF Parser using pdfplumber (offline-capable, no internet required).
    Extracts text and splits into chunks for embedding and indexing.
    """

    def __init__(self, vision_model_path: str = None):
        # Local parser - no API key needed
        # vision_model_path not used currently, but kept for API compatibility
        pass

    async def parse_pdf(self, file_path: str) -> List[Dict]:
        """
        Parses PDF using pdfplumber (local, offline).
        Extracts text and chunks it for embedding.
        """
        try:
            # A. Extract text from PDF using pdfplumber
            full_text = ""
            page_contents = []

            with pdfplumber.open(file_path) as pdf:
                logger.info(f"Opened PDF with {len(pdf.pages)} pages")

                for page_num, page in enumerate(pdf.pages):
                    # Extract text from page
                    text = page.extract_text()
                    if text:
                        page_contents.append({
                            "page_num": page_num + 1,
                            "text": text
                        })
                        full_text += f"\n\n--- Page {page_num + 1} ---\n\n{text}"

            logger.info(f"Extracted text from {len(page_contents)} pages")

            # B. Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]  # Standard separators
            )

            # Split the full text
            chunks = text_splitter.split_text(full_text)
            logger.info(f"Split into {len(chunks)} chunks using RecursiveCharacterTextSplitter")

            # C. Construct Result Chunks with metadata
            processed_chunks = []
            for i, chunk_text in enumerate(chunks):
                # Determine which page(s) this chunk came from (approximate)
                page_num = min(i // max(1, len(chunks) // len(page_contents)) + 1, len(page_contents))

                processed_chunks.append({
                    "id": f"{os.path.basename(file_path)}_chunk_{i}",
                    "text": chunk_text,
                    "metadata": {
                        "source": file_path,
                        "chunk_index": i,
                        "page": page_num,
                        "total_pages": len(page_contents)
                    }
                })

            logger.info(f"✓ Successfully parsed PDF: {os.path.basename(file_path)} ({len(processed_chunks)} chunks)")
            return processed_chunks

        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {str(e)}")
            raise
