import torch
from sentence_transformers import CrossEncoder
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class Reranker:
    """
    Reranks retrieval results using a Cross-Encoder model.
    """
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Loading Reranker {model_name} on {self.device}...")
        try:
            self.model = CrossEncoder(model_name, device=self.device)
        except Exception as e:
            logger.error(f"Failed to load reranker: {e}")
            raise

    def rerank(self, query: str, results: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Reranks a list of results based on relevance to the query.
        """
        if not results:
            return []

        # Prepare pairs for the model: (query, document_text)
        pairs = [[query, res['content']] for res in results]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Update scores in result objects
        for i, res in enumerate(results):
            res['score'] = float(scores[i]) # Convert numpy float to python float
            
        # Sort by new score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:top_k]
