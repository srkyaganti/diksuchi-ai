"""
ChromaDB Vector Store

Manages per-collection ChromaDB collections for storing and querying
chunk embeddings. Runs ChromaDB in embedded (in-process) mode backed
by SQLite -- no separate service required.
"""

import logging
import os
from typing import Callable, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection

from src.embeddings.ollama_embeddings import OllamaEmbeddingFunction
from src.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


class VectorStore:
    """Thin wrapper around ChromaDB for collection-scoped operations."""

    def __init__(self):
        self._client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self._embedding_fn = OllamaEmbeddingFunction(
            model_name=OLLAMA_EMBED_MODEL,
            base_url=OLLAMA_URL,
        )
        logger.info(f"VectorStore ready  path={CHROMA_DB_PATH}")

    def _collection_name(self, collection_id: str) -> str:
        return f"collection_{collection_id}"

    def get_or_create_collection(self, collection_id: str) -> Collection:
        return self._client.get_or_create_collection(
            name=self._collection_name(collection_id),
            embedding_function=self._embedding_fn,
        )

    def get_collection(self, collection_id: str) -> Collection:
        return self._client.get_collection(
            name=self._collection_name(collection_id),
            embedding_function=self._embedding_fn,
        )

    def add_chunks(
        self,
        collection_id: str,
        chunks: List[Chunk],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Upsert a batch of chunks into the collection's vector store."""
        if not chunks:
            return

        coll = self.get_or_create_collection(collection_id)

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        BATCH = 64
        num_batches = max(1, (len(ids) + BATCH - 1) // BATCH)
        for batch_idx, start in enumerate(range(0, len(ids), BATCH)):
            end = min(start + BATCH, len(ids))
            coll.upsert(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )
            if progress_callback:
                progress_callback(batch_idx + 1, num_batches)

        logger.info(
            f"Upserted {len(chunks)} chunks into ChromaDB "
            f"collection={self._collection_name(collection_id)}"
        )

    def query(
        self,
        collection_id: str,
        query_text: str,
        n_results: int = 10,
    ) -> dict:
        """
        Semantic search over a collection.

        Returns raw ChromaDB query result dict with keys:
            ids, documents, metadatas, distances
        """
        coll = self.get_collection(collection_id)
        return coll.query(query_texts=[query_text], n_results=n_results)

    def delete_document_chunks(self, collection_id: str, document_uuid: str) -> None:
        """Remove all chunks for a specific document from the collection.

        No-ops if the underlying Chroma collection doesn't exist (e.g.
        processing failed before any chunks were embedded). Raises on real
        Chroma errors so callers can surface them.
        """
        try:
            coll = self.get_collection(collection_id)
        except Exception as exc:
            # ChromaDB raises when the collection is missing — treat as
            # "nothing to delete" rather than a hard failure.
            logger.info(
                f"No vector collection for {collection_id} "
                f"(nothing to delete for {document_uuid}): {exc}"
            )
            return

        coll.delete(where={"document_uuid": document_uuid})
        logger.info(
            f"Deleted chunks for document {document_uuid} "
            f"from collection {collection_id}"
        )
