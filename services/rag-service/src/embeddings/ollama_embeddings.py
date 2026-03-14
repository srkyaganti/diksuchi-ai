"""
Ollama-based embedding function for ChromaDB.

Delegates embedding generation to the Ollama server, keeping the Python
process lightweight. The same Ollama instance that serves the LLM also
handles embedding with a dedicated model (e.g. nomic-embed-text).
"""

import logging
from typing import List

import httpx
from chromadb import EmbeddingFunction, Documents, Embeddings

logger = logging.getLogger(__name__)


class OllamaEmbeddingFunction(EmbeddingFunction):
    """
    ChromaDB EmbeddingFunction backed by Ollama's /api/embed endpoint.
    """

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._verify_connection()
        logger.info(
            f"OllamaEmbeddingFunction ready  model={model_name}  server={base_url}"
        )

    def _verify_connection(self) -> None:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = [
                    m.get("name", "").split(":")[0]
                    for m in resp.json().get("models", [])
                ]
                if self.model_name not in models:
                    logger.warning(
                        f"Model '{self.model_name}' not found in Ollama. "
                        f"Available: {models}. Pull with: ollama pull {self.model_name}"
                    )
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: ollama serve"
            ) from exc

    def _embed_single(self, text: str, client: httpx.Client) -> List[float]:
        resp = client.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model_name, "input": text},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []

        embeddings: Embeddings = []
        with httpx.Client(timeout=self.timeout) as client:
            for text in input:
                if not text or not text.strip():
                    embeddings.append([0.0] * 768)
                    continue
                embeddings.append(self._embed_single(text, client))

        logger.debug(f"Generated {len(embeddings)} embeddings via Ollama")
        return embeddings
