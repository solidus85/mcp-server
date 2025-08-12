from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import BaseRepository
from .email_models import EmailThread, Email


class EmailThreadRepository(BaseRepository[EmailThread]):
    """Repository for EmailThread operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(EmailThread, session)
    
    async def get_by_thread_id(self, thread_id: str) -> Optional[EmailThread]:
        """Get thread by thread ID"""
        stmt = select(EmailThread).where(EmailThread.thread_id == thread_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_thread_emails(self, thread_id: str) -> List[Email]:
        """Get all emails in a thread"""
        from .email_repository import EmailRepository
        
        email_repo = EmailRepository(self.session)
        return await email_repo.search_emails(thread_id=thread_id, limit=1000)