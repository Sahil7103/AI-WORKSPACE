"""
Security audit logging for compliance and monitoring.
"""

import json
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.core.database import get_db
from app.utils.logger import logger


class AuditLogger:
    """Centralized audit logging for security events."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        risk_level: str = "low"  # low, medium, high, critical
    ):
        """
        Log a security audit event.
        
        Args:
            event_type: Type of event (login, logout, api_access, etc.)
            user_id: User ID if available
            ip_address: Client IP address
            user_agent: Browser user agent
            resource: Resource being accessed
            action: Action performed
            success: Whether the action was successful
            details: Additional event details
            risk_level: Risk level for prioritization
        """
        try:
            # Log to structured logger
            log_data = {
                "timestamp": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "resource": resource,
                "action": action,
                "success": success,
                "risk_level": risk_level,
                "details": details or {}
            }
            
            # Log to application logger
            if risk_level in ["high", "critical"]:
                logger.warning(
                    f"Security audit event: {event_type}",
                    extra={
                        "audit": True,
                        **log_data
                    }
                )
            else:
                logger.info(
                    f"Audit event: {event_type}",
                    extra={
                        "audit": True,
                        **log_data
                    }
                )
            
            # Store in database (if audit table exists)
            await self._store_audit_log(log_data)
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    async def _store_audit_log(self, log_data: Dict[str, Any]):
        """Store audit log in database."""
        try:
            # Note: This would require creating an audit_logs table
            # For now, we'll just log to the application logger
            # In production, create the table and uncomment this code
            pass
        except Exception as e:
            logger.error(f"Failed to store audit log: {e}")


class SecurityEventLogger:
    """Specialized logger for security-related events."""
    
    def __init__(self, db: AsyncSession):
        self.audit_logger = AuditLogger(db)
    
    async def log_login_attempt(
        self,
        username: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        failure_reason: Optional[str] = None
    ):
        """Login attempt logging."""
        await self.audit_logger.log_event(
            event_type="login_attempt",
            ip_address=ip_address,
            user_agent=user_agent,
            resource=f"username:{username}",
            action="login",
            success=success,
            details={
                "username": username,
                "failure_reason": failure_reason
            },
            risk_level="high" if not success else "low"
        )
    
    async def log_api_access(
        self,
        user_id: int,
        endpoint: str,
        method: str,
        ip_address: str,
        user_agent: str,
        status_code: int,
        response_time_ms: Optional[int] = None
    ):
        """API access logging."""
        risk_level = "low"
        if status_code >= 400:
            risk_level = "medium" if status_code < 500 else "high"
        
        await self.audit_logger.log_event(
            event_type="api_access",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=endpoint,
            action=method,
            success=status_code < 400,
            details={
                "status_code": status_code,
                "response_time_ms": response_time_ms
            },
            risk_level=risk_level
        )
    
    async def log_data_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: Optional[str] = None,
        action: str = "read",
        ip_address: Optional[str] = None
    ):
        """Data access logging for GDPR compliance."""
        await self.audit_logger.log_event(
            event_type="data_access",
            user_id=user_id,
            ip_address=ip_address,
            resource=f"{resource_type}:{resource_id}" if resource_id else resource_type,
            action=action,
            success=True,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            risk_level="medium"
        )
    
    async def log_security_violation(
        self,
        violation_type: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Security violation logging."""
        await self.audit_logger.log_event(
            event_type="security_violation",
            user_id=user_id,
            ip_address=ip_address,
            action=violation_type,
            success=False,
            details=details,
            risk_level="critical"
        )


# Dependency for getting audit logger in routes
async def get_audit_logger(db: AsyncSession = Depends(get_db)):
    """Dependency to get audit logger instance."""
    return SecurityEventLogger(db)
