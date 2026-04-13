"""
Integration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import (
    GmailConnectionResponse,
    GmailOAuthStartResponse,
    GitHubConnectionResponse,
    GitHubOAuthStartResponse,
)
from app.services.github_service import GitHubOAuthError, GitHubService
from app.services.gmail_service import GmailAuthError, GmailOAuthError, GmailService
from app.utils.logger import logger

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/gmail", response_model=GmailConnectionResponse)
async def get_gmail_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get Gmail connection status for the current user."""
    user_id = int(current_user["user_id"])
    connection = await GmailService.get_connection(db, user_id)

    return GmailConnectionResponse(
        connected=bool(connection and connection.is_active),
        gmail_address=connection.gmail_address if connection and connection.is_active else None,
        last_synced_at=connection.last_synced_at if connection else None,
        imported_count=0,
    )


@router.get("/gmail/oauth/start", response_model=GmailOAuthStartResponse)
async def start_gmail_oauth(
    next_path: str = Query(default="/chat"),
    current_user: dict = Depends(get_current_user),
):
    """Create a Google OAuth URL for Gmail connection."""
    try:
        user_id = int(current_user["user_id"])
        auth_url = GmailService.build_oauth_authorization_url(user_id, next_path)
        return GmailOAuthStartResponse(auth_url=auth_url)
    except GmailOAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Error starting Gmail OAuth: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start Gmail OAuth",
        )


@router.get("/gmail/oauth/callback")
async def gmail_oauth_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Complete Google OAuth and redirect the user back to the frontend."""
    try:
        _, next_path = await GmailService.complete_oauth_callback(
            db,
            code,
            state,
            authorization_response=str(request.url),
        )
        return RedirectResponse(
            GmailService.build_frontend_callback_redirect(next_path, success=True)
        )
    except (GmailOAuthError, GmailAuthError) as exc:
        logger.warning(f"Gmail OAuth callback failed: {str(exc)}")
        return RedirectResponse(
            GmailService.build_frontend_callback_redirect(
                "/chat",
                success=False,
                message=str(exc),
            )
        )
    except Exception as exc:
        logger.error(f"Unexpected Gmail OAuth callback error: {str(exc)}")
        return RedirectResponse(
            GmailService.build_frontend_callback_redirect(
                "/chat",
                success=False,
                message="Failed to complete Gmail connection",
            )
        )


@router.post("/gmail/sync", response_model=GmailConnectionResponse)
async def sync_gmail(
    sync_limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync recent Gmail messages for the current user."""
    try:
        user_id = int(current_user["user_id"])
        connection = await GmailService.get_connection(db, user_id)
        if not connection or not connection.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gmail is not connected",
            )

        imported_count = await GmailService.sync_inbox(
            db,
            user_id=user_id,
            limit=max(1, min(sync_limit, 100)),
        )
        refreshed = await GmailService.get_connection(db, user_id)

        return GmailConnectionResponse(
            connected=True,
            gmail_address=refreshed.gmail_address,
            last_synced_at=refreshed.last_synced_at,
            imported_count=imported_count,
        )
    except GmailAuthError as exc:
        user_id = int(current_user["user_id"])
        await GmailService.mark_connection_inactive(db, user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error syncing Gmail: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync Gmail",
        )


@router.delete("/gmail", response_model=GmailConnectionResponse)
async def disconnect_gmail(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Gmail for the current user."""
    try:
        user_id = int(current_user["user_id"])
        await GmailService.disconnect(db, user_id)
        return GmailConnectionResponse(
            connected=False,
            gmail_address=None,
            last_synced_at=None,
            imported_count=0,
        )
    except Exception as exc:
        logger.error(f"Error disconnecting Gmail: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Gmail",
        )


@router.get("/github", response_model=GitHubConnectionResponse)
async def get_github_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get GitHub connection status for the current user."""
    user_id = int(current_user["user_id"])
    connection = await GitHubService.get_connection(db, user_id)

    return GitHubConnectionResponse(
        connected=bool(connection and connection.is_active),
        github_login=connection.github_login if connection and connection.is_active else None,
        last_synced_at=connection.last_synced_at if connection else None,
        imported_count=0,
    )


@router.get("/github/oauth/start", response_model=GitHubOAuthStartResponse)
async def start_github_oauth(
    next_path: str = Query(default="/chat"),
    current_user: dict = Depends(get_current_user),
):
    """Create a GitHub OAuth URL for GitHub connection."""
    try:
        user_id = int(current_user["user_id"])
        auth_url = GitHubService.build_oauth_authorization_url(user_id, next_path)
        return GitHubOAuthStartResponse(auth_url=auth_url)
    except GitHubOAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Error starting GitHub OAuth: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start GitHub OAuth",
        )


@router.get("/github/oauth/callback")
async def github_oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Complete GitHub OAuth and redirect the user back to the frontend."""
    try:
        _, next_path = await GitHubService.complete_oauth_callback(db, code, state)
        return RedirectResponse(
            GitHubService.build_frontend_callback_redirect(next_path, success=True)
        )
    except GitHubOAuthError as exc:
        logger.warning(f"GitHub OAuth callback failed: {str(exc)}")
        return RedirectResponse(
            GitHubService.build_frontend_callback_redirect(
                "/chat",
                success=False,
                message=str(exc),
            )
        )
    except Exception as exc:
        logger.error(f"Unexpected GitHub OAuth callback error: {str(exc)}")
        return RedirectResponse(
            GitHubService.build_frontend_callback_redirect(
                "/chat",
                success=False,
                message="Failed to complete GitHub connection",
            )
        )


@router.post("/github/sync", response_model=GitHubConnectionResponse)
async def sync_github(
    sync_limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync recent GitHub repositories for the current user."""
    try:
        user_id = int(current_user["user_id"])
        connection = await GitHubService.get_connection(db, user_id)
        if not connection or not connection.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub is not connected",
            )

        imported_count = await GitHubService.sync_repositories(
            db,
            user_id=user_id,
            limit=max(1, min(sync_limit, 20)),
        )
        refreshed = await GitHubService.get_connection(db, user_id)

        return GitHubConnectionResponse(
            connected=True,
            github_login=refreshed.github_login,
            last_synced_at=refreshed.last_synced_at,
            imported_count=imported_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error syncing GitHub: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync GitHub",
        )


@router.delete("/github", response_model=GitHubConnectionResponse)
async def disconnect_github(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect GitHub for the current user."""
    try:
        user_id = int(current_user["user_id"])
        await GitHubService.disconnect(db, user_id)
        return GitHubConnectionResponse(
            connected=False,
            github_login=None,
            last_synced_at=None,
            imported_count=0,
        )
    except Exception as exc:
        logger.error(f"Error disconnecting GitHub: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect GitHub",
        )
