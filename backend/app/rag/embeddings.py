"""
Embedding generation and management.
"""

from hashlib import sha256
from typing import List
import re
import numpy as np

from app.utils.logger import logger


class EmbeddingModel:
    """Wrapper for embedding models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", fallback_dim: int = 384):
        """
        Initialize embedding model.

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.fallback_dim = fallback_dim
        self.model = None

        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.warning(
                f"Failed to load embedding model '{model_name}': {str(e)}. "
                "Falling back to local hash embeddings."
            )

    def _fallback_encode(self, texts: List[str]) -> np.ndarray:
        """Generate deterministic local embeddings without external downloads."""
        vectors = []

        for text in texts:
            vector = np.zeros(self.fallback_dim, dtype=np.float32)
            normalized = (text or "").lower()
            tokens = re.findall(r"\w+", normalized)

            if not tokens:
                vectors.append(vector)
                continue

            for token in tokens:
                digest = sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % self.fallback_dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[index] += sign

            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            vectors.append(vector)

        return np.vstack(vectors)

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts to embeddings.

        Args:
            texts: List of texts to encode

        Returns:
            NumPy array of embeddings
        """
        try:
            if self.model is None:
                return self._fallback_encode(texts)

            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.warning(
                f"Error encoding texts with '{self.model_name}': {str(e)}. "
                "Using local hash embeddings instead."
            )
            return self._fallback_encode(texts)

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text."""
        return self.encode([text])[0]


class OpenAIEmbedding:
    """OpenAI embedding API wrapper."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Initialize OpenAI embedding."""
        try:
            import openai

            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
            logger.info(f"Initialized OpenAI embeddings with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {str(e)}")
            raise

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model,
            )
            embeddings = np.array([item.embedding for item in response.data])
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text."""
        return self.encode([text])[0]


def create_embedding_model(use_local: bool = True, api_key: str = None):
    """Factory function to create appropriate embedding model."""
    if use_local:
        return EmbeddingModel()
    else:
        if not api_key:
            raise ValueError("API key required for OpenAI embeddings")
        return OpenAIEmbedding(api_key)
