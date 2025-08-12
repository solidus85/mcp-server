from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import BaseRepository
from .email_models import Email


class EmailStatsRepository(BaseRepository[Email]):
    """Repository for email statistics and analytics operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Email, session)
    
    async def get_statistics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get email statistics"""
        # Base query
        base_conditions = []
        if date_from:
            base_conditions.append(Email.datetime_sent >= date_from)
        if date_to:
            base_conditions.append(Email.datetime_sent <= date_to)
        
        # Total emails
        stmt = select(func.count(Email.id))
        if base_conditions:
            stmt = stmt.where(and_(*base_conditions))
        result = await self.session.execute(stmt)
        total_emails = result.scalar_one()
        
        # Unread count
        stmt = select(func.count(Email.id)).where(Email.is_read == False)
        if base_conditions:
            stmt = stmt.where(and_(*base_conditions))
        result = await self.session.execute(stmt)
        unread_count = result.scalar_one()
        
        # Flagged count
        stmt = select(func.count(Email.id)).where(Email.is_flagged == True)
        if base_conditions:
            stmt = stmt.where(and_(*base_conditions))
        result = await self.session.execute(stmt)
        flagged_count = result.scalar_one()
        
        # Thread count
        stmt = select(func.count(distinct(Email.thread_id)))
        if base_conditions:
            stmt = stmt.where(and_(*base_conditions))
        result = await self.session.execute(stmt)
        thread_count = result.scalar_one()
        
        # Sender count
        stmt = select(func.count(distinct(Email.from_person_id)))
        if base_conditions:
            stmt = stmt.where(and_(*base_conditions))
        result = await self.session.execute(stmt)
        sender_count = result.scalar_one()
        
        return {
            "total_emails": total_emails,
            "unread_count": unread_count,
            "flagged_count": flagged_count,
            "thread_count": thread_count,
            "sender_count": sender_count
        }
    
    async def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get statistics for emails in a project"""
        # Count emails in project
        stmt = select(func.count(Email.id)).where(Email.project_id == project_id)
        result = await self.session.execute(stmt)
        email_count = result.scalar_one()
        
        # Count unread
        stmt = select(func.count(Email.id)).where(
            and_(Email.project_id == project_id, Email.is_read == False)
        )
        result = await self.session.execute(stmt)
        unread_count = result.scalar_one()
        
        # Count threads
        stmt = select(func.count(distinct(Email.thread_id))).where(
            Email.project_id == project_id
        )
        result = await self.session.execute(stmt)
        thread_count = result.scalar_one()
        
        return {
            "project_id": project_id,
            "email_count": email_count,
            "unread_count": unread_count,
            "thread_count": thread_count
        }
    
    async def get_activity_timeline(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get email activity timeline for the last N days"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Group emails by date
        stmt = select(
            func.date(Email.datetime_sent).label("date"),
            func.count(Email.id).label("count")
        ).where(
            Email.datetime_sent >= start_date
        ).group_by(
            func.date(Email.datetime_sent)
        ).order_by(
            func.date(Email.datetime_sent)
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        timeline = []
        for row in rows:
            timeline.append({
                "date": row.date.isoformat() if row.date else None,
                "count": row.count
            })
        
        return timeline