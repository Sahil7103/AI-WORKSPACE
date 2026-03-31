"""
User management service.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.schemas import UserCreate
from app.core.security import hash_password, verify_password
from app.utils.logger import logger


class UserService:
    """Service for user operations."""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Check for conflicting username or email before insert.
            stmt = select(User).where(
                or_(User.email == user_data.email, User.username == user_data.username)
            )
            existing = await db.execute(stmt)
            existing_user = existing.scalar_one_or_none()
            if existing_user:
                if existing_user.email == user_data.email:
                    raise ValueError(f"User with email {user_data.email} already exists")
                raise ValueError(f"Username {user_data.username} is already taken")

            # Hash password
            hashed_pwd = hash_password(user_data.password)

            # Create user
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_pwd,
                full_name=user_data.full_name,
                role="employee",  # Default role
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"User created: {user.email}")
            return user

        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error creating user: {str(e)}")
            raise ValueError("Username or email is already in use") from e
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> User:
        """Get user by username."""
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
        """Authenticate user with username and password."""
        user = await UserService.get_user_by_username(db, username)

        if not user or not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        """Get user by ID."""
        return await db.get(User, user_id)

    @staticmethod
    async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> tuple:
        """List all users with pagination."""
        # Get total count
        count_stmt = select(User)
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        # Get paginated results
        stmt = select(User).offset(skip).limit(limit)
        result = await db.execute(stmt)
        users = result.scalars().all()

        return users, total

    @staticmethod
    async def update_user_role(db: AsyncSession, user_id: int, role: str) -> User:
        """Update user role."""
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            user.role = role
            await db.commit()
            await db.refresh(user)

            logger.info(f"User {user_id} role updated to {role}")
            return user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user role: {str(e)}")
            raise
