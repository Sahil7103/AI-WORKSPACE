"""
Document management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import DocumentResponse, DocumentDetailResponse
from app.services.document_service import DocumentService
from app.utils.logger import logger
from app.utils.file_handler import save_uploaded_file, read_file_content

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document."""
    try:
        user_id = int(current_user["user_id"])

        # Save file
        file_path = await save_uploaded_file(file.filename, file.file)

        # Get file type
        file_type = file.filename.split(".")[-1].lower()

        # Read file content
        content = await read_file_content(file_path)

        # Create document record
        document = await DocumentService.create_document(
            db,
            filename=file.filename,
            file_path=file_path,
            file_type=file_type,
            size_bytes=len(content.encode()),
            uploaded_by_id=user_id,
            content=content,
        )

        # Process document asynchronously (in production, use Celery/tasks)
        try:
            await DocumentService.process_document(db, document.id, content)
        except Exception as e:
            logger.warning(f"Error processing document: {str(e)}")
            # Don't fail upload if processing fails

        return document

    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading document",
        )


@router.get("/", response_model=dict)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's documents."""
    try:
        user_id = int(current_user["user_id"])
        documents, total = await DocumentService.list_documents(
            db, user_id=user_id, skip=skip, limit=limit
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "documents": documents,
        }

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing documents",
        )


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(
    doc_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details."""
    try:
        document = await DocumentService.get_document(db, doc_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Check access
        user_id = int(current_user["user_id"])
        if (
            document.uploaded_by_id != user_id
            and current_user["payload"].get("role") != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Get chunks
        chunks = await DocumentService.get_document_chunks(db, doc_id)
        document.chunks = chunks

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching document",
        )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    try:
        document = await DocumentService.get_document(db, doc_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Check access
        user_id = int(current_user["user_id"])
        if (
            document.uploaded_by_id != user_id
            and current_user["payload"].get("role") != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        await DocumentService.delete_document(db, doc_id)

        return {"message": "Document deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting document",
        )
