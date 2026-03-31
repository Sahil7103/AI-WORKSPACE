"""
Application configuration management.
Uses Pydantic Settings for environment variable handling.
"""

import json
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./ai_workplace_copilot.db"
    sqlalchemy_db_url: Optional[str] = None

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

    # External LLM Endpoint
    llm_api_url: str = "https://sk1354-llama3-career-api.hf.space/chat"
    llm_api_token: str = ""
    llm_model_label: str = "sk1354/llama3-career-api"
    llm_timeout_seconds: float = 60.0
    llm_max_tokens: int = 1000

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
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    # Application Info
    app_name: str = "AI Workplace Copilot"
    app_version: str = "1.0.0"
    environment: str = "development"

    # Document Processing
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_file_size_mb: int = 50
    process_documents_on_upload: bool = False

    # RAG Configuration
    max_retrieved_documents: int = 5
    similarity_threshold: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = False

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Accept common environment labels such as release/production."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"debug", "dev", "development"}:
                return True
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """Accept JSON lists or comma-separated CORS origin strings."""
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return []

            if normalized.startswith("["):
                try:
                    parsed = json.loads(normalized)
                    if isinstance(parsed, list):
                        return [str(item).strip().rstrip("/") for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass

            return [
                item.strip().rstrip("/")
                for item in normalized.split(",")
                if item.strip()
            ]

        if isinstance(value, list):
            return [str(item).strip().rstrip("/") for item in value if str(item).strip()]

        return value


settings = Settings()
