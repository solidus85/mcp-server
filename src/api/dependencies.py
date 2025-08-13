from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from datetime import datetime, timedelta, UTC
import logging

from ..config import settings
from ..mcp.server import MCPServer
from ..vector.database import VectorDatabase
from ..vector.search import VectorSearchEngine
from ..utils import setup_logging

# Security - auto_error=False to return 401 instead of 403
security = HTTPBearer(auto_error=False)

# Logger
logger = setup_logging("API.Dependencies")

# Singleton instances
_mcp_server: Optional[MCPServer] = None
_vector_db: Optional[VectorDatabase] = None
_search_engine: Optional[VectorSearchEngine] = None


def get_mcp_server() -> MCPServer:
    """Get or create MCP server instance"""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
        # Register built-in tools and resources
        from ..mcp.builtin_tools import register_builtin_tools
        from ..mcp.builtin_resources import register_builtin_resources
        register_builtin_tools(_mcp_server)
        register_builtin_resources(_mcp_server)
    return _mcp_server


def get_vector_database() -> VectorDatabase:
    """Get or create vector database instance"""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDatabase()
    return _vector_db


def get_search_engine() -> VectorSearchEngine:
    """Get or create search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = VectorSearchEngine(
            database=get_vector_database(),
            use_cache=True
        )
    return _search_engine


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """Verify JWT token and return payload"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token_payload: dict = Depends(verify_token)) -> dict:
    """Get current user from token"""
    username = token_payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    # In a real app, you would fetch user from database
    # For now, return user info from token
    return {
        "username": username,
        "roles": token_payload.get("roles", []),
        "email": token_payload.get("email"),
    }


def require_role(required_role: str):
    """Dependency to require a specific role"""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if required_role not in current_user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    return role_checker


def get_api_key(x_api_key: Annotated[Optional[str], Header()] = None) -> Optional[str]:
    """Extract API key from header"""
    return x_api_key


def validate_api_key(api_key: Optional[str] = Depends(get_api_key)) -> bool:
    """Validate API key (simple implementation)"""
    if not api_key:
        return False
    
    # In production, validate against database or service
    # For now, check against environment variable
    valid_keys = settings.api_keys.split(",") if hasattr(settings, "api_keys") else []
    return api_key in valid_keys


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
        self.logger = setup_logging("RateLimiter")
    
    def check_rate_limit(
        self,
        key: str,
        limit: int = None,
        window: int = None
    ) -> bool:
        """Check if request is within rate limit"""
        limit = limit or settings.api_rate_limit
        window = window or settings.api_rate_limit_period
        
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=window)
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Rate limiting dependency"""
    key = f"user:{current_user['username']}"
    
    if not rate_limiter.check_rate_limit(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return current_user


# Optional authentication (allows both authenticated and unauthenticated access)
def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """Get user if authenticated, None otherwise"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        username = payload.get("sub")
        if username:
            return {
                "username": username,
                "roles": payload.get("roles", []),
                "email": payload.get("email"),
            }
    except JWTError:
        pass
    
    return None