"""
Rate limiting middleware for API security.
"""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.utils.logger import logger


class RedisRateLimiter:
    """Redis-based rate limiter for API endpoints."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique identifier (user_id, IP, etc.)
            limit: Max requests per window
            window: Time window in seconds
            
        Returns:
            (allowed, info_dict) where info contains remaining requests
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Clean old entries and count current requests
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.expire(key, window)
            results = await pipe.execute()
            
            current_requests = results[1]
            remaining = max(0, limit - current_requests)
            
            if current_requests >= limit:
                return False, {
                    "remaining": 0,
                    "reset_time": current_time + window,
                    "limit": limit,
                    "window": window
                }
            
            # Add current request
            await self.redis.zadd(key, {str(current_time): current_time})
            return True, {
                "remaining": remaining - 1,
                "reset_time": current_time + window,
                "limit": limit,
                "window": window
            }
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open - allow request if Redis fails
            return True, {"remaining": limit}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.limiter = RedisRateLimiter(redis_client)
        self.rate_limits = {
            # endpoint: (requests_per_minute, requests_per_hour)
            "/auth/login": (5, 50),
            "/auth/register": (3, 20),
            "/chat/query": (30, 500),
            "/chat/query-stream": (30, 500),
            "/documents/upload": (10, 100),
            "/integrations/gmail/sync": (5, 50),
            "default": (60, 1000)
        }
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_id = await self._get_client_id(request)
        
        # Get rate limit for this endpoint
        path = request.url.path
        rate_limit = self.rate_limits.get(path, self.rate_limits["default"])
        per_minute, per_hour = rate_limit
        
        # Check minute limit
        minute_key = f"rate_limit:minute:{client_id}:{path}"
        minute_allowed, minute_info = await self.limiter.is_allowed(
            minute_key, per_minute, 60
        )
        
        # Check hour limit
        hour_key = f"rate_limit:hour:{client_id}:{path}"
        hour_allowed, hour_info = await self.limiter.is_allowed(
            hour_key, per_hour, 3600
        )
        
        if not minute_allowed or not hour_allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path}",
                extra={
                    "client_id": client_id,
                    "path": path,
                    "minute_remaining": minute_info.get("remaining", 0),
                    "hour_remaining": hour_info.get("remaining", 0)
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "minute_limit": per_minute,
                    "hour_limit": per_hour,
                    "minute_remaining": minute_info.get("remaining", 0),
                    "hour_remaining": hour_info.get("remaining", 0),
                    "reset_time": max(
                        minute_info.get("reset_time", 0),
                        hour_info.get("reset_time", 0)
                    )
                },
                headers={
                    "X-RateLimit-Limit-Minute": str(per_minute),
                    "X-RateLimit-Remaining-Minute": str(minute_info.get("remaining", 0)),
                    "X-RateLimit-Limit-Hour": str(per_hour),
                    "X-RateLimit-Remaining-Hour": str(hour_info.get("remaining", 0)),
                    "Retry-After": str(max(
                        minute_info.get("reset_time", 0) - int(time.time()),
                        hour_info.get("reset_time", 0) - int(time.time())
                    ))
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit-Minute"] = str(per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(minute_info.get("remaining", 0))
        response.headers["X-RateLimit-Limit-Hour"] = str(per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(hour_info.get("remaining", 0))
        
        return response
    
    async def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try to get user ID from JWT token first
        try:
            authorization = request.headers.get("authorization")
            if authorization and authorization.startswith("Bearer "):
                # For now, use a simple approach - in production, decode JWT
                return f"user:{hash(authorization)}"
        except:
            pass
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        return f"ip:{request.client.host if request.client else 'unknown'}"


# Dependency for getting rate limiter in routes
async def get_rate_limiter():
    """Dependency to get rate limiter instance."""
    try:
        redis_client = redis.from_url(settings.redis_url)
        return RedisRateLimiter(redis_client)
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}")
        # Return a dummy limiter that always allows
        class DummyLimiter:
            async def is_allowed(self, key, limit, window=60):
                return True, {"remaining": limit}
        return DummyLimiter()
