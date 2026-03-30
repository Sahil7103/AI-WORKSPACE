"""
Redis cache management.
"""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


class RedisCache:
    """Redis cache helper."""

    def __init__(self):
        self.redis_url = settings.redis_url
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        self.client = await redis.from_url(self.redis_url)

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.client:
            return None

        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, expire: int = 3600):
        """Set value in cache."""
        if not self.client:
            return

        await self.client.setex(key, expire, json.dumps(value))

    async def delete(self, key: str):
        """Delete key from cache."""
        if not self.client:
            return

        await self.client.delete(key)

    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern."""
        if not self.client:
            return

        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)


# Global cache instance
cache = RedisCache()


async def get_session_memory(session_id: int) -> list:
    """Get chat session memory from Redis."""
    memory = await cache.get(f"session:{session_id}")
    return memory or []


async def set_session_memory(session_id: int, messages: list):
    """Store chat session memory in Redis."""
    await cache.set(f"session:{session_id}", messages, expire=86400)  # 24 hours
