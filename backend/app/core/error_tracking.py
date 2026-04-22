"""
Comprehensive error tracking and monitoring.
"""

import traceback
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import logger


class ErrorTracker:
    """Centralized error tracking system."""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.max_errors = 1000  # Keep last 1000 errors in memory
    
    def track_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[int] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track an error with full context.
        
        Returns:
            Error ID for reference
        """
        error_id = str(uuid.uuid4())
        
        error_data = {
            "error_id": error_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "request": {
                "method": request.method if request else None,
                "url": str(request.url) if request else None,
                "headers": dict(request.headers) if request else None,
                "client_ip": self._get_client_ip(request) if request else None,
                "user_agent": request.headers.get("user-agent") if request else None
            },
            "user_id": user_id,
            "additional_context": additional_context or {},
            "severity": self._determine_severity(error, request)
        }
        
        # Store in memory (in production, send to external service)
        self.errors.append(error_data)
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
        
        # Log to application logger
        logger.error(
            f"Error tracked: {error_id} - {error_data['error_type']}: {error_data['error_message']}",
            extra={
                "error_tracking": True,
                "error_id": error_id,
                **error_data
            }
        )
        
        return error_id
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP from request."""
        if not request:
            return None
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else None
    
    def _determine_severity(self, error: Exception, request: Optional[Request] = None) -> str:
        """Determine error severity based on type and context."""
        if isinstance(error, HTTPException):
            if error.status_code >= 500:
                return "critical"
            elif error.status_code >= 400:
                return "medium"
            else:
                return "low"
        
        # Database errors
        if "database" in str(type(error)).lower() or "sql" in str(type(error)).lower():
            return "high"
        
        # Authentication errors
        if "auth" in str(type(error)).lower() or "token" in str(type(error)).lower():
            return "medium"
        
        # Network/external service errors
        if "connection" in str(error).lower() or "timeout" in str(error).lower():
            return "medium"
        
        # Default to high for unknown errors
        return "high"
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours."""
        cutoff_time = datetime.now(UTC).timestamp() - (hours * 3600)
        
        recent_errors = [
            error for error in self.errors
            if datetime.fromisoformat(error["timestamp"]).timestamp() > cutoff_time
        ]
        
        # Group by error type
        error_types = {}
        for error in recent_errors:
            error_type = error["error_type"]
            if error_type not in error_types:
                error_types[error_type] = {"count": 0, "severity": set()}
            error_types[error_type]["count"] += 1
            error_types[error_type]["severity"].add(error["severity"])
        
        # Get top errors
        top_errors = sorted(
            error_types.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]
        
        return {
            "total_errors": len(recent_errors),
            "timeframe_hours": hours,
            "error_types": dict(error_types),
            "top_errors": top_errors,
            "critical_errors": len([e for e in recent_errors if e["severity"] == "critical"]),
            "high_errors": len([e for e in recent_errors if e["severity"] == "high"]),
            "medium_errors": len([e for e in recent_errors if e["severity"] == "medium"]),
            "low_errors": len([e for e in recent_errors if e["severity"] == "low"])
        }


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track all errors."""
    
    def __init__(self, app, error_tracker: ErrorTracker):
        super().__init__(app)
        self.error_tracker = error_tracker
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Extract user ID from request if available
            user_id = None
            try:
                # This would depend on your auth implementation
                # For now, we'll leave it as None
                pass
            except:
                pass
            
            # Track the error
            error_id = self.error_tracker.track_error(
                error=e,
                request=request,
                user_id=user_id
            )
            
            # Return appropriate error response
            if isinstance(e, HTTPException):
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "error": e.detail,
                        "error_id": error_id,
                        "type": type(e).__name__
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "error_id": error_id,
                        "type": type(e).__name__
                    }
                )


# Global error tracker instance
error_tracker = ErrorTracker()


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance."""
    return error_tracker


async def track_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "ms",
    tags: Optional[Dict[str, str]] = None
):
    """Track performance metrics."""
    metric_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now(UTC).isoformat(),
        "tags": tags or {}
    }
    
    logger.info(
        f"Performance metric: {metric_name} = {value}{unit}",
        extra={
            "performance": True,
            **metric_data
        }
    )


async def track_business_metric(
    metric_name: str,
    value: Any,
    context: Optional[Dict[str, Any]] = None
):
    """Track business-related metrics."""
    metric_data = {
        "metric_name": metric_name,
        "value": value,
        "timestamp": datetime.now(UTC).isoformat(),
        "context": context or {}
    }
    
    logger.info(
        f"Business metric: {metric_name} = {value}",
        extra={
            "business": True,
            **metric_data
        }
    )
