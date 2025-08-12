"""
EmailRepository - Main email repository that combines all email-related operations

This class aggregates functionality from specialized repository modules to provide
a single interface for all email operations while keeping file sizes manageable.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .email_ingestion_repository import EmailIngestionRepository
from .email_search_repository import EmailSearchRepository
from .email_stats_repository import EmailStatsRepository
from .email_models import Email, Person


class EmailRepository:
    """
    Main repository for Email operations.
    Combines functionality from specialized repository classes.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._ingestion_repo = EmailIngestionRepository(session)
        self._search_repo = EmailSearchRepository(session)
        self._stats_repo = EmailStatsRepository(session)
    
    # Delegate to ingestion repository
    async def get(self, id: str) -> Optional[Email]:
        """Get email by ID with all relationships loaded"""
        return await self._ingestion_repo.get(id)
    
    async def get_by_email_id(self, email_id: str) -> Optional[Email]:
        """Get email by external email ID"""
        return await self._ingestion_repo.get_by_email_id(email_id)
    
    async def create(self, **kwargs) -> Email:
        """Create a new email"""
        return await self._ingestion_repo.create(**kwargs)
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Email]:
        """Update an email"""
        return await self._ingestion_repo.update(id, data)
    
    async def delete(self, id: str) -> bool:
        """Delete an email"""
        return await self._ingestion_repo.delete(id)
    
    async def create_with_recipients(
        self,
        email_data: Dict[str, Any],
        to_people: List[Person],
        cc_people: List[Person] = None,
        bcc_people: List[Person] = None
    ) -> Email:
        """Create email with recipients"""
        return await self._ingestion_repo.create_with_recipients(
            email_data, to_people, cc_people, bcc_people
        )
    
    async def ingest_email(
        self,
        email_id: str,
        from_email: str,
        to_emails: List[str],
        subject: str,
        body: str,
        body_text: str,
        datetime_sent: datetime,
        cc_emails: List[str] = None,
        is_update: bool = False,
        **kwargs
    ) -> Email:
        """Ingest a new email, creating people and project associations as needed"""
        return await self._ingestion_repo.ingest_email(
            email_id=email_id,
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            body=body,
            body_text=body_text,
            datetime_sent=datetime_sent,
            cc_emails=cc_emails,
            is_update=is_update,
            **kwargs
        )
    
    async def update_thread_stats(self, thread_id: str):
        """Update email thread statistics"""
        return await self._ingestion_repo.update_thread_stats(thread_id)
    
    # Delegate to search repository
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
        return await self._search_repo.search_emails(
            query=query,
            person_id=person_id,
            project_id=project_id,
            date_from=date_from,
            date_to=date_to,
            thread_id=thread_id,
            filters=filters,
            skip=skip,
            limit=limit
        )
    
    async def get_thread_emails(self, thread_id: str) -> List[Email]:
        """Get all emails in a thread"""
        return await self._search_repo.get_thread_emails(thread_id)
    
    async def search(
        self,
        filters: Dict[str, Any],
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "datetime_sent",
        sort_order: str = "desc"
    ) -> List[Email]:
        """Search emails with filters"""
        return await self._search_repo.search(
            filters=filters,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    async def count_search_results(self, filters: Dict[str, Any]) -> int:
        """Count search results"""
        return await self._search_repo.count_search_results(filters)
    
    # Delegate to stats repository
    async def get_statistics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get email statistics"""
        return await self._stats_repo.get_statistics(date_from, date_to)
    
    async def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get statistics for emails in a project"""
        return await self._stats_repo.get_project_statistics(project_id)
    
    async def get_activity_timeline(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get email activity timeline for the last N days"""
        return await self._stats_repo.get_activity_timeline(days)