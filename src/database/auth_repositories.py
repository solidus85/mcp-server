from typing import Optional, List, Tuple
from datetime import datetime, timedelta, UTC
import hashlib
from uuid import uuid4

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from .models import Role, ApiKey, Session
from ..utils import setup_logging

logger = setup_logging("Database.AuthRepositories")


class RoleRepository(BaseRepository[Role]):
    """Repository for Role operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        stmt = select(Role).where(Role.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_default_roles(self):
        """Create default system roles"""
        default_roles = [
            {
                "name": "admin",
                "description": "Administrator with full access",
                "permissions": ["*"]
            },
            {
                "name": "user",
                "description": "Regular user with standard access",
                "permissions": ["read", "write", "execute"]
            },
            {
                "name": "viewer",
                "description": "Read-only access",
                "permissions": ["read"]
            }
        ]
        
        for role_data in default_roles:
            existing = await self.get_by_name(role_data["name"])
            if not existing:
                await self.create(**role_data)


class ApiKeyRepository(BaseRepository[ApiKey]):
    """Repository for API Key operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ApiKey, session)
    
    async def create_key(
        self,
        user_id: str,
        name: str,
        expires_in_days: Optional[int] = None
    ) -> Tuple[ApiKey, str]:
        """Create API key and return both the model and raw key"""
        # Generate random key
        raw_key = f"mcp_{uuid4().hex}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
        
        api_key = await self.create(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            expires_at=expires_at
        )
        
        return api_key, raw_key
    
    async def get_by_key(self, raw_key: str) -> Optional[ApiKey]:
        """Get API key by raw key value"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        stmt = select(ApiKey).where(
            and_(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True
            )
        ).options(selectinload(ApiKey.user))
        
        result = await self.session.execute(stmt)
        api_key = result.scalar_one_or_none()
        
        # Update last used
        if api_key:
            api_key.last_used = datetime.now(UTC)
            await self.session.flush()
        
        return api_key
    
    async def revoke(self, key_id: str) -> bool:
        """Revoke an API key"""
        return await self.update(key_id, is_active=False)


class SessionRepository(BaseRepository[Session]):
    """Repository for Session operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Session, session)
    
    async def create_session(
        self,
        user_id: str,
        token: str,
        expires_in_minutes: int = 30,
        **kwargs
    ) -> Session:
        """Create user session"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(minutes=expires_in_minutes)
        
        return await self.create(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            **kwargs
        )
    
    async def get_by_token(self, token: str) -> Optional[Session]:
        """Get session by token"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        stmt = select(Session).where(
            and_(
                Session.token_hash == token_hash,
                Session.is_active == True,
                Session.expires_at > datetime.now(UTC)
            )
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()
        
        # Update last activity
        if session:
            session.last_activity = datetime.now(UTC)
            await self.session.flush()
        
        return session
    
    async def revoke(self, session_id: str) -> bool:
        """Revoke a session"""
        return await self.update(session_id, is_active=False)
    
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        stmt = (
            delete(Session)
            .where(Session.expires_at < datetime.now(UTC))
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount