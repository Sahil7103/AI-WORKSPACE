"""
Vector database abstraction for FAISS and Pinecone.
"""

from typing import List, Tuple
import numpy as np
import json
from pathlib import Path

from app.utils.logger import logger


class VectorStore:
    """Base class for vector stores."""

    async def add_vectors(
        self, ids: List[str], vectors: np.ndarray, metadata: List[dict]
    ):
        """Add vectors to store."""
        raise NotImplementedError

    async def search(self, vector: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar vectors."""
        raise NotImplementedError

    async def delete(self, ids: List[str]):
        """Delete vectors by ID."""
        raise NotImplementedError


class FAISSVectorStore(VectorStore):
    """FAISS vector store implementation."""

    def __init__(self, embedding_dim: int = 384):
        """Initialize FAISS store."""
        try:
            import faiss

            self.faiss = faiss
            self.embedding_dim = embedding_dim
            self.index = faiss.IndexFlatL2(embedding_dim)
            self.id_map = {}  # Map index position to actual ID
            self.metadata_store = {}
            self.index_counter = 0
            logger.info(f"Initialized FAISS with dimension {embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {str(e)}")
            raise

    async def add_vectors(
        self, ids: List[str], vectors: np.ndarray, metadata: List[dict]
    ):
        """Add vectors to FAISS index."""
        try:
            # Ensure vectors are float32
            vectors = np.array(vectors, dtype=np.float32)

            # Add to index
            self.index.add(vectors)

            # Store ID mapping and metadata
            for i, (id_, meta) in enumerate(zip(ids, metadata)):
                self.id_map[self.index_counter + i] = id_
                self.metadata_store[id_] = meta

            self.index_counter += len(ids)
            logger.info(f"Added {len(ids)} vectors to FAISS index")
        except Exception as e:
            logger.error(f"Error adding vectors: {str(e)}")
            raise

    async def search(self, vector: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """Search for k nearest vectors."""
        try:
            vector = np.array([vector], dtype=np.float32)
            distances, indices = self.index.search(vector, k)

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx != -1 and idx in self.id_map:
                    id_ = self.id_map[idx]
                    results.append((id_, float(dist)))

            return results
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []

    async def delete(self, ids: List[str]):
        """Note: FAISS doesn't support deletion. Mark as deprecated."""
        logger.warning("FAISS doesn't support deletion. Use recreation if needed.")

    def save(self, path: str):
        """Save index to disk."""
        try:
            import faiss

            faiss.write_index(self.index, path + ".index")

            with open(path + ".map", "w") as f:
                json.dump(
                    {
                        "id_map": {str(k): v for k, v in self.id_map.items()},
                        "metadata": self.metadata_store,
                    },
                    f,
                )

            logger.info(f"Saved FAISS index to {path}")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")

    def load(self, path: str):
        """Load index from disk."""
        try:
            import faiss

            self.index = faiss.read_index(path + ".index")

            with open(path + ".map", "r") as f:
                data = json.load(f)
                self.id_map = {int(k): v for k, v in data["id_map"].items()}
                self.metadata_store = data["metadata"]
                self.index_counter = max(self.id_map.keys()) + 1

            logger.info(f"Loaded FAISS index from {path}")
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")


class PineconeVectorStore(VectorStore):
    """Pinecone vector store implementation."""

    def __init__(self, api_key: str, index_name: str):
        """Initialize Pinecone store."""
        try:
            import pinecone

            pinecone.init(api_key=api_key)
            self.index = pinecone.Index(index_name)
            logger.info(f"Initialized Pinecone index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            raise

    async def add_vectors(
        self, ids: List[str], vectors: np.ndarray, metadata: List[dict]
    ):
        """Add vectors to Pinecone."""
        try:
            vectors = np.array(vectors, dtype=np.float32)

            # Prepare vectors for Pinecone
            vectors_to_upsert = [
                (id_, vec.tolist(), meta)
                for id_, vec, meta in zip(ids, vectors, metadata)
            ]

            self.index.upsert(vectors=vectors_to_upsert)
            logger.info(f"Upserted {len(ids)} vectors to Pinecone")
        except Exception as e:
            logger.error(f"Error upserting vectors: {str(e)}")
            raise

    async def search(self, vector: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """Search Pinecone index."""
        try:
            results = self.index.query(vector.tolist(), top_k=k, include_metadata=True)

            return [(match["id"], 1 - match["score"]) for match in results["matches"]]
        except Exception as e:
            logger.error(f"Error searching Pinecone: {str(e)}")
            return []

    async def delete(self, ids: List[str]):
        """Delete vectors from Pinecone."""
        try:
            self.index.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from Pinecone")
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")


async def create_vector_store(use_faiss: bool = True, **kwargs) -> VectorStore:
    """Factory function to create vector store."""
    if use_faiss:
        embedding_dim = kwargs.get("embedding_dim", 384)
        return FAISSVectorStore(embedding_dim)
    else:
        api_key = kwargs.get("api_key")
        index_name = kwargs.get("index_name", "ai-copilot")
        return PineconeVectorStore(api_key, index_name)
