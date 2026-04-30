"""
BM25 Index Store

Builds and persists per-collection BM25 indices using bm25s.
Indices are stored on disk at data/bm25_index/collection_{id}/ and
loaded on demand for keyword search during retrieval.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import bm25s

from src.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)

BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", "data/bm25_index")


class BM25Store:
    """Manages per-collection BM25 indices."""

    def __init__(self):
        self._indices: Dict[str, bm25s.BM25] = {}
        self._corpora: Dict[str, List[dict]] = {}
        Path(BM25_INDEX_PATH).mkdir(parents=True, exist_ok=True)
        logger.info(f"BM25Store ready  path={BM25_INDEX_PATH}")

    def _index_dir(self, collection_id: str) -> str:
        return os.path.join(BM25_INDEX_PATH, f"collection_{collection_id}")

    def build_index(self, collection_id: str, chunks: List[Chunk]) -> None:
        """
        Build (or rebuild) the BM25 index for a collection from chunks.

        The corpus is stored alongside the index so that search results
        can return the original chunk text and metadata.
        """
        if not chunks:
            return

        corpus_dicts = [
            {"id": c.chunk_id, "text": c.text, "metadata": c.metadata}
            for c in chunks
        ]
        self._persist_corpus(collection_id, corpus_dicts)
        logger.info(
            f"Built BM25 index for collection {collection_id}: "
            f"{len(chunks)} chunks"
        )

    def _persist_corpus(self, collection_id: str, corpus_dicts: List[dict]) -> None:
        """Tokenize, index, and persist the given corpus to disk.

        If the corpus is empty, removes any existing on-disk index and
        clears in-memory caches so subsequent searches get an empty result.
        """
        index_dir = self._index_dir(collection_id)

        if not corpus_dicts:
            if os.path.exists(index_dir):
                shutil.rmtree(index_dir)
            self._indices.pop(collection_id, None)
            self._corpora.pop(collection_id, None)
            logger.info(
                f"Removed BM25 index for collection {collection_id} (empty corpus)"
            )
            return

        corpus_texts = [c["text"] for c in corpus_dicts]
        tokenized = bm25s.tokenize(corpus_texts)
        retriever = bm25s.BM25()
        retriever.index(tokenized)

        Path(index_dir).mkdir(parents=True, exist_ok=True)
        retriever.save(index_dir, corpus=corpus_dicts)

        self._indices[collection_id] = retriever
        self._corpora[collection_id] = corpus_dicts

    def remove_document(self, collection_id: str, document_uuid: str) -> int:
        """Remove a document's chunks from the BM25 index by rebuilding without them.

        Returns the number of chunks removed. No-ops when the index doesn't
        exist (e.g. processing failed before BM25 was built) or when the
        document has no chunks in the index.
        """
        if collection_id not in self._corpora and not self._load_index(collection_id):
            logger.info(
                f"No BM25 index for collection {collection_id} "
                f"(nothing to remove for {document_uuid})"
            )
            return 0

        corpus = self._corpora[collection_id]
        filtered = [
            c for c in corpus
            if c.get("metadata", {}).get("document_uuid") != document_uuid
        ]
        removed = len(corpus) - len(filtered)

        if removed == 0:
            logger.info(
                f"No BM25 chunks for document {document_uuid} "
                f"in collection {collection_id}"
            )
            return 0

        self._persist_corpus(collection_id, filtered)
        logger.info(
            f"Removed {removed} BM25 chunk(s) for document {document_uuid} "
            f"from collection {collection_id}"
        )
        return removed

    def _load_index(self, collection_id: str) -> bool:
        """Load a persisted BM25 index from disk. Returns True on success."""
        index_dir = self._index_dir(collection_id)
        if not os.path.exists(index_dir):
            return False

        try:
            retriever = bm25s.BM25.load(index_dir, load_corpus=True)
            self._indices[collection_id] = retriever
            self._corpora[collection_id] = list(retriever.corpus)
            logger.info(f"Loaded BM25 index for collection {collection_id}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to load BM25 index for {collection_id}: {exc}")
            return False

    def search(
        self,
        collection_id: str,
        query: str,
        k: int = 10,
    ) -> List[dict]:
        """
        Keyword search over a collection's BM25 index.

        Returns list of dicts: { id, text, metadata, score }
        """
        if collection_id not in self._indices:
            if not self._load_index(collection_id):
                logger.info(f"No BM25 index for collection {collection_id}")
                return []

        retriever = self._indices[collection_id]
        corpus = self._corpora.get(collection_id, [])
        if not corpus:
            return []

        tokenized_query = bm25s.tokenize(query)
        docs, scores = retriever.retrieve(tokenized_query, corpus=corpus, k=min(k, len(corpus)))

        hits: List[dict] = []
        for i, doc in enumerate(docs[0]):
            if doc is None:
                continue
            score = float(scores[0][i])
            hits.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": score,
            })

        return hits
