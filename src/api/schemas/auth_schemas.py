"""
Authentication and authorization schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")


class UserResponse(BaseModel):
    """User response schema (without sensitive data)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = []
    created_at: datetime
    updated_at: datetime


class UserProfile(BaseModel):
    """Current user profile"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    roles: List[str] = []
    is_active: bool = True
    is_superuser: bool = False


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str