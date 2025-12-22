"""
Ollama-based embedding function for ChromaDB.
Connects to local Ollama server for memory-efficient embeddings.

This replaces the SentenceTransformer-based embedding function to:
1. Reduce memory usage (model runs in separate Ollama process)
2. Share embedding model between worker and API processes
3. Leverage Ollama's optimized inference (Metal acceleration, quantization)
"""
import logging
import httpx
from typing import List, Optional
from chromadb import EmbeddingFunction, Documents, Embeddings

logger = logging.getLogger(__name__)


class OllamaEmbeddingFunction(EmbeddingFunction):
    """
    ChromaDB Embedding Function using Ollama API.
    
    Memory-efficient: model runs in separate Ollama process, not in Python.
    Supports batch embedding for better throughput.
    """
    
    def __init__(
        self, 
        model_name: str = "bge-m3",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
        batch_size: int = 32
    ):
        """
        Initialize Ollama embedding function.
        
        Args:
            model_name: Ollama model name (e.g., "bge-m3", "nomic-embed-text")
            base_url: Ollama server URL
            timeout: Request timeout in seconds
            batch_size: Number of texts to embed per batch (for progress logging)
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.batch_size = batch_size
        self.dimension = 1024  # BGE-M3 dimension
        
        # Verify connection on initialization
        self._verify_connection()
        logger.info(f"✓ OllamaEmbeddingFunction initialized")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Server: {base_url}")
        logger.info(f"  Embedding dimension: {self.dimension}")
    
    def _verify_connection(self) -> None:
        """Verify Ollama server is running and model is available."""
        try:
            with httpx.Client(timeout=10.0) as client:
                # Check server is up
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                # Check if model is available
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                
                if self.model_name not in model_names:
                    logger.warning(
                        f"Model '{self.model_name}' not found in Ollama. "
                        f"Available: {model_names}. "
                        f"Pull with: ollama pull {self.model_name}"
                    )
                else:
                    logger.info(f"✓ Model '{self.model_name}' is available in Ollama")
                    
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running: ollama serve"
            ) from e
        except httpx.HTTPStatusError as e:
            raise ConnectionError(
                f"Ollama server error: {e.response.status_code}"
            ) from e
    
    def _embed_single(self, text: str, client: httpx.Client) -> List[float]:
        """Embed a single text using Ollama API."""
        response = client.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model_name,
                "prompt": text
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["embedding"]
    
    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for input documents via Ollama API.
        
        Args:
            input: List of text documents to embed
            
        Returns:
            List of embedding vectors (list of floats)
        """
        if not input:
            return []
        
        embeddings = []
        total = len(input)
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                for i, text in enumerate(input):
                    # Skip empty texts
                    if not text or not text.strip():
                        # Return zero vector for empty text
                        embeddings.append([0.0] * self.dimension)
                        continue
                    
                    embedding = self._embed_single(text, client)
                    embeddings.append(embedding)
                    
                    # Log progress for large batches
                    if total > 10 and (i + 1) % self.batch_size == 0:
                        logger.debug(f"Embedded {i + 1}/{total} texts")
            
            logger.debug(f"Generated {len(embeddings)} embeddings via Ollama")
            return embeddings
            
        except httpx.ConnectError as e:
            logger.error(f"Lost connection to Ollama: {e}")
            raise ConnectionError(
                f"Lost connection to Ollama at {self.base_url}. "
                f"Is Ollama still running?"
            ) from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Ollama embedding failed: {e}") from e
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise


class OllamaEmbeddingFunctionAsync:
    """
    Async version of OllamaEmbeddingFunction for high-throughput scenarios.
    Note: ChromaDB doesn't support async embedding functions directly,
    but this can be used for pre-computing embeddings.
    """
    
    def __init__(
        self,
        model_name: str = "bge-m3",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
        max_concurrent: int = 5
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.dimension = 1024
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts concurrently."""
        import asyncio
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def embed_with_semaphore(text: str) -> List[float]:
            async with semaphore:
                return await self._embed_single_async(text)
        
        tasks = [embed_with_semaphore(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    async def _embed_single_async(self, text: str) -> List[float]:
        """Embed a single text asynchronously."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
