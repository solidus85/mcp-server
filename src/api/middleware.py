import time
import json
import traceback
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import logging

from ..utils import setup_logging, generate_id, get_timestamp
from .base_schemas import ErrorResponse


logger = setup_logging("API.Middleware")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # Let FastAPI handle HTTP exceptions
            raise e
        except Exception as e:
            # Log the error
            error_id = generate_id("error")
            logger.error(
                f"Unhandled exception {error_id}: {str(e)}",
                extra={
                    "error_id": error_id,
                    "path": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc(),
                }
            )
            
            # Return error response
            error_response = ErrorResponse(
                message="An internal error occurred",
                error_code="INTERNAL_ERROR",
                details={"error_id": error_id}
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump()
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = generate_id("req")
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client": request.client.host if request.client else None,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
            }
        )
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier
        client = request.client.host if request.client else "unknown"
        
        # Check rate limit
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if client in self.requests:
            self.requests[client] = [
                req_time for req_time in self.requests[client]
                if req_time > minute_ago
            ]
        else:
            self.requests[client] = []
        
        # Check if limit exceeded
        if len(self.requests[client]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for client: {client}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": 60
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(minute_ago + 60))
                }
            )
        
        # Add current request
        self.requests[client].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[client])
        )
        response.headers["X-RateLimit-Reset"] = str(int(minute_ago + 60))
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response
        
        # Only compress certain content types
        content_type = response.headers.get("content-type", "")
        compressible_types = ["application/json", "text/", "application/javascript"]
        
        if not any(ct in content_type for ct in compressible_types):
            return response
        
        # For simplicity, we're not actually compressing here
        # In production, you would use gzip compression
        # response.headers["content-encoding"] = "gzip"
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers (but don't override CORS headers)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Removed restrictive CSP that might interfere with CORS
        # response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


def setup_cors(app, origins: list = None):
    """Setup CORS middleware"""
    if origins is None:
        # Allow common development origins
        origins = [
            "*",  # Allow all origins in development
            "http://localhost:8080",
            "http://localhost:8090",
            "http://localhost:3000",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8090",
            "http://127.0.0.1:3000",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-*"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )


def setup_middleware(app):
    """Setup all middleware"""
    # Order matters: middleware added first will be the outermost layer
    # CORS needs to be first to handle preflight requests properly
    
    # CORS (must be first to handle OPTIONS requests)
    setup_cors(app)
    
    # Error handling
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Logging
    app.add_middleware(LoggingMiddleware)
    
    # Rate limiting
    from ..config import settings
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.api_rate_limit
    )
    
    # Compression
    app.add_middleware(CompressionMiddleware)
    
    # Security headers (last, so it doesn't interfere with CORS)
    app.add_middleware(SecurityHeadersMiddleware)
    
    logger.info("Middleware setup complete")