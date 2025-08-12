from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Base

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
    
    async def update(self, id: str, data: dict = None, **kwargs) -> Optional[ModelType]:
        """Update a record"""
        instance = await self.get(id)
        if instance:
            # Handle both dict and kwargs
            update_data = data if data else kwargs
            for key, value in update_data.items():
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