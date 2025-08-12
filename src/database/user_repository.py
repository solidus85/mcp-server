from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from .models import User, Role


class UserRepository(BaseRepository[User]):
    """Repository for User operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(User).where(User.username == username).options(
            selectinload(User.roles)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email).options(
            selectinload(User.roles)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_with_password(
        self,
        username: str,
        email: str,
        password: str,
        **kwargs
    ) -> User:
        """Create user with hashed password"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        password_hash = pwd_context.hash(password)
        
        return await self.create(
            username=username,
            email=email,
            password_hash=password_hash,
            **kwargs
        )
    
    async def verify_password(self, user: User, password: str) -> bool:
        """Verify user password"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not user.password_hash:
            return False
        
        return pwd_context.verify(password, user.password_hash)
    
    async def add_role(self, user_id: str, role_id: str) -> bool:
        """Add role to user"""
        user = await self.get(user_id)
        if not user:
            return False
        
        # Get role directly using SQL
        stmt = select(Role).where(Role.id == role_id)
        result = await self.session.execute(stmt)
        role = result.scalar_one_or_none()
        
        if role and role not in user.roles:
            user.roles.append(role)
            await self.session.flush()
            return True
        return False
    
    async def remove_role(self, user_id: str, role_id: str) -> bool:
        """Remove role from user"""
        user = await self.get(user_id)
        if not user:
            return False
        
        # Get role directly using SQL
        stmt = select(Role).where(Role.id == role_id)
        result = await self.session.execute(stmt)
        role = result.scalar_one_or_none()
        
        if user and role and role in user.roles:
            user.roles.remove(role)
            await self.session.flush()
            return True
        return False