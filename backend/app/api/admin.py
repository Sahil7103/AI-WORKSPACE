"""
Admin and management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.schemas import UserListResponse, UserResponse, DocumentStatsResponse
from app.services.user_service import UserService
from app.services.document_service import DocumentService
from app.utils.logger import logger

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    try:
        users, total = await UserService.list_users(db, skip=skip, limit=limit)

        return UserListResponse(total=total, users=users)

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing users",
        )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user role (admin only)."""
    try:
        if role not in ["admin", "employee"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )

        user = await UserService.update_user_role(db, user_id, role)
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user role",
        )


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_admin_stats(
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get system statistics (admin only)."""
    try:
        documents, total = await DocumentService.list_documents(db, skip=0, limit=10000)

        total_processed = sum(1 for d in documents if d.is_processed)
        total_with_embeddings = sum(1 for d in documents if d.embedding_generated)

        total_chunks = 0
        for doc in documents:
            chunks = await DocumentService.get_document_chunks(db, doc.id)
            total_chunks += len(chunks)

        return DocumentStatsResponse(
            total_documents=total,
            total_processed=total_processed,
            total_with_embeddings=total_with_embeddings,
            total_chunks=total_chunks,
        )

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting statistics",
        )


@router.post("/cache/clear")
async def clear_cache(
    current_user: dict = Depends(get_current_admin_user),
):
    """Clear Redis cache (admin only)."""
    try:
        from app.utils.cache import cache

        await cache.clear_pattern("*")

        return {"message": "Cache cleared"}

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing cache",
        )
