"""
Embedding generation and management.
"""

from typing import List
import numpy as np

from app.utils.logger import logger


class EmbeddingModel:
    """Wrapper for embedding models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model.

        Args:
            model_name: HuggingFace model identifier
        """
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts to embeddings.

        Args:
            texts: List of texts to encode

        Returns:
            NumPy array of embeddings
        """
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            raise

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
