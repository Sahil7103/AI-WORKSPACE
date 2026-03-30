"""
Application configuration management.
Uses Pydantic Settings for environment variable handling.
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/ai_workplace_copilot"
    sqlalchemy_db_url: str = "postgresql://user:password@localhost:5432/ai_workplace_copilot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"

    # Vector Database
    use_faiss: bool = True
    pinecone_api_key: str = ""
    pinecone_index_name: str = "ai-copilot"

    # Slack Integration
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    # Gmail Integration
    google_credentials_json: str = "{}"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Application Info
    app_name: str = "AI Workplace Copilot"
    app_version: str = "1.0.0"
    environment: str = "development"

    # Document Processing
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_file_size_mb: int = 50

    # RAG Configuration
    max_retrieved_documents: int = 5
    similarity_threshold: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
