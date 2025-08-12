from typing import Optional, List, Tuple
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from .models import Document, Tag, document_tags
from ..utils import setup_logging, hash_text

logger = setup_logging("Database.DocumentRepositories")


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)
    
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
    
    def __init__(self, session: AsyncSession):
        super().__init__(Tag, session)
    
    async def get_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name"""
        stmt = select(Tag).where(Tag.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_popular(self, limit: int = 10) -> List[Tuple[Tag, int]]:
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