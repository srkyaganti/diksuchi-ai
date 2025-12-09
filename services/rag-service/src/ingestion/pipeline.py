import os
import asyncio
import logging
from typing import List
import chromadb
# from chromadb.utils import embedding_functions # Removed default
from src.embeddings.sentence_transformer_embeddings import SentenceTransformerEmbeddingFunction

from src.ingestion.s1000d_parser import S1000DParser
from src.ingestion.pdf_parser import PDFParser
from src.storage.graph_manager import LocalGraph

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """
    Orchestrates the ingestion process:
    1. Parse Documents (XML/PDF)
    2. Chunking (if needed)
    3. Vector Store Insertion (ChromaDB) - per collection
    4. Knowledge Graph Insertion (SQLite)
    """

    def __init__(self, embedding_model_path: str = "models/bge-m3.gguf"):
        # Initialize Components
        self.s1000d_parser = S1000DParser()
        self.pdf_parser = PDFParser()
        self.graph = LocalGraph()

        # Initialize ChromaDB client with LlamaCpp Embeddings
        self.chroma_client = chromadb.PersistentClient(path="data/chroma_db")

        # Check if model exists, otherwise warn (user needs to download it)
        if not os.path.exists(embedding_model_path):
            logger.warning(f"Embedding model not found at {embedding_model_path}. Please download it.")
            # Fallback or raise error depending on policy. Here we raise to ensure correctness.
            raise FileNotFoundError(f"Model not found: {embedding_model_path}")

        self.embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name_or_path=embedding_model_path
        )
        logger.info(f"Initialized IngestionPipeline with sentence-transformers model: {embedding_model_path}")

        # Don't create a default collection - collections are now created per collectionId
        # This ensures data isolation between organizations

    def _get_collection(self, collection_id: str):
        """
        Get or create a ChromaDB collection specific to the given collectionId.
        This ensures complete data isolation between different collections/organizations.

        Args:
            collection_id: The collection ID from the web application

        Returns:
            ChromaDB collection instance
        """
        collection_name = f"collection_{collection_id}"
        logger.info(f"Using ChromaDB collection: {collection_name}")

        return self.chroma_client.get_or_create_collection(
            name=collection_name,
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

    async def process_s1000d(self, file_path: str, collection_id: str, file_id: str = None):
        logger.info(f"Processing S1000D: {file_path} for collection: {collection_id}")
        try:
            # Get collection-specific ChromaDB collection
            collection = self._get_collection(collection_id)

            data = self.s1000d_parser.parse_data_module(file_path)
            dm_id = data["dm_id"]
            logger.info(f"Parsed S1000D: {data['title']} ({dm_id})")
            logger.info(f"Content blocks: {len(data['content_blocks'])}, References: {len(data['references'])}")

            # 1. Add Document Node to Graph
            self.graph.add_node(
                node_id=dm_id,
                node_type="DataModule",
                content=data["title"],
                metadata={"title": data["title"], "schema": data["metadata"]["schema_ver"]}
            )
            logger.info(f"Added S1000D document node '{dm_id}' to knowledge graph")

            # 2. Process Content Blocks
            ids = []
            documents = []
            metadatas = []

            for block in data["content_blocks"]:
                # Vector Store Data with collection isolation
                ids.append(block["id"])
                documents.append(f"{block['section_title']}\n{block['text']}")
                metadatas.append({
                    "source": file_path,
                    "dm_id": dm_id,
                    "type": block["type"],
                    "collectionId": collection_id,  # ✅ Store for reference
                    "fileId": file_id  # ✅ Store file ID
                })

                # Graph Data (Section Node)
                self.graph.add_node(
                    node_id=block["id"],
                    node_type="Section",
                    content=block["text"][:100] + "...", # Preview
                    metadata={"title": block["section_title"]}
                )
                self.graph.add_edge(dm_id, block["id"], "CONTAINS")

            # 3. Batch Insert to collection-specific Chroma collection
            if ids:
                collection.add(ids=ids, documents=documents, metadatas=metadatas)
                logger.info(f"✓ Inserted {len(ids)} chunks into ChromaDB collection: {collection_name}")

            # 4. Process References (Graph Edges)
            for ref_dm_id in data["references"]:
                # We might not have the target node yet, but we create the edge
                # The target node will be created when that file is processed, or we can create a placeholder
                self.graph.add_edge(dm_id, ref_dm_id, "REFERENCES")
            logger.info(f"Added {len(data['references'])} reference edges to knowledge graph")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    async def process_pdf(self, file_path: str, collection_id: str, file_id: str = None):
        logger.info(f"Processing PDF: {file_path} for collection: {collection_id}")
        try:
            # Get collection-specific ChromaDB collection
            collection_name = f"collection_{collection_id}"
            collection = self._get_collection(collection_id)

            chunks = await self.pdf_parser.parse_pdf(file_path)
            logger.info(f"Received {len(chunks)} chunks from PDF parser")

            ids = []
            documents = []
            metadatas = []

            doc_name = os.path.basename(file_path)
            self.graph.add_node(doc_name, "PDFDocument", metadata={"path": file_path})
            logger.info(f"Added PDF document node '{doc_name}' to knowledge graph")

            logger.info(f"Starting to process {len(chunks)} chunks...")

            for chunk_idx, chunk in enumerate(chunks):
                logger.debug(f"Processing chunk {chunk_idx + 1}/{len(chunks)}: {chunk.get('id', 'UNKNOWN_ID')}")

                # Log chunk structure
                logger.debug(f"  Chunk keys: {chunk.keys()}")
                logger.debug(f"  Chunk text length: {len(chunk.get('text', ''))}")

                ids.append(chunk["id"])
                logger.debug(f"  ✓ Added ID: {chunk['id']}")

                documents.append(chunk["text"])
                logger.debug(f"  ✓ Added document text")

                # Add collection isolation metadata
                logger.debug(f"  Processing metadata...")
                chunk_metadata = chunk["metadata"].copy()
                logger.debug(f"    Original metadata keys: {chunk_metadata.keys()}")

                chunk_metadata["collectionId"] = collection_id  # ✅ Store for reference
                chunk_metadata["fileId"] = file_id  # ✅ Store file ID
                logger.debug(f"    Updated metadata keys: {chunk_metadata.keys()}")

                metadatas.append(chunk_metadata)
                logger.debug(f"  ✓ Added metadata")

                # Graph Node for Page
                logger.debug(f"  Adding graph node for chunk...")
                self.graph.add_node(chunk["id"], "Page", content=chunk["text"][:50])
                logger.debug(f"  ✓ Added graph node")

                logger.debug(f"  Adding graph edge...")
                self.graph.add_edge(doc_name, chunk["id"], "CONTAINS")
                logger.debug(f"  ✓ Added graph edge")

                logger.info(f"✓ Processed chunk {chunk_idx + 1}/{len(chunks)}")

            logger.info(f"Chunk processing complete. Total: {len(ids)} IDs, {len(documents)} docs, {len(metadatas)} metadatas")

            if ids:
                logger.info(f"Preparing ChromaDB insertion...")
                logger.info(f"  IDs count: {len(ids)}")
                logger.info(f"  Documents count: {len(documents)}")
                logger.info(f"  Metadatas count: {len(metadatas)}")
                logger.info(f"  First ID: {ids[0]}")
                logger.info(f"  First document length: {len(documents[0])}")
                logger.info(f"  First metadata: {metadatas[0]}")

                # Log all document lengths
                logger.info(f"Document lengths: {[len(d) for d in documents]}")

                # Validate metadata - convert non-string values to strings for ChromaDB
                logger.info(f"Validating metadata...")
                for idx, metadata in enumerate(metadatas):
                    logger.debug(f"  Chunk {idx} metadata types: {[(k, type(v).__name__) for k, v in metadata.items()]}")
                    # Convert all metadata values to strings (ChromaDB requirement)
                    metadatas[idx] = {k: str(v) for k, v in metadata.items()}
                    logger.debug(f"  Chunk {idx} metadata after conversion: {metadatas[idx]}")

                logger.info(f"Inserting chunks one-by-one to ChromaDB...")
                successful_inserts = 0

                for chunk_idx in range(len(ids)):
                    try:
                        logger.info(f"  [{chunk_idx + 1}/{len(ids)}] Inserting chunk...")
                        logger.info(f"    ID: {ids[chunk_idx]}")
                        logger.info(f"    Text length: {len(documents[chunk_idx])}")
                        logger.info(f"    Text preview: {documents[chunk_idx][:80]}")

                        collection.add(
                            ids=[ids[chunk_idx]],
                            documents=[documents[chunk_idx]],
                            metadatas=[metadatas[chunk_idx]]
                        )
                        logger.info(f"  ✓ [{chunk_idx + 1}/{len(ids)}] Chunk inserted successfully")
                        successful_inserts += 1

                    except Exception as chunk_error:
                        logger.error(f"  ✗ [{chunk_idx + 1}/{len(ids)}] Chunk FAILED: {chunk_error}", exc_info=True)
                        logger.error(f"    ID: {ids[chunk_idx]}")
                        logger.error(f"    Document: {documents[chunk_idx]}")
                        logger.error(f"    Metadata: {metadatas[chunk_idx]}")
                        # Continue to next chunk
                        continue

                logger.info(f"✓ ChromaDB insertion complete: {successful_inserts}/{len(ids)} chunks inserted")

                if successful_inserts == len(ids):
                    logger.info(f"✓ All chunks successfully inserted into ChromaDB collection: {collection_name}")
                elif successful_inserts > 0:
                    logger.warning(f"⚠ Partial insertion: {successful_inserts}/{len(ids)} chunks inserted. {len(ids) - successful_inserts} failed.")
                else:
                    logger.error(f"✗ No chunks could be inserted into ChromaDB!")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
