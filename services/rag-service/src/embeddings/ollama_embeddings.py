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
        self._dim: int | None = None  # detected on first successful embed
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

    def _sanitize(self, text: str) -> str:
        """Remove characters that can cause NaN embeddings."""
        # Strip null bytes and other control chars (keep newlines/tabs)
        cleaned = "".join(
            ch for ch in text if ch in ("\n", "\r", "\t") or not (0 <= ord(ch) < 32)
        )
        return cleaned.strip()

    def _embed_single(self, text: str, client: httpx.Client) -> List[float]:
        resp = client.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model_name, "input": text},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]

    def _zero_vector(self) -> List[float]:
        # 768 is a safe default; overridden once the real dim is known
        return [0.0] * (self._dim or 768)

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []

        embeddings: Embeddings = []
        with httpx.Client(timeout=self.timeout) as client:
            for text in input:
                cleaned = self._sanitize(text) if text else ""
                if not cleaned:
                    embeddings.append(self._zero_vector())
                    continue
                try:
                    vec = self._embed_single(cleaned, client)
                    if self._dim is None:
                        self._dim = len(vec)
                    embeddings.append(vec)
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        f"Ollama embed returned {exc.response.status_code} "
                        f"for text ({len(cleaned)} chars), using zero vector"
                    )
                    embeddings.append(self._zero_vector())

        # Back-fill any early zero vectors that used the wrong dimension
        if self._dim and embeddings:
            for i, vec in enumerate(embeddings):
                if len(vec) != self._dim:
                    embeddings[i] = [0.0] * self._dim

        logger.debug(f"Generated {len(embeddings)} embeddings via Ollama")
        return embeddings
