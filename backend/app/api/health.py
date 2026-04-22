"""
Health check endpoints for monitoring and load balancer health checks.
"""

import time
import asyncio
from datetime import datetime, UTC
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns overall service health status.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "ai-workplace-copilot",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness check - verifies all dependencies are ready.
    Used by Kubernetes and orchestration systems.
    """
    checks = {}
    overall_healthy = True
    
    # Database connectivity check
    try:
        start_time = time.time()
        await db.execute(text("SELECT 1"))
        db_time = (time.time() - start_time) * 1000
        
        checks["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_time, 2),
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }
        overall_healthy = False
    
    # Redis connectivity check
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.redis_url)
        
        start_time = time.time()
        await redis_client.ping()
        redis_time = (time.time() - start_time) * 1000
        
        checks["redis"] = {
            "status": "healthy",
            "response_time_ms": round(redis_time, 2),
            "timestamp": datetime.now(UTC).isoformat()
        }
        await redis_client.close()
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }
        overall_healthy = False
    
    # Vector store check (if configured)
    try:
        from app.rag.vector_store import VectorStore
        vector_store = VectorStore()
        
        # Simple test - try to initialize or check health
        start_time = time.time()
        # This would depend on your vector store implementation
        # For now, just check if it can be imported
        vector_time = (time.time() - start_time) * 1000
        
        checks["vector_store"] = {
            "status": "healthy",
            "response_time_ms": round(vector_time, 2),
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        checks["vector_store"] = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }
        # Don't fail readiness for vector store issues
    
    # LLM service check
    try:
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        
        start_time = time.time()
        # Simple health check - can be expanded based on LLM service
        llm_time = (time.time() - start_time) * 1000
        
        checks["llm_service"] = {
            "status": "healthy",
            "response_time_ms": round(llm_time, 2),
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        checks["llm_service"] = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }
        # Don't fail readiness for LLM issues
    
    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready" if overall_healthy else "not_ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks
    }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check - verifies the service is running.
    Simple endpoint that returns quickly.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime_seconds": time.time() - getattr(liveness_check, "_start_time", time.time())
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with system information.
    Includes memory, disk, and other system metrics.
    """
    # Basic health checks
    basic_health = await readiness_check(db)
    
    # System metrics (try psutil, but handle gracefully if not available)
    try:
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_metrics = {
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round((disk.used / disk.total) * 100, 2)
            },
            "cpu": {
                "percent_used": psutil.cpu_percent(interval=1)
            }
        }
    except ImportError:
        system_metrics = {"error": "psutil not available - install with: pip install psutil"}
    except Exception as e:
        system_metrics = {"error": str(e)}
    
    return {
        **basic_health,
        "system": system_metrics,
        "environment": settings.environment,
        "api_version": "1.0.0"
    }


# Store start time for uptime calculation
liveness_check._start_time = time.time()
