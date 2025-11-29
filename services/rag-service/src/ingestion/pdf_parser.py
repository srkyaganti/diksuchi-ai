import os
from llama_parse import LlamaParse
from typing import List, Dict
import logging
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from src.ingestion.vision_analyzer import VisionAnalyzer

logger = logging.getLogger(__name__)

class PDFParser:
    """
    PDF Parser using LlamaParse with Markdown-aware splitting and Vision Analysis.
    """
    
    def __init__(self, api_key: str = None, vision_model_path: str = None):
        self.api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")
        
        # 1. LlamaParse Configuration
        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            premium_mode=True, 
            verbose=True,
            # Enable image extraction (LlamaParse will save images locally)
            # Note: In a real implementation, you'd configure the download path
        )
        
        # 2. Vision Analyzer
        self.vision_analyzer = VisionAnalyzer() if vision_model_path else None

    async def parse_pdf(self, file_path: str) -> List[Dict]:
        """
        Parses PDF, splits by Markdown headers (preserving tables), and analyzes images.
        """
        try:
            # A. Parse with LlamaParse
            documents = await self.parser.aload_data(file_path)
            full_markdown = "\n\n".join([doc.text for doc in documents])
            
            # B. Markdown-Aware Splitting (Preserves Tables)
            # Split by headers first to keep sections together
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
            markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            md_header_splits = markdown_splitter.split_text(full_markdown)
            
            # Then split large sections recursively, but respect code blocks/tables
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""] # Standard separators
            )
            final_chunks = text_splitter.split_documents(md_header_splits)
            
            # C. Construct Result Chunks
            processed_chunks = []
            for i, chunk in enumerate(final_chunks):
                # TODO: If we had image paths from LlamaParse, we would loop through them here
                # and call self.vision_analyzer.analyze_image(img_path)
                # For now, we assume LlamaParse put image descriptions in the text.
                
                processed_chunks.append({
                    "id": f"{os.path.basename(file_path)}_chunk_{i}",
                    "text": chunk.page_content,
                    "metadata": {
                        "source": file_path,
                        "chunk_index": i,
                        **chunk.metadata # Contains Header info
                    }
                })
            
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {str(e)}")
            raise
