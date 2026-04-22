"""
Main FastAPI application.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.utils.cache import cache
from app.utils.logger import logger
from app.api import auth, documents, chat, admin, agents, integrations, health
from app.core.security_headers import configure_production_middleware


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    keepalive_task = None
    warmup_task = None

    async def llm_keepalive_loop():
        """Keep the configured external LLM endpoint warm between requests."""
        while True:
            await asyncio.sleep(max(30, settings.llm_keepalive_interval_seconds))
            try:
                await chat.query_service.llm.keepalive_once()
            except Exception as exc:
                logger.warning(f"LLM keepalive loop error: {str(exc)}")

    # Startup
    logger.info("Starting up application")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug: {settings.debug}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize Redis
    cache_ready = await cache.connect()
    if cache_ready:
        logger.info("Redis connected")
    else:
        logger.info("Redis cache disabled")

    warmup_task = asyncio.create_task(chat.query_service.warmup_dependencies())

    if settings.llm_keepalive_enabled:
        keepalive_task = asyncio.create_task(llm_keepalive_loop())
        logger.info(
            f"LLM keepalive enabled with interval {settings.llm_keepalive_interval_seconds}s"
        )

    yield

    # Shutdown
    logger.info("Shutting down application")
    if warmup_task:
        warmup_task.cancel()
    if keepalive_task:
        keepalive_task.cancel()
    await chat.query_service.llm.close()
    await cache.disconnect()
    logger.info("Redis disconnected")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Workplace Copilot - Enterprise GenAI SaaS",
    lifespan=lifespan,
)

# Configure production middleware (includes CORS, security headers, rate limiting)
configure_production_middleware(app)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(agents.router)
app.include_router(integrations.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
        "docs": "/docs",
        "redoc": "/redoc",
    }




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
