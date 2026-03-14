"""
Hybrid Retriever

Combines vector search (ChromaDB) and keyword search (BM25), merges
results with Reciprocal Rank Fusion (RRF), and expands top hits to
full parent sections using the document map.
"""

import logging
import time
from typing import Dict, List

from src.storage.vector_store import VectorStore
from src.storage.bm25_store import BM25Store

logger = logging.getLogger(__name__)

RRF_K = 60  # standard RRF constant


class HybridRetriever:
    """
    Performs hybrid search: vector + BM25, merged via RRF.
    Stateless per query; stores are injected.
    """

    def __init__(self, vector_store: VectorStore, bm25_store: BM25Store):
        self.vector_store = vector_store
        self.bm25_store = bm25_store

    def search(
        self,
        query: str,
        collection_id: str,
        k: int = 20,
    ) -> List[Dict]:
        """
        Run hybrid search and return merged results sorted by RRF score.

        Each result dict: { id, text, metadata, score, source }
        """
        t0 = time.time()
        results_map: Dict[str, Dict] = {}

        # --- Vector search ---
        try:
            vec_res = self.vector_store.query(collection_id, query, n_results=k)
            ids_outer = vec_res.get("ids") or [[]]
            docs_outer = vec_res.get("documents") or [[]]
            metas_outer = vec_res.get("metadatas") or [[]]

            ids_list = ids_outer[0] if ids_outer else []
            docs_list = docs_outer[0] if docs_outer else []
            metas_raw = metas_outer[0] if metas_outer else []
            metas_list = [m if isinstance(m, dict) else {} for m in (metas_raw or [])]

            for rank, (doc_id, doc_text, doc_meta) in enumerate(
                zip(ids_list, docs_list, metas_list)
            ):
                rrf_score = 1.0 / (RRF_K + rank + 1)
                results_map[doc_id] = {
                    "id": doc_id,
                    "text": doc_text or "",
                    "metadata": doc_meta,
                    "score": rrf_score,
                    "source": "vector",
                }
            logger.info(f"  Vector search: {len(ids_list)} hits")
        except Exception as exc:
            logger.warning(f"  Vector search failed: {exc}")

        # --- BM25 search ---
        try:
            bm25_hits = self.bm25_store.search(collection_id, query, k=k)
            for rank, hit in enumerate(bm25_hits):
                rrf_score = 1.0 / (RRF_K + rank + 1)
                doc_id = hit["id"]
                if doc_id in results_map:
                    results_map[doc_id]["score"] += rrf_score
                    results_map[doc_id]["source"] = "hybrid"
                else:
                    results_map[doc_id] = {
                        "id": doc_id,
                        "text": hit["text"],
                        "metadata": hit["metadata"],
                        "score": rrf_score,
                        "source": "bm25",
                    }
            logger.info(f"  BM25 search: {len(bm25_hits)} hits")
        except Exception as exc:
            logger.warning(f"  BM25 search failed: {exc}")

        merged = sorted(results_map.values(), key=lambda r: r["score"], reverse=True)

        elapsed = time.time() - t0
        logger.info(
            f"  Hybrid search complete: {len(merged)} unique results in {elapsed:.3f}s"
        )

        return merged
