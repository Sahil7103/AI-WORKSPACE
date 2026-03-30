"""
Tests for RAG pipeline.
"""

import pytest
import numpy as np

from app.rag.chunking import DocumentChunker, chunk_by_sentences, chunk_by_paragraphs
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import FAISSVectorStore


class TestDocumentChunking:
    """Test chunking strategies."""

    def test_basic_chunking(self):
        """Test basic text chunking."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)

        text = "This is a test document. " * 20
        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    def test_sentence_chunking(self):
        """Test sentence-based chunking."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_by_sentences(text, max_chunk_size=50)

        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    def test_paragraph_chunking(self):
        """Test paragraph-based chunking."""
        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = chunk_by_paragraphs(text, max_chunk_size=100)

        assert len(chunks) > 0


@pytest.mark.asyncio
async def test_faiss_vector_store():
    """Test FAISS vector store."""
    store = FAISSVectorStore(embedding_dim=384)

    # Add vectors
    ids = ["doc1:chunk0", "doc1:chunk1"]
    vectors = np.random.randn(2, 384).astype(np.float32)
    metadata = [
        {"text": "chunk 1", "doc_id": "doc1"},
        {"text": "chunk 2", "doc_id": "doc1"},
    ]

    await store.add_vectors(ids, vectors, metadata)

    # Search
    query_vector = vectors[0]
    results = await store.search(query_vector, k=2)

    assert len(results) > 0
    assert results[0][0] == "doc1:chunk0"
