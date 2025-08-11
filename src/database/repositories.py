from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
from uuid import uuid4

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Base, User, Role, ApiKey, Document, Tag, Tool, Resource,
    Query, AuditLog, Session, user_roles, document_tags
)
from ..utils import setup_logging, hash_text

logger = setup_logging("Database.Repositories")

# Generic type for models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """Create a new record"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def get(self, id: str) -> Optional[ModelType]:
        """Get a record by ID"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get all records with optional filtering"""
        stmt = select(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """Update a record"""
        instance = await self.get(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.session.flush()
        return instance
    
    async def delete(self, id: str) -> bool:
        """Delete a record"""
        instance = await self.get(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
    
    async def count(self, **filters) -> int:
        """Count records with optional filtering"""
        stmt = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class UserRepository(BaseRepository[User]):
    """Repository for User operations"""
    
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
        role_repo = RoleRepository(self.session)
        role = await role_repo.get(role_id)
        
        if user and role and role not in user.roles:
            user.roles.append(role)
            await self.session.flush()
            return True
        return False
    
    async def remove_role(self, user_id: str, role_id: str) -> bool:
        """Remove role from user"""
        user = await self.get(user_id)
        role_repo = RoleRepository(self.session)
        role = await role_repo.get(role_id)
        
        if user and role and role in user.roles:
            user.roles.remove(role)
            await self.session.flush()
            return True
        return False


class RoleRepository(BaseRepository[Role]):
    """Repository for Role operations"""
    
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
    
    async def create_key(
        self,
        user_id: str,
        name: str,
        expires_in_days: Optional[int] = None
    ) -> tuple[ApiKey, str]:
        """Create API key and return both the model and raw key"""
        # Generate random key
        raw_key = f"mcp_{uuid4().hex}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
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
            api_key.last_used = datetime.utcnow()
            await self.session.flush()
        
        return api_key
    
    async def revoke(self, key_id: str) -> bool:
        """Revoke an API key"""
        return await self.update(key_id, is_active=False)


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document operations"""
    
    async def create_with_hash(self, content: str, **kwargs) -> Document:
        """Create document with content hash"""
        content_hash = hash_text(content)
        
        # Check for duplicates
        existing = await self.get_by_hash(content_hash)
        if existing:
            logger.warning(f"Document with same content already exists: {existing.id}")
            return existing
        
        return await self.create(
            content=content,
            content_hash=content_hash,
            **kwargs
        )
    
    async def get_by_hash(self, content_hash: str) -> Optional[Document]:
        """Get document by content hash"""
        stmt = select(Document).where(Document.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_vector_id(self, vector_id: str) -> Optional[Document]:
        """Get document by vector store ID"""
        stmt = select(Document).where(Document.vector_id == vector_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def search(
        self,
        query: str,
        owner_id: Optional[str] = None,
        document_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Document]:
        """Search documents"""
        stmt = select(Document)
        
        # Text search
        if query:
            stmt = stmt.where(
                or_(
                    Document.title.ilike(f"%{query}%"),
                    Document.content.ilike(f"%{query}%")
                )
            )
        
        # Filter by owner
        if owner_id:
            stmt = stmt.where(Document.owner_id == owner_id)
        
        # Filter by type
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        
        # Filter by tags
        if tags:
            stmt = stmt.join(document_tags).join(Tag).where(Tag.name.in_(tags))
        
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def add_tag(self, document_id: str, tag_name: str) -> bool:
        """Add tag to document"""
        document = await self.get(document_id)
        tag_repo = TagRepository(self.session)
        
        # Get or create tag
        tag = await tag_repo.get_by_name(tag_name)
        if not tag:
            tag = await tag_repo.create(name=tag_name)
        
        if document and tag and tag not in document.tags:
            document.tags.append(tag)
            await self.session.flush()
            return True
        return False


class TagRepository(BaseRepository[Tag]):
    """Repository for Tag operations"""
    
    async def get_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name"""
        stmt = select(Tag).where(Tag.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_popular(self, limit: int = 10) -> List[tuple[Tag, int]]:
        """Get most popular tags with document count"""
        stmt = (
            select(Tag, func.count(document_tags.c.document_id).label("doc_count"))
            .outerjoin(document_tags)
            .group_by(Tag.id)
            .order_by(func.count(document_tags.c.document_id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.all())


class ToolRepository(BaseRepository[Tool]):
    """Repository for Tool operations"""
    
    async def get_by_name(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        stmt = select(Tool).where(Tool.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active(self) -> List[Tool]:
        """Get all active tools"""
        stmt = select(Tool).where(Tool.is_active == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def record_usage(
        self,
        tool_id: str,
        success: bool,
        execution_time: float
    ):
        """Record tool usage statistics"""
        tool = await self.get(tool_id)
        if tool:
            tool.usage_count += 1
            if success:
                tool.success_count += 1
            else:
                tool.error_count += 1
            
            # Update average execution time
            if tool.avg_execution_time:
                tool.avg_execution_time = (
                    tool.avg_execution_time * (tool.usage_count - 1) + execution_time
                ) / tool.usage_count
            else:
                tool.avg_execution_time = execution_time
            
            await self.session.flush()


class ResourceRepository(BaseRepository[Resource]):
    """Repository for Resource operations"""
    
    async def get_by_uri(self, uri: str) -> Optional[Resource]:
        """Get resource by URI"""
        stmt = select(Resource).where(Resource.uri == uri)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active(self) -> List[Resource]:
        """Get all active resources"""
        stmt = select(Resource).where(Resource.is_active == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def record_access(self, resource_id: str):
        """Record resource access"""
        resource = await self.get(resource_id)
        if resource:
            resource.access_count += 1
            resource.last_accessed = datetime.utcnow()
            await self.session.flush()


class QueryRepository(BaseRepository[Query]):
    """Repository for Query operations"""
    
    async def get_user_queries(
        self,
        user_id: str,
        limit: int = 10,
        query_type: Optional[str] = None
    ) -> List[Query]:
        """Get user's recent queries"""
        stmt = select(Query).where(Query.user_id == user_id)
        
        if query_type:
            stmt = stmt.where(Query.query_type == query_type)
        
        stmt = stmt.order_by(Query.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_popular_queries(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[tuple[str, int]]:
        """Get popular queries in the last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(Query.query_text, func.count(Query.id).label("count"))
            .where(Query.created_at > cutoff)
            .group_by(Query.query_text)
            .order_by(func.count(Query.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.all())


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for Audit Log operations"""
    
    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """Create audit log entry"""
        return await self.create(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            **kwargs
        )
    
    async def get_user_activity(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get user's recent activity"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp > cutoff
                )
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class SessionRepository(BaseRepository[Session]):
    """Repository for Session operations"""
    
    async def create_session(
        self,
        user_id: str,
        token: str,
        expires_in_minutes: int = 30,
        **kwargs
    ) -> Session:
        """Create user session"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
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
                Session.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()
        
        # Update last activity
        if session:
            session.last_activity = datetime.utcnow()
            await self.session.flush()
        
        return session
    
    async def revoke(self, session_id: str) -> bool:
        """Revoke a session"""
        return await self.update(session_id, is_active=False)
    
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        stmt = (
            delete(Session)
            .where(Session.expires_at < datetime.utcnow())
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount