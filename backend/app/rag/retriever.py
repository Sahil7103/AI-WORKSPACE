"""
RAG retriever - combines chunking, embeddings, and vector search.
"""

from typing import List, Optional
import numpy as np

from app.rag.chunking import DocumentChunker
from app.rag.embeddings import create_embedding_model
from app.rag.vector_store import create_vector_store
from app.utils.logger import logger


class RAGRetriever:
    """
    Retrieval-Augmented Generation pipeline.

    Pipeline:
    1. Chunk document
    2. Generate embeddings for chunks
    3. Store in vector database
    4. Retrieve relevant chunks for queries
    """

    def __init__(
        self,
        embedding_model=None,
        vector_store=None,
        chunker=None,
        use_faiss: bool = True,
        use_local_embeddings: bool = True,
    ):
        """Initialize RAG retriever."""
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.chunker = chunker or DocumentChunker()
        self.use_faiss = use_faiss
        self.use_local_embeddings = use_local_embeddings

        logger.info("Initialized RAG Retriever")

    async def initialize_vector_store(self) -> None:
        """Initialize vector store."""
        if not self.vector_store:
            self.vector_store = await create_vector_store(use_faiss=self.use_faiss)

    def initialize_embedding_model(self) -> None:
        """Initialize embedding model lazily."""
        if self.embedding_model is None:
            self.embedding_model = create_embedding_model(self.use_local_embeddings)

    def has_indexed_content(self) -> bool:
        """Return whether the current vector store appears to contain data."""
        if not self.vector_store:
            return False

        metadata_store = getattr(self.vector_store, "metadata_store", None)
        if metadata_store is not None:
            return len(metadata_store) > 0

        index = getattr(self.vector_store, "index", None)
        if index is not None and hasattr(index, "ntotal"):
            return index.ntotal > 0

        return True

    async def process_document(
        self, doc_id: str, content: str, metadata: dict = None
    ) -> List[dict]:
        """
        Process a document: chunk, embed, and store.

        Args:
            doc_id: Document identifier
            content: Document text content
            metadata: Optional metadata

        Returns:
            List of chunk metadata
        """
        try:
            # Initialize vector store if needed
            await self.initialize_vector_store()
            self.initialize_embedding_model()

            # Chunk document
            chunks = self.chunker.chunk_text(content)
            logger.info(f"Chunked document {doc_id} into {len(chunks)} chunks")

            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks)

            # Prepare metadata
            chunk_metadata = [
                {
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "text": chunk,
                    **metadata,
                }
                for i, chunk in enumerate(chunks)
            ]

            # Store in vector database
            chunk_ids = [f"{doc_id}:chunk:{i}" for i in range(len(chunks))]
            await self.vector_store.add_vectors(chunk_ids, embeddings, chunk_metadata)

            logger.info(f"Stored {len(chunks)} embeddings for document {doc_id}")
            return chunk_metadata

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    async def index_existing_chunks(
        self,
        doc_id: str,
        chunks: List[dict],
        metadata: dict = None,
    ) -> List[dict]:
        """Index existing chunk texts into the active vector store without rewriting DB rows."""
        try:
            await self.initialize_vector_store()
            self.initialize_embedding_model()

            chunk_texts = [chunk["text"] for chunk in chunks]
            if not chunk_texts:
                return []

            embeddings = self.embedding_model.encode(chunk_texts)
            chunk_metadata = [
                {
                    "doc_id": doc_id,
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    **(metadata or {}),
                }
                for chunk in chunks
            ]
            chunk_ids = [f"{doc_id}:chunk:{chunk['chunk_index']}" for chunk in chunks]
            await self.vector_store.add_vectors(chunk_ids, embeddings, chunk_metadata)

            logger.info(f"Indexed {len(chunks)} existing chunks for document {doc_id}")
            return chunk_metadata
        except Exception as e:
            logger.error(f"Error indexing existing chunks for document {doc_id}: {str(e)}")
            raise

    async def retrieve(
        self,
        query: str,
        k: int = 5,
        similarity_threshold: float = 0.7,
        allowed_doc_ids: Optional[List[int]] = None,
    ) -> List[dict]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: User query string
            k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity score

        Returns:
            List of relevant chunks with metadata
        """
        try:
            # Initialize vector store if needed
            await self.initialize_vector_store()

            if not self.has_indexed_content():
                logger.info("Skipping retrieval because the vector store is empty")
                return []

            self.initialize_embedding_model()

            # Embed query
            query_embedding = self.embedding_model.encode_single(query)

            # Search vector store
            results = await self.vector_store.search(query_embedding, k=k)
            allowed_ids = (
                {str(doc_id) for doc_id in allowed_doc_ids}
                if allowed_doc_ids is not None
                else None
            )

            # Filter by similarity threshold and format results
            retrieved_chunks = []
            fallback_chunks = []
            for chunk_id, distance in results:
                # For L2 distance: lower is better
                # Convert to similarity score (0-1)
                similarity = 1 / (1 + distance)

                chunk_info = self.vector_store.metadata_store.get(chunk_id, {})
                if allowed_ids is not None and str(chunk_info.get("doc_id")) not in allowed_ids:
                    continue

                chunk_payload = {
                    "chunk_id": chunk_id,
                    "text": chunk_info.get("text", ""),
                    "doc_id": chunk_info.get("doc_id"),
                    "chunk_index": chunk_info.get("chunk_index"),
                    "similarity": float(similarity),
                    "metadata": chunk_info,
                }
                fallback_chunks.append(chunk_payload)

                if similarity >= similarity_threshold:
                    retrieved_chunks.append(chunk_payload)

            if not retrieved_chunks and fallback_chunks:
                logger.info(
                    "No chunks met the similarity threshold; returning top fallback matches instead"
                )
                retrieved_chunks = fallback_chunks[: min(len(fallback_chunks), max(1, k))]

            logger.info(f"Retrieved {len(retrieved_chunks)} chunks for query")
            return retrieved_chunks

        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}")
            return []


# Global retriever instance
rag_retriever = None


async def get_rag_retriever(force_init: bool = False) -> RAGRetriever:
    """Get or initialize global RAG retriever."""
    global rag_retriever

    if rag_retriever is None or force_init:
        rag_retriever = RAGRetriever()
        await rag_retriever.initialize_vector_store()

    return rag_retriever
