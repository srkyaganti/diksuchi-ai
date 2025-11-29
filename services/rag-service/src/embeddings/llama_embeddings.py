import logging
from typing import List
from chromadb import EmbeddingFunction, Documents, Embeddings
from llama_cpp import Llama

logger = logging.getLogger(__name__)

class LlamaCppEmbeddingFunction(EmbeddingFunction):
    """
    Custom Embedding Function for ChromaDB using llama-cpp-python.
    Allows using GGUF embedding models (e.g., bge-m3-gguf) for high performance.
    """
    def __init__(self, model_path: str, n_gpu_layers: int = -1):
        """
        Args:
            model_path: Path to the .gguf embedding model file.
            n_gpu_layers: Number of layers to offload to GPU (-1 for all).
        """
        self.model_path = model_path
        try:
            self.llm = Llama(
                model_path=model_path,
                embedding=True,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
        except Exception as e:
            logger.error(f"Failed to load Llama model at {model_path}: {e}")
            raise

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            # Create embedding
            # Note: llama-cpp-python returns a list of floats directly
            embed = self.llm.create_embedding(text)
            embeddings.append(embed['data'][0]['embedding'])
        return embeddings
