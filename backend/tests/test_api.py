"""
Basic tests for the application.
"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import User
from app.services.user_service import UserService
from app.schemas import UserCreate
from app.core.security import hash_password, verify_password


# Test database setup
@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        yield session


# Tests
@pytest.mark.asyncio
async def test_password_hashing():
    """Test password hashing."""
    password = "test_password_123"

    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


@pytest.mark.asyncio
async def test_user_creation(test_db):
    """Test user creation."""
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="secure_password",
        full_name="Test User",
    )

    user = await UserService.create_user(test_db, user_data)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password != "secure_password"
    assert user.role == "employee"


@pytest.mark.asyncio
async def test_user_authentication(test_db):
    """Test user authentication."""
    # Create user
    user_data = UserCreate(
        username="authtest",
        email="auth@example.com",
        password="password123",
    )
    await UserService.create_user(test_db, user_data)

    # Test authentication
    user = await UserService.authenticate_user(test_db, "authtest", "password123")
    assert user is not None
    assert user.username == "authtest"

    # Test wrong password
    user = await UserService.authenticate_user(test_db, "authtest", "wrongpass")
    assert user is None


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
