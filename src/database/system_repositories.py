from typing import Optional, List, Tuple
from datetime import datetime, timedelta, UTC

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from .models import Tool, Resource, Query, AuditLog


class ToolRepository(BaseRepository[Tool]):
    """Repository for Tool operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Tool, session)
    
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
    
    def __init__(self, session: AsyncSession):
        super().__init__(Resource, session)
    
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
            resource.last_accessed = datetime.now(UTC)
            await self.session.flush()


class QueryRepository(BaseRepository[Query]):
    """Repository for Query operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Query, session)
    
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
    ) -> List[Tuple[str, int]]:
        """Get popular queries in the last N days"""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
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
    
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)
    
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
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
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