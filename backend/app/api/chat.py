"""
Chat endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import (
    QueryRequest,
    QueryResponse,
    ChatSessionResponse,
    ChatSessionDetailResponse,
    ChatMessageResponse,
)
from app.services.chat_service import ChatService
from app.services.llm_service import QueryService, LLMService
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
query_service = QueryService(LLMService())


def _serialize_chat_session(session, messages=None) -> ChatSessionDetailResponse:
    """Convert ORM session objects into plain response models."""
    serialized_messages = [
        ChatMessageResponse.model_validate(message, from_attributes=True)
        for message in (messages or [])
    ]

    return ChatSessionDetailResponse(
        id=session.id,
        session_name=session.session_name,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=serialized_messages,
    )


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_name: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    try:
        user_id = int(current_user["user_id"])
        session = await ChatService.create_session(db, user_id, session_name)
        return session

    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating chat session",
        )


@router.get("/sessions", response_model=dict)
async def list_chat_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's chat sessions."""
    try:
        user_id = int(current_user["user_id"])
        sessions, total = await ChatService.list_sessions(
            db, user_id, skip=skip, limit=limit
        )

        return {
            "total": total,
            "sessions": sessions,
        }

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing sessions",
        )


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_chat_session(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat session with messages."""
    try:
        session = await ChatService.get_session(db, session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Check access
        user_id = int(current_user["user_id"])
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Get messages
        messages = await ChatService.get_session_messages(db, session_id)
        return _serialize_chat_session(session, messages)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching session",
        )


@router.post("/query", response_model=QueryResponse)
async def query_chat(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a query and get response."""
    try:
        user_id = int(current_user["user_id"])

        # Verify session access
        session = await ChatService.get_session(db, request.session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session not found or access denied",
            )

        # Get conversation history
        messages = await ChatService.get_session_messages(db, request.session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[-4:]  # Last 4 messages for context
        ]

        # Process query
        result = await query_service.process_query(
            query=request.query,
            user_id=user_id,
            session_id=request.session_id,
            document_ids=request.document_ids,
            conversation_history=conversation_history,
        )

        # Save query message
        await ChatService.add_message(db, request.session_id, "user", request.query)

        # Save response message with sources
        sources_json = json.dumps(result["sources"])
        response_msg = await ChatService.add_message(
            db, request.session_id, "assistant", result["response"], sources_json
        )

        return QueryResponse(
            message_id=response_msg.id,
            session_id=request.session_id,
            query=request.query,
            response=result["response"],
            sources=result["sources"],
            response_time_ms=result["response_time_ms"],
            streaming=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing query",
        )


@router.post("/query-stream")
async def query_stream(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a query response."""
    try:
        user_id = int(current_user["user_id"])

        # Verify session access
        session = await ChatService.get_session(db, request.session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session not found or access denied",
            )

        # Get conversation history
        messages = await ChatService.get_session_messages(db, request.session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content} for msg in messages[-4:]
        ]

        # Stream response
        async def generate():
            """Generate streaming response."""
            async for token in query_service.process_query_streaming(
                query=request.query,
                user_id=user_id,
                session_id=request.session_id,
                document_ids=request.document_ids,
                conversation_history=conversation_history,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Save messages when streaming completes
            await ChatService.add_message(db, request.session_id, "user", request.query)
            # Note: Real response would be reconstructed from stream
            await ChatService.add_message(
                db, request.session_id, "assistant", "[Streaming complete]"
            )

        return StreamingResponse(generate(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in streaming query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing streaming query",
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session."""
    try:
        session = await ChatService.get_session(db, session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Check access
        user_id = int(current_user["user_id"])
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        await ChatService.delete_session(db, session_id)

        return {"message": "Session deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting session",
        )
