"""
Document management service.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models import Document, DocumentChunk
from app.schemas import DocumentCreate
from app.rag.retriever import get_rag_retriever
from app.utils.logger import logger


class DocumentService:
    """Service for document operations."""

    @staticmethod
    async def create_document(
        db: AsyncSession,
        filename: str,
        file_path: str,
        file_type: str,
        size_bytes: int,
        uploaded_by_id: int,
        content: str = None,
    ) -> Document:
        """Create a document record."""
        try:
            doc = Document(
                filename=filename,
                file_path=file_path,
                file_type=file_type,
                size_bytes=size_bytes,
                uploaded_by_id=uploaded_by_id,
                content=content,
                is_processed=False,
                embedding_generated=False,
            )

            db.add(doc)
            await db.commit()
            await db.refresh(doc)

            logger.info(f"Document created: {filename} (ID: {doc.id})")
            return doc

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise

    @staticmethod
    async def get_document(db: AsyncSession, doc_id: int) -> Optional[Document]:
        """Get document by ID."""
        return await db.get(Document, doc_id)

    @staticmethod
    async def list_documents(
        db: AsyncSession, user_id: int = None, skip: int = 0, limit: int = 100
    ) -> tuple:
        """List documents with pagination."""
        try:
            # Build query
            stmt = select(Document)
            if user_id:
                stmt = stmt.where(Document.uploaded_by_id == user_id)

            # Count total
            count_result = await db.execute(stmt)
            total = len(count_result.scalars().all())

            # Get paginated results
            stmt = stmt.offset(skip).limit(limit)
            result = await db.execute(stmt)
            documents = result.scalars().all()

            return documents, total

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return [], 0

    @staticmethod
    async def process_document(db: AsyncSession, doc_id: int, content: str) -> Document:
        """
        Process document: chunk, embed, and store chunks.
        """
        try:
            doc = await DocumentService.get_document(db, doc_id)
            if not doc:
                raise ValueError(f"Document {doc_id} not found")

            # Get RAG retriever
            retriever = await get_rag_retriever()

            # Process document through RAG pipeline
            chunk_metadata = await retriever.process_document(
                doc_id=str(doc_id),
                content=content,
                metadata={"filename": doc.filename, "file_type": doc.file_type},
            )

            # Store chunks in database
            for chunk_info in chunk_metadata:
                chunk = DocumentChunk(
                    document_id=doc_id,
                    chunk_text=chunk_info["text"],
                    chunk_index=chunk_info["chunk_index"],
                )
                db.add(chunk)

            # Mark document as processed
            doc.is_processed = True
            doc.embedding_generated = True
            doc.content = content

            await db.commit()

            logger.info(
                f"Processed document {doc_id} with {len(chunk_metadata)} chunks"
            )
            return doc

        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing document: {str(e)}")
            raise

    @staticmethod
    async def delete_document(db: AsyncSession, doc_id: int):
        """Delete document and its chunks."""
        try:
            doc = await DocumentService.get_document(db, doc_id)
            if doc:
                await db.delete(doc)
                await db.commit()
                logger.info(f"Document {doc_id} deleted")

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting document: {str(e)}")
            raise

    @staticmethod
    async def get_document_chunks(db: AsyncSession, doc_id: int) -> List[DocumentChunk]:
        """Get all chunks for a document."""
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc_id)
        result = await db.execute(stmt)
        return result.scalars().all()
