"""
Security headers and CORS configuration for production hardening.
"""

from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust based on needs
            "style-src 'self' 'unsafe-inline'",  # For Tailwind CSS
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' https://api.openai.com https://gmail.googleapis.com",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "upgrade-insecure-requests"
        ]
        
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        # HSTS (only in HTTPS)
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Remove server information
        response.headers["Server"] = "AI-Copilot"
        response.headers["X-Powered-By"] = "AI-Copilot"
        
        return response


def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS with production-ready settings.
    """
    # Parse allowed origins from settings
    allowed_origins = []
    if settings.cors_origins:
        allowed_origins = settings.cors_origins
    
    # Add common development origins if in debug mode
    if settings.debug:
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]
        for origin in dev_origins:
            if origin not in allowed_origins:
                allowed_origins.append(origin)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
            "PATCH"
        ],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "X-Client-Version",
            "X-Request-ID"
        ],
        expose_headers=[
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Limit-Hour",
            "X-RateLimit-Remaining-Hour",
            "Retry-After",
            "X-Request-ID",
            "X-Response-Time"
        ],
        max_age=86400,  # 24 hours
    )


def configure_security_middleware(app: FastAPI) -> None:
    """
    Configure all security middleware for production.
    """
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add rate limiting middleware (if Redis is available)
    try:
        import redis.asyncio as redis
        from app.core.rate_limiter import RateLimitMiddleware
        
        redis_client = redis.from_url(settings.redis_url)
        app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
        
    except ImportError:
        # Redis not available - skip rate limiting
        pass
    except Exception as e:
        # Redis connection failed - log but continue
        import logging
        logging.warning(f"Failed to initialize rate limiting: {e}")
    
    # Add error tracking middleware
    try:
        from app.core.error_tracking import ErrorTrackingMiddleware, get_error_tracker
        app.add_middleware(ErrorTrackingMiddleware, error_tracker=get_error_tracker())
    except Exception as e:
        import logging
        logging.warning(f"Failed to initialize error tracking: {e}")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request IDs for tracing."""
    
    async def dispatch(self, request, call_next):
        import uuid
        
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


def configure_production_middleware(app: FastAPI) -> None:
    """
    Configure all production middleware in the correct order.
    """
    # Order matters: RequestID -> RateLimit -> Security -> CORS
    app.add_middleware(RequestIDMiddleware)
    configure_security_middleware(app)
    configure_cors(app)
