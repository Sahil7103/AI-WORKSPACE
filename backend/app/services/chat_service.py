"""
Chat session management service.
"""

from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import re

from app.models import ChatSession, ChatMessage
from app.utils.cache import get_session_memory, set_session_memory
from app.utils.logger import logger


class ChatService:
    """Service for chat operations."""

    DEFAULT_SESSION_NAMES = {"new chat", "new"}

    @staticmethod
    def is_default_session_name(session_name: Optional[str]) -> bool:
        """Return whether the session title is still a placeholder."""
        if not session_name:
            return True
        normalized = session_name.strip().lower()
        return normalized in ChatService.DEFAULT_SESSION_NAMES

    @staticmethod
    def generate_session_name(prompt: str, max_words: int = 7, max_chars: int = 60) -> str:
        """Generate a concise chat title from the first prompt."""
        text = (prompt or "").strip()
        if not text:
            return "New Chat"

        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"^[\"'`]+|[\"'`]+$", "", text)
        text = re.sub(
            r"^(hi|hello|hey|please|can you|could you|would you|help me|i want to know|tell me about|explain|summarize)\s+",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = text.strip(" .,:;!?-")

        if not text:
            return "New Chat"

        words = text.split()
        if len(words) > max_words:
            text = " ".join(words[:max_words])

        text = text[:max_chars].rstrip(" ,:;.-")

        if not text:
            return "New Chat"

        return text[0].upper() + text[1:]

    @staticmethod
    async def create_session(
        db: AsyncSession, user_id: int, session_name: str = None
    ) -> ChatSession:
        """Create a new chat session."""
        try:
            session = ChatSession(
                user_id=user_id,
                session_name=session_name or "New Chat",
                updated_at=datetime.now(UTC).replace(tzinfo=None),
            )

            db.add(session)
            await db.commit()
            await db.refresh(session)

            logger.info(f"Chat session created: {session.id}")
            return session

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating chat session: {str(e)}")
            raise

    @staticmethod
    async def get_session(db: AsyncSession, session_id: int) -> Optional[ChatSession]:
        """Get session by ID."""
        return await db.get(ChatSession, session_id)

    @staticmethod
    async def list_sessions(
        db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple:
        """List user's chat sessions."""
        try:
            stmt = select(ChatSession).where(ChatSession.user_id == user_id)

            # Count total
            count_result = await db.execute(stmt)
            total = len(count_result.scalars().all())

            # Get paginated, ordered by most recent first
            stmt = (
                select(ChatSession)
                .where(ChatSession.user_id == user_id)
                .order_by(func.coalesce(ChatSession.updated_at, ChatSession.created_at).desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            sessions = result.scalars().all()

            return sessions, total

        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return [], 0

    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: int,
        role: str,
        content: str,
        sources: str = None,
    ) -> ChatMessage:
        """Add a message to a session."""
        try:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                sources=sources,
            )

            db.add(message)

            # Update session timestamp
            session = await ChatService.get_session(db, session_id)
            if session:
                session.updated_at = __import__("datetime").datetime.utcnow()

            await db.commit()
            await db.refresh(message)

            logger.info(f"Message added to session {session_id}")
            return message

        except Exception as e:
            await db.rollback()
            logger.error(f"Error adding message: {str(e)}")
            raise

    @staticmethod
    async def get_session_messages(
        db: AsyncSession, session_id: int
    ) -> List[ChatMessage]:
        """Get all messages in a session."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_session_memory_context(session_id: int) -> list:
        """Get conversation memory from Redis for context."""
        return await get_session_memory(session_id)

    @staticmethod
    async def update_session_memory(session_id: int, messages: list):
        """Update session memory in Redis."""
        await set_session_memory(session_id, messages)

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: int):
        """Delete a session and its messages."""
        try:
            session = await ChatService.get_session(db, session_id)
            if session:
                await db.delete(session)
                await db.commit()
                logger.info(f"Chat session {session_id} deleted")

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting session: {str(e)}")
            raise

    @staticmethod
    async def rename_session(
        db: AsyncSession,
        session_id: int,
        session_name: str,
    ) -> ChatSession:
        """Rename a session."""
        try:
            session = await ChatService.get_session(db, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            session.session_name = (session_name or "").strip() or "New Chat"
            session.updated_at = datetime.now(UTC).replace(tzinfo=None)

            await db.commit()
            await db.refresh(session)
            logger.info(f"Chat session renamed: {session.id}")
            return session
        except Exception as e:
            await db.rollback()
            logger.error(f"Error renaming chat session: {str(e)}")
            raise
