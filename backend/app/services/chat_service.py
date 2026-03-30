"""
Chat session management service.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models import ChatSession, ChatMessage
from app.utils.cache import get_session_memory, set_session_memory
from app.utils.logger import logger


class ChatService:
    """Service for chat operations."""

    @staticmethod
    async def create_session(
        db: AsyncSession, user_id: int, session_name: str = None
    ) -> ChatSession:
        """Create a new chat session."""
        try:
            session = ChatSession(
                user_id=user_id,
                session_name=session_name or "New Chat",
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
                .order_by(ChatSession.updated_at.desc())
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
