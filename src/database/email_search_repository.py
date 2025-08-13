from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .repositories import BaseRepository
from .email_models import Email, EmailRecipient, Person


class EmailSearchRepository(BaseRepository[Email]):
    """Repository for email search and filtering operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Email, session)
    
    async def search_emails(
        self,
        query: Optional[str] = None,
        person_id: Optional[str] = None,
        project_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        thread_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Email]:
        """Search emails with various filters"""
        stmt = select(Email).options(
            selectinload(Email.sender),
            selectinload(Email.recipients).selectinload(EmailRecipient.person),
            selectinload(Email.project)
        )
        
        # Apply filters
        conditions = []
        
        if query:
            search_term = f"%{query}%"
            conditions.append(
                or_(
                    Email.subject.ilike(search_term),
                    Email.body_text.ilike(search_term)
                )
            )
        
        if person_id:
            # Email from or to this person
            subquery = select(EmailRecipient.email_id).where(
                EmailRecipient.person_id == person_id
            )
            conditions.append(
                or_(
                    Email.from_person_id == person_id,
                    Email.id.in_(subquery)
                )
            )
        
        if project_id:
            conditions.append(Email.project_id == project_id)
        
        if date_from:
            conditions.append(Email.datetime_sent >= date_from)
        
        if date_to:
            conditions.append(Email.datetime_sent <= date_to)
        
        if thread_id:
            conditions.append(Email.thread_id == thread_id)
        
        # Handle additional filters dict
        if filters:
            if filters.get("is_read") is not None:
                conditions.append(Email.is_read == filters["is_read"])
            if filters.get("is_flagged") is not None:
                conditions.append(Email.is_flagged == filters["is_flagged"])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(Email.datetime_sent.desc())
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_thread_emails(self, thread_id: str) -> List[Email]:
        """Get all emails in a thread"""
        return await self.search_emails(thread_id=thread_id, limit=1000)
    
    async def search(
        self,
        filters: Dict[str, Any],
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "datetime_sent",
        sort_order: str = "desc"
    ) -> List[Email]:
        """Search emails with filters"""
        stmt = select(Email).options(
            selectinload(Email.sender),
            selectinload(Email.recipients).selectinload(EmailRecipient.person),
            selectinload(Email.project)
        )
        
        # Apply filters
        conditions = []
        
        if filters.get("query"):
            search_term = f"%{filters['query']}%"
            conditions.append(
                or_(
                    Email.subject.ilike(search_term),
                    Email.body_text.ilike(search_term)
                )
            )
        
        if filters.get("from_email"):
            # Join with Person table to filter by sender email
            stmt = stmt.join(Person, Email.from_person_id == Person.id)
            conditions.append(func.lower(Person.email) == filters["from_email"].lower())
        
        if filters.get("to_email"):
            # Filter by recipient email
            subquery = (
                select(EmailRecipient.email_id)
                .join(Person, EmailRecipient.person_id == Person.id)
                .where(func.lower(Person.email) == filters["to_email"].lower())
            )
            conditions.append(Email.id.in_(subquery))
        
        if filters.get("project_id"):
            conditions.append(Email.project_id == filters["project_id"])
        
        if filters.get("date_from"):
            conditions.append(Email.datetime_sent >= filters["date_from"])
        
        if filters.get("date_to"):
            conditions.append(Email.datetime_sent <= filters["date_to"])
        
        if filters.get("thread_id"):
            conditions.append(Email.thread_id == filters["thread_id"])
        
        if filters.get("is_read") is not None:
            conditions.append(Email.is_read == filters["is_read"])
        
        if filters.get("is_flagged") is not None:
            conditions.append(Email.is_flagged == filters["is_flagged"])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply sorting
        sort_column = getattr(Email, sort_by, Email.datetime_sent)
        if sort_order == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())
        
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count_search_results(self, filters: Dict[str, Any]) -> int:
        """Count search results"""
        stmt = select(func.count(Email.id))
        
        # Apply same filters as search
        conditions = []
        
        if filters.get("query"):
            search_term = f"%{filters['query']}%"
            conditions.append(
                or_(
                    Email.subject.ilike(search_term),
                    Email.body_text.ilike(search_term)
                )
            )
        
        if filters.get("from_email"):
            # Join with Person table to filter by email
            stmt = stmt.join(Person, Email.from_person_id == Person.id)
            conditions.append(func.lower(Person.email) == filters["from_email"].lower())
        
        if filters.get("to_email"):
            # Filter by recipient email
            subquery = (
                select(EmailRecipient.email_id)
                .join(Person, EmailRecipient.person_id == Person.id)
                .where(func.lower(Person.email) == filters["to_email"].lower())
            )
            conditions.append(Email.id.in_(subquery))
        
        if filters.get("project_id"):
            conditions.append(Email.project_id == filters["project_id"])
        
        if filters.get("date_from"):
            conditions.append(Email.datetime_sent >= filters["date_from"])
        
        if filters.get("date_to"):
            conditions.append(Email.datetime_sent <= filters["date_to"])
        
        if filters.get("thread_id"):
            conditions.append(Email.thread_id == filters["thread_id"])
        
        if filters.get("is_read") is not None:
            conditions.append(Email.is_read == filters["is_read"])
        
        if filters.get("is_flagged") is not None:
            conditions.append(Email.is_flagged == filters["is_flagged"])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        result = await self.session.execute(stmt)
        return result.scalar_one()