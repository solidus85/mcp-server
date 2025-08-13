from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, UTC

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
        
        # Draft count
        stmt = select(func.count(Email.id)).where(Email.is_draft == True)
        if base_conditions:
            stmt = stmt.where(and_(*base_conditions))
        result = await self.session.execute(stmt)
        draft_count = result.scalar_one()
        
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
        
        # Emails by project (top 5)
        stmt = select(
            Email.project_id,
            func.count(Email.id).label("count")
        ).group_by(Email.project_id).order_by(func.count(Email.id).desc()).limit(5)
        if base_conditions:
            stmt = stmt.where(and_(*base_conditions))
        result = await self.session.execute(stmt)
        emails_by_project = {str(row.project_id): row.count for row in result if row.project_id}
        
        # Emails by sender (top 5)
        from .email_models import Person
        stmt = select(
            Person.email,
            func.concat(Person.first_name, ' ', Person.last_name).label("full_name"),
            func.count(Email.id).label("count")
        ).join(Person, Email.from_person_id == Person.id).group_by(
            Person.id, Person.email, Person.first_name, Person.last_name
        ).order_by(func.count(Email.id).desc()).limit(5)
        if base_conditions:
            stmt = stmt.where(and_(*base_conditions))
        result = await self.session.execute(stmt)
        emails_by_sender = [
            {"email": row.email, "name": row.full_name, "count": row.count}
            for row in result
        ]
        
        # Emails by date (last 7 days)
        stmt = select(
            func.date(Email.datetime_sent).label("date"),
            func.count(Email.id).label("count")
        ).where(
            Email.datetime_sent >= datetime.now(UTC) - timedelta(days=7)
        ).group_by(func.date(Email.datetime_sent)).order_by(func.date(Email.datetime_sent))
        result = await self.session.execute(stmt)
        emails_by_date = [
            {"date": row.date.isoformat() if row.date else None, "count": row.count}
            for row in result
        ]
        
        return {
            "total_emails": total_emails,
            "unread_count": unread_count,
            "flagged_count": flagged_count,
            "draft_count": draft_count,
            "thread_count": thread_count,
            "sender_count": sender_count,
            "emails_by_project": emails_by_project,
            "emails_by_sender": emails_by_sender,
            "emails_by_date": emails_by_date,
            "average_response_time": None  # TODO: Calculate this if needed
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
        end_date = datetime.now(UTC)
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