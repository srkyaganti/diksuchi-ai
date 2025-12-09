import logging
from typing import List
from chromadb import EmbeddingFunction, Documents, Embeddings
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    """
    ChromaDB Embedding Function using sentence-transformers.
    Supports offline operation with pre-downloaded models.
    Replaces llama-cpp for better stability and pure Python implementation.
    """

    def __init__(self, model_name_or_path: str, device: str = None):
        """
        Args:
            model_name_or_path: HuggingFace model name OR local path to downloaded model
            device: 'cuda', 'mps' (Apple Silicon), 'cpu', or None (auto-detect)
        """
        self.model_path = model_name_or_path

        # Auto-detect device if not specified
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"  # Apple Silicon
            else:
                device = "cpu"

        self.device = device

        try:
            logger.info(f"Loading sentence-transformers model: {model_name_or_path}")
            logger.info(f"Device: {device}")

            # Load model from local path (offline) or HuggingFace (online)
            self.model = SentenceTransformer(model_name_or_path, device=device)

            # Get embedding dimension
            self.dimension = self.model.get_sentence_embedding_dimension()

            logger.info(f"✓ Loaded sentence-transformers model successfully")
            logger.info(f"  Model: {model_name_or_path}")
            logger.info(f"  Device: {device}")
            logger.info(f"  Embedding dimension: {self.dimension}")

        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            raise

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for input documents."""
        try:
            # Generate embeddings (batch processing)
            embeddings = self.model.encode(
                input,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=32,
            )

            # Convert to list of lists (ChromaDB format)
            embeddings_list = embeddings.tolist()

            logger.debug(f"Generated {len(embeddings_list)} embeddings")
            return embeddings_list

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
