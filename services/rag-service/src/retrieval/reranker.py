"""
Cross-Encoder Reranker

Reranks retrieval results using a cross-encoder model for precision.
Loads on GPU when available (RTX 5090 handles this easily alongside the LLM).
"""

import logging
from typing import List, Dict

import torch
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    """Reranks candidate results by cross-encoder relevance score."""

    def __init__(self, model_name: str = DEFAULT_MODEL, use_fp16: bool = True):
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        automodel_args = {}
        if use_fp16 and self.device in ("cuda", "mps"):
            automodel_args["torch_dtype"] = torch.float16

        logger.info(f"Loading reranker {model_name} on {self.device}")
        self.model = CrossEncoder(
            model_name,
            device=self.device,
            automodel_args=automodel_args,
        )
        logger.info("Reranker loaded")

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Rerank results by cross-encoder score.

        Args:
            query:   The user's question.
            results: List of dicts with at least a 'text' key.
            top_k:   How many to return after reranking.

        Returns:
            Top-k results sorted by reranker score (descending).
        """
        if not results:
            return []

        pairs = [[query, r["text"]] for r in results]
        scores = self.model.predict(pairs)

        for i, r in enumerate(results):
            r["rerank_score"] = float(scores[i])

        results.sort(key=lambda r: r["rerank_score"], reverse=True)
        return results[:top_k]
