"""
GitHub integration service using OAuth.
"""

from base64 import b64decode
from datetime import datetime, UTC, timedelta
import json
from typing import Optional
from urllib.parse import quote

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Document, GitHubConnection
from app.services.document_service import DocumentService
from app.utils.logger import logger


class GitHubOAuthError(ValueError):
    """Raised when GitHub OAuth cannot be completed."""


class GitHubService:
    """Service for connecting to GitHub and importing repo knowledge."""

    GITHUB_OAUTH_SCOPES = ["read:user", "repo"]

    @staticmethod
    async def get_connection(db: AsyncSession, user_id: int) -> Optional[GitHubConnection]:
        stmt = select(GitHubConnection).where(GitHubConnection.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def _encode_state(user_id: int, next_path: str) -> str:
        payload = {
            "sub": str(user_id),
            "next_path": next_path or "/chat",
            "purpose": "github_oauth",
            "exp": datetime.utcnow() + timedelta(minutes=15),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def _decode_state(state: str) -> dict:
        try:
            payload = jwt.decode(
                state,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
        except JWTError as exc:
            raise GitHubOAuthError("Invalid GitHub OAuth state") from exc

        if payload.get("purpose") != "github_oauth":
            raise GitHubOAuthError("Invalid GitHub OAuth state")

        return payload

    @staticmethod
    def build_oauth_authorization_url(user_id: int, next_path: str = "/chat") -> str:
        if not settings.github_client_id or not settings.github_client_secret:
            raise GitHubOAuthError(
                "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET."
            )

        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_oauth_redirect_uri,
            "scope": " ".join(GitHubService.GITHUB_OAUTH_SCOPES),
            "state": GitHubService._encode_state(user_id, next_path),
        }
        query = "&".join(f"{key}={quote(str(value))}" for key, value in params.items())
        return f"https://github.com/login/oauth/authorize?{query}"

    @staticmethod
    async def upsert_connection(
        db: AsyncSession,
        user_id: int,
        github_login: str,
        access_token: str,
    ) -> GitHubConnection:
        connection = await GitHubService.get_connection(db, user_id)
        if connection is None:
            connection = GitHubConnection(
                user_id=user_id,
                github_login=github_login.strip(),
                access_token=access_token.strip(),
                is_active=True,
            )
            db.add(connection)
        else:
            connection.github_login = github_login.strip()
            connection.access_token = access_token.strip()
            connection.is_active = True

        await db.commit()
        await db.refresh(connection)
        return connection

    @staticmethod
    async def disconnect(db: AsyncSession, user_id: int) -> None:
        connection = await GitHubService.get_connection(db, user_id)
        if connection:
            connection.is_active = False
            await db.commit()

    @staticmethod
    async def complete_oauth_callback(
        db: AsyncSession,
        code: str,
        state: str,
    ) -> tuple[GitHubConnection, str]:
        payload = GitHubService._decode_state(state)
        user_id = int(payload["sub"])
        next_path = payload.get("next_path") or "/chat"

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": settings.github_oauth_redirect_uri,
                    "state": state,
                },
            )
            token_response.raise_for_status()
            token_payload = token_response.json()
            access_token = token_payload.get("access_token")
            if not access_token:
                raise GitHubOAuthError(
                    token_payload.get("error_description")
                    or token_payload.get("error")
                    or "GitHub did not return an access token"
                )

            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            user_response.raise_for_status()
            user_payload = user_response.json()

        github_login = user_payload.get("login")
        if not github_login:
            raise GitHubOAuthError("Unable to determine the connected GitHub account")

        connection = await GitHubService.upsert_connection(
            db,
            user_id=user_id,
            github_login=github_login,
            access_token=access_token,
        )
        imported_count = await GitHubService.sync_repositories(db, user_id, limit=10)
        logger.info(f"GitHub OAuth connected for user {user_id}; imported {imported_count} repos")
        return connection, next_path

    @staticmethod
    async def sync_repositories(db: AsyncSession, user_id: int, limit: int = 10) -> int:
        connection = await GitHubService.get_connection(db, user_id)
        if not connection or not connection.is_active:
            raise ValueError("GitHub is not connected for this user")

        async with httpx.AsyncClient(timeout=60.0) as client:
            repo_response = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {connection.access_token}",
                    "Accept": "application/vnd.github+json",
                },
                params={"sort": "updated", "per_page": max(1, min(limit, 20))},
            )
            repo_response.raise_for_status()
            repos = repo_response.json()

            imported_count = 0
            for repo in repos:
                repo_full_name = repo.get("full_name")
                if not repo_full_name:
                    continue

                readme_text = ""
                try:
                    readme_response = await client.get(
                        f"https://api.github.com/repos/{repo_full_name}/readme",
                        headers={
                            "Authorization": f"Bearer {connection.access_token}",
                            "Accept": "application/vnd.github+json",
                        },
                    )
                    if readme_response.status_code == 200:
                        readme_payload = readme_response.json()
                        content = readme_payload.get("content", "")
                        if content:
                            readme_text = b64decode(content).decode("utf-8", errors="replace")
                except Exception:
                    readme_text = ""

                repo_summary = {
                    "name": repo.get("name"),
                    "full_name": repo_full_name,
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "default_branch": repo.get("default_branch"),
                    "private": repo.get("private"),
                    "html_url": repo.get("html_url"),
                    "updated_at": repo.get("updated_at"),
                }
                content = (
                    f"Repository: {repo_full_name}\n"
                    f"Description: {repo.get('description') or 'No description'}\n"
                    f"Language: {repo.get('language') or 'Unknown'}\n"
                    f"Default branch: {repo.get('default_branch') or 'main'}\n"
                    f"Private: {'Yes' if repo.get('private') else 'No'}\n"
                    f"URL: {repo.get('html_url') or ''}\n"
                    f"Updated at: {repo.get('updated_at') or ''}\n\n"
                    f"README:\n{readme_text or 'README not available.'}"
                ).strip()

                file_path = f"github://{connection.github_login}/{repo_full_name}"
                existing_stmt = select(Document).where(
                    Document.uploaded_by_id == user_id,
                    Document.file_path == file_path,
                )
                existing_result = await db.execute(existing_stmt)
                existing_document = existing_result.scalars().first()

                if existing_document:
                    existing_document.filename = f"GitHub - {repo_full_name}"
                    existing_document.content = content
                    existing_document.file_type = "github"
                    existing_document.size_bytes = len(content.encode("utf-8"))
                    existing_document.is_processed = False
                    existing_document.embedding_generated = False
                    await db.commit()
                    await DocumentService.process_document(db, existing_document.id, content)
                else:
                    document = await DocumentService.create_document(
                        db,
                        filename=f"GitHub - {repo_full_name}",
                        file_path=file_path,
                        file_type="github",
                        size_bytes=len(content.encode("utf-8")),
                        uploaded_by_id=user_id,
                        content=content,
                    )
                    await DocumentService.process_document(db, document.id, content)
                    imported_count += 1

            connection.last_synced_at = datetime.now(UTC).replace(tzinfo=None)
            await db.commit()
            return imported_count

    @staticmethod
    def build_frontend_callback_redirect(next_path: str, success: bool, message: str = "") -> str:
        cleaned_path = next_path if next_path.startswith("/") else f"/{next_path}"
        status_value = "connected" if success else "error"
        suffix = f"?github={status_value}"
        if message:
            suffix += f"&github_message={quote(message)}"
        return f"{settings.frontend_url.rstrip('/')}{cleaned_path}{suffix}"
