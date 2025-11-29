import os
import asyncio
import logging
from typing import List
import chromadb
# from chromadb.utils import embedding_functions # Removed default
from src.embeddings.llama_embeddings import LlamaCppEmbeddingFunction

from src.ingestion.s1000d_parser import S1000DParser
from src.ingestion.pdf_parser import PDFParser
from src.storage.graph_manager import LocalGraph

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """
    Orchestrates the ingestion process:
    1. Parse Documents (XML/PDF)
    2. Chunking (if needed)
    3. Vector Store Insertion (ChromaDB)
    4. Knowledge Graph Insertion (SQLite)
    """
    
    def __init__(self, embedding_model_path: str = "models/bge-m3.gguf"):
        # Initialize Components
        self.s1000d_parser = S1000DParser()
        self.pdf_parser = PDFParser()
        self.graph = LocalGraph()
        
        # Initialize ChromaDB with LlamaCpp Embeddings
        self.chroma_client = chromadb.PersistentClient(path="data/chroma_db")
        
        # Check if model exists, otherwise warn (user needs to download it)
        if not os.path.exists(embedding_model_path):
            logger.warning(f"Embedding model not found at {embedding_model_path}. Please download it.")
            # Fallback or raise error depending on policy. Here we raise to ensure correctness.
            raise FileNotFoundError(f"Model not found: {embedding_model_path}")

        self.embedding_fn = LlamaCppEmbeddingFunction(model_path=embedding_model_path)
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="manuals",
            embedding_function=self.embedding_fn
        )

    async def process_directory(self, directory_path: str):
        """Process all supported files in a directory."""
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(".xml"):
                    await self.process_s1000d(file_path)
                elif file.endswith(".pdf"):
                    await self.process_pdf(file_path)

    async def process_s1000d(self, file_path: str):
        logger.info(f"Processing S1000D: {file_path}")
        try:
            data = self.s1000d_parser.parse_data_module(file_path)
            dm_id = data["dm_id"]
            
            # 1. Add Document Node to Graph
            self.graph.add_node(
                node_id=dm_id,
                node_type="DataModule",
                content=data["title"],
                metadata={"title": data["title"], "schema": data["metadata"]["schema_ver"]}
            )
            
            # 2. Process Content Blocks
            ids = []
            documents = []
            metadatas = []
            
            for block in data["content_blocks"]:
                # Vector Store Data
                ids.append(block["id"])
                documents.append(f"{block['section_title']}\n{block['text']}")
                metadatas.append({
                    "source": file_path,
                    "dm_id": dm_id,
                    "type": block["type"]
                })
                
                # Graph Data (Section Node)
                self.graph.add_node(
                    node_id=block["id"],
                    node_type="Section",
                    content=block["text"][:100] + "...", # Preview
                    metadata={"title": block["section_title"]}
                )
                self.graph.add_edge(dm_id, block["id"], "CONTAINS")
                
            # 3. Batch Insert to Chroma
            if ids:
                self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
                
            # 4. Process References (Graph Edges)
            for ref_dm_id in data["references"]:
                # We might not have the target node yet, but we create the edge
                # The target node will be created when that file is processed, or we can create a placeholder
                self.graph.add_edge(dm_id, ref_dm_id, "REFERENCES")
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    async def process_pdf(self, file_path: str):
        logger.info(f"Processing PDF: {file_path}")
        try:
            chunks = await self.pdf_parser.parse_pdf(file_path)
            
            ids = []
            documents = []
            metadatas = []
            
            doc_name = os.path.basename(file_path)
            self.graph.add_node(doc_name, "PDFDocument", metadata={"path": file_path})
            
            for chunk in chunks:
                ids.append(chunk["id"])
                documents.append(chunk["text"])
                metadatas.append(chunk["metadata"])
                
                # Graph Node for Page
                self.graph.add_node(chunk["id"], "Page", content=chunk["text"][:50])
                self.graph.add_edge(doc_name, chunk["id"], "CONTAINS")
                
            if ids:
                self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
