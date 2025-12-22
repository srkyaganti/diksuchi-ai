import torch
from sentence_transformers import CrossEncoder
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class Reranker:
    """
    Reranks retrieval results using a Cross-Encoder model.
    Supports FP16 for memory efficiency on Apple Silicon / CUDA.
    """
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", use_fp16: bool = True):
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Loading Reranker {model_name} on {self.device}...")
        
        # Configure FP16 for memory efficiency (~50% reduction)
        automodel_args = {}
        if use_fp16 and self.device in ["cuda", "mps"]:
            automodel_args["torch_dtype"] = torch.float16
            logger.info("Using FP16 for memory efficiency (saves ~50% memory)")
        
        try:
            self.model = CrossEncoder(
                model_name, 
                device=self.device,
                automodel_args=automodel_args
            )
            logger.info(f"✓ Reranker loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load reranker: {e}")
            raise

    def rerank(self, query: str, results: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Reranks a list of results based on relevance to the query.

        PHASE 1: Safety-constrained reranking
        - Separates safety-critical items from normal results
        - Only reranks normal results with cross-encoder
        - Preserves safety items in top positions
        - Returns safety items first, then reranked normal items
        """
        if not results:
            return []

        # PHASE 1: Safety-constrained reranking
        # Separate safety-critical from normal results
        safety_results = [r for r in results if r.get("is_safety_critical", False)]
        normal_results = [r for r in results if not r.get("is_safety_critical", False)]

        logger.info(
            f"Reranking: {len(safety_results)} safety items + {len(normal_results)} normal items"
        )

        # Rerank ONLY normal results
        if normal_results:
            # Prepare pairs for the model: (query, document_text)
            pairs = [[query, res['content']] for res in normal_results]

            # Predict scores
            scores = self.model.predict(pairs)

            # Update scores in result objects
            for i, res in enumerate(normal_results):
                res['score'] = float(scores[i])  # Convert numpy float to python float

            # Sort normal results by new score
            normal_results.sort(key=lambda x: x['score'], reverse=True)

            logger.debug(
                f"Reranked {len(normal_results)} normal results. "
                f"Top score: {normal_results[0]['score']:.3f}"
            )

        # PHASE 1: Safety-first merge strategy
        # Combine: Safety items first (never demoted), then reranked normal items
        num_safety = len(safety_results)
        num_normal_slots = max(0, top_k - num_safety)

        final_results = safety_results + normal_results[:num_normal_slots]

        logger.info(
            f"Final ranking: {num_safety} safety items + {len(normal_results[:num_normal_slots])} "
            f"normal items = {len(final_results)} results"
        )

        return final_results[:top_k]
