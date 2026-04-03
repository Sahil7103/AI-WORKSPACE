"""
Pydantic schemas for request and response validation.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ==================== User Schemas ====================


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Authentication Schemas ====================


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ==================== Document Schemas ====================


class DocumentChunkResponse(BaseModel):
    id: int
    chunk_text: str
    chunk_index: int
    document_id: int

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    filename: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    file_type: str
    size_bytes: int
    is_processed: bool
    embedding_generated: bool
    created_at: datetime
    uploaded_by_id: int

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    content: Optional[str] = None
    chunks: List[DocumentChunkResponse] = []


# ==================== Chat Schemas ====================


class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: int
    sources: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    session_name: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: int
    session_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []


class QueryRequest(BaseModel):
    """Chat query request."""

    session_id: int
    query: str
    document_ids: Optional[List[int]] = None  # Optional: limit to specific documents


class QueryResponse(BaseModel):
    """Chat query response."""

    message_id: int
    session_id: int
    session_name: Optional[str] = None
    query: str
    response: str
    sources: List[dict]
    response_time_ms: float
    streaming: bool = False


class QueryStreamChunk(BaseModel):
    """Streamed response chunk."""

    token: str
    done: bool = False


# ==================== Admin Schemas ====================


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]


class DocumentStatsResponse(BaseModel):
    total_documents: int
    total_processed: int
    total_with_embeddings: int
    total_chunks: int


# ==================== Evaluation Schemas ====================


class EvaluationMetricResponse(BaseModel):
    id: int
    message_id: int
    response_time_ms: float
    retrieval_accuracy_score: Optional[float] = None
    hallucination_detected: bool
    user_satisfaction_score: Optional[float] = None

    class Config:
        from_attributes = True


# ==================== Streaming Response Schemas ====================


class StreamingResponse(BaseModel):
    """For streaming responses."""

    content: str
    is_complete: bool = False
