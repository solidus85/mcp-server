"""
Authentication and authorization routes
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.user_repository import UserRepository
from src.database.auth_repositories import RoleRepository, SessionRepository
from src.database.models import User
from src.api.schemas.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserProfile,
    PasswordChangeRequest,
    PasswordResetRequest,
    MessageResponse
)
from src.api.dependencies import (
    create_access_token,
    get_current_user,
    verify_token
)
from src.api.routes.base import get_db
from src.config import settings

# Create router
auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token"""
    # If using simple auth, just check username/password match test credentials
    if settings.use_simple_auth:
        if (request.username == settings.test_username and 
            request.password == settings.test_password):
            # Return the simple token
            return TokenResponse(
                access_token=settings.simple_auth_token,
                token_type="bearer",
                expires_in=999999999  # Effectively never expires
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    
    # Original JWT-based authentication (if simple auth disabled)
    repo = UserRepository(db)
    
    # Get user by username
    user = await repo.get_by_username(request.username)
    if not user:
        # Try by email if username not found
        user = await repo.get_by_email(request.username)
    
    # Verify password
    if not user or not await repo.verify_password(user, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Get user roles
    role_names = [role.name for role in user.roles] if user.roles else ["user"]
    
    # Create access token
    token_data = {
        "sub": user.username,
        "email": user.email,
        "roles": role_names
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.jwt_expiration_minutes)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60  # Convert to seconds
    )


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    
    # Check if username exists
    existing_user = await user_repo.get_by_username(request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Check if email exists
    existing_email = await user_repo.get_by_email(request.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    user = await user_repo.create_with_password(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    await db.commit()
    
    # Assign default role using direct SQL to avoid lazy loading issues
    default_role = await role_repo.get_by_name("user")
    if default_role:
        from src.database.models import user_roles
        from sqlalchemy import insert
        stmt = insert(user_roles).values(user_id=user.id, role_id=default_role.id)
        await db.execute(stmt)
        await db.commit()
    
    # Get user with roles loaded
    user = await user_repo.get_by_username(request.username)
    
    # Return user with roles as strings
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=[role.name for role in user.roles] if user.roles else [],
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@auth_router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information"""
    # If using simple auth, return test user info
    if settings.use_simple_auth:
        return UserProfile(
            username=settings.test_username,
            email=settings.test_email,
            full_name="Test User",
            roles=current_user.get("roles", ["user"]),
            is_active=True,
            is_superuser=settings.test_is_admin
        )
    
    # Original database lookup (if simple auth disabled)
    repo = UserRepository(db)
    
    # Get full user data from database
    user = await repo.get_by_username(current_user["username"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfile(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=[role.name for role in user.roles] if user.roles else [],
        is_active=user.is_active,
        is_superuser=user.is_superuser
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: dict = Depends(get_current_user)
):
    """Refresh access token"""
    # Create new token with same user data
    token_data = {
        "sub": current_user["username"],
        "email": current_user.get("email"),
        "roles": current_user.get("roles", [])
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.jwt_expiration_minutes)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60
    )


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user (invalidate session if using sessions)"""
    # In a real application, you might want to:
    # 1. Blacklist the token
    # 2. Delete the session from database
    # 3. Clear any server-side cache
    
    # For now, just return success message
    # The client should delete the token
    return MessageResponse(message="Successfully logged out")


@auth_router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user's password"""
    repo = UserRepository(db)
    
    # Get user from database
    user = await repo.get_by_username(current_user["username"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not await repo.verify_password(user, request.current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.password_hash = pwd_context.hash(request.new_password)
    
    await db.commit()
    
    return MessageResponse(message="Password changed successfully")


@auth_router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset"""
    repo = UserRepository(db)
    
    # Check if user exists
    user = await repo.get_by_email(request.email)
    
    # Always return success to prevent email enumeration
    # In a real application, you would:
    # 1. Generate a reset token
    # 2. Send email with reset link
    # 3. Store token in database with expiration
    
    if user:
        # TODO: Send password reset email
        pass
    
    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )