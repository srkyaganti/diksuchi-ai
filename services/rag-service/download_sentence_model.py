"""
Download BGE-M3 model for offline use with sentence-transformers.
Run this once with internet connection, then the model is cached locally.

Usage:
    python download_sentence_model.py

This will download ~1.5-2.5GB of model files to models/bge-m3/
"""
import os
import logging
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model to download
MODEL_NAME = "BAAI/bge-m3"

# Where to save it
MODEL_SAVE_PATH = "models/bge-m3"


def download_model():
    """Download and save BGE-M3 model locally."""
    logger.info(f"Downloading {MODEL_NAME}...")
    logger.info(f"This may take a few minutes (model size: ~1.5-2.5GB)")
    logger.info("=" * 60)

    try:
        # Download model from HuggingFace
        model = SentenceTransformer(MODEL_NAME)

        # Save to local directory
        os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
        model.save(MODEL_SAVE_PATH)

        logger.info("=" * 60)
        logger.info(f"✓ Model downloaded and saved to: {MODEL_SAVE_PATH}")
        logger.info(f"✓ Model is now available for offline use")
        logger.info(f"  Embedding dimension: {model.get_sentence_embedding_dimension()}")

        # Test it
        test_text = "This is a test sentence."
        embedding = model.encode(test_text)
        logger.info(f"✓ Test embedding generated successfully (dim: {len(embedding)})")
        logger.info("=" * 60)
        logger.info("Ready to use! Set EMBEDDING_MODEL_PATH=models/bge-m3 in .env")

    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise


if __name__ == "__main__":
    download_model()
