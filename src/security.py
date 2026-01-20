from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from starlette.responses import JSONResponse
import time
import logging
from typing import Dict

from config import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Custom rate limit exceeded handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "error": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.detail.split()[1] if " " in exc.detail else "60"
        },
        headers={"Retry-After": "60"}
    )


class SecurityMiddleware:
    """Security middleware for production deployment"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add security headers
            request = Request(scope, receive)
            
            # Process request
            await self.app(scope, receive, send)
            
            # Add security headers to response
            # Note: This is a simplified version
            # In production, you'd want to properly handle response modification
        else:
            await self.app(scope, receive, send)


def add_security_headers(app):
    """Add security headers to FastAPI app"""
    
    @app.middleware("http")
    async def add_security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Remove server information
        response.headers["Server"] = "SentinelRisk"
        
        return response
    
    return app


class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def validate_transaction_amount(amount: float) -> float:
        """Validate transaction amount"""
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction amount must be positive"
            )
        if amount > 1000000:  # $1M limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction amount exceeds maximum limit"
            )
        return amount
    
    @staticmethod
    def validate_feature_values(features: Dict[str, float]) -> Dict[str, float]:
        """Validate feature values are within reasonable bounds"""
        for key, value in features.items():
            if not isinstance(value, (int, float)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Feature {key} must be numeric"
                )
            if abs(value) > 100:  # Reasonable bound for most features
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Feature {key} value {value} is outside acceptable range"
                )
        return features


# Request logging middleware
class RequestLogger:
    """Log all requests for security monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
    
    async def log_request(self, request: Request, response):
        """Log request details"""
        self.logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"IP: {request.client.host if request.client else 'unknown'} - "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )


# Initialize request logger
request_logger = RequestLogger()
