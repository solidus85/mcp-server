from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .repositories import BaseRepository
from .email_models import (
    Email, EmailRecipient, EmailThread, Person,
    RecipientType
)
from .person_repository import PersonRepository
from .project_repository import ProjectRepository
from ..utils import setup_logging

logger = setup_logging("Database.EmailIngestion")


class EmailIngestionRepository(BaseRepository[Email]):
    """Repository for email ingestion and creation operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Email, session)
    
    async def get(self, id: str) -> Optional[Email]:
        """Get email by ID with all relationships loaded"""
        stmt = select(Email).where(Email.id == id).options(
            selectinload(Email.sender),
            selectinload(Email.recipients).selectinload(EmailRecipient.person),
            selectinload(Email.project)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email_id(self, email_id: str) -> Optional[Email]:
        """Get email by external email ID"""
        stmt = select(Email).where(Email.email_id == email_id).options(
            selectinload(Email.sender),
            selectinload(Email.recipients).selectinload(EmailRecipient.person),
            selectinload(Email.project)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_with_recipients(
        self,
        email_data: Dict[str, Any],
        to_people: List[Person],
        cc_people: List[Person] = None,
        bcc_people: List[Person] = None
    ) -> Email:
        """Create email with recipients"""
        # Create email
        email = await self.create(**email_data)
        
        # Add recipients
        recipients = []
        
        for person in to_people:
            recipients.append(EmailRecipient(
                email_id=email.id,
                person_id=person.id,
                recipient_type=RecipientType.TO
            ))
        
        for person in (cc_people or []):
            recipients.append(EmailRecipient(
                email_id=email.id,
                person_id=person.id,
                recipient_type=RecipientType.CC
            ))
        
        for person in (bcc_people or []):
            recipients.append(EmailRecipient(
                email_id=email.id,
                person_id=person.id,
                recipient_type=RecipientType.BCC
            ))
        
        self.session.add_all(recipients)
        await self.session.flush()
        
        return email
    
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
        # Check if email already exists
        existing = await self.get_by_email_id(email_id)
        if existing:
            logger.info(f"Email {email_id} already exists, updating")
            # Update existing email
            update_data = {
                'subject': subject,
                'body': body,
                'body_text': body_text,
                'datetime_sent': datetime_sent,
                **kwargs
            }
            for key, value in update_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.flush()
            # Return the reloaded email with all relationships
            return await self.get_by_email_id(email_id)
        
        # Get or create people
        person_repo = PersonRepository(self.session)
        project_repo = ProjectRepository(self.session)
        
        # Create sender
        sender, _ = await person_repo.get_or_create(from_email)
        
        # Create recipients
        to_people = []
        for email in to_emails:
            person, _ = await person_repo.get_or_create(email)
            to_people.append(person)
        
        cc_people = []
        for email in (cc_emails or []):
            person, _ = await person_repo.get_or_create(email)
            cc_people.append(person)
        
        # Find project
        project = await project_repo.find_project_for_email(
            from_email, to_emails, cc_emails
        )
        
        # Determine thread ID
        thread_id = kwargs.get('thread_id')
        if not thread_id and kwargs.get('in_reply_to'):
            # Try to find thread from reply
            stmt = select(Email.thread_id).where(
                Email.message_id == kwargs.get('in_reply_to')
            )
            result = await self.session.execute(stmt)
            existing_thread = result.scalar_one_or_none()
            if existing_thread:
                thread_id = existing_thread
        
        if not thread_id:
            thread_id = f"thread_{uuid4().hex[:12]}"
        
        # Create email
        email_data = {
            'email_id': email_id,
            'from_person_id': sender.id,
            'subject': subject,
            'body': body,
            'body_text': body_text,
            'datetime_sent': datetime_sent,
            'thread_id': thread_id,
            'project_id': project.id if project else None,
            **kwargs
        }
        
        email = await self.create_with_recipients(
            email_data,
            to_people,
            cc_people
        )
        
        logger.info(f"Ingested email {email_id} with {len(to_people)} TO recipients")
        
        # Update thread statistics
        await self.update_thread_stats(thread_id)
        
        # Fetch the email with all relationships loaded
        return await self.get_by_email_id(email_id)
    
    async def update_thread_stats(self, thread_id: str):
        """Update email thread statistics"""
        from .email_thread_repository import EmailThreadRepository
        
        stmt = select(
            func.count(Email.id).label('count'),
            func.min(Email.datetime_sent).label('first'),
            func.max(Email.datetime_sent).label('last'),
            func.array_agg(distinct(Email.from_person_id)).label('participants')
        ).where(Email.thread_id == thread_id)
        
        result = await self.session.execute(stmt)
        stats = result.first()
        
        if stats and stats.count > 0:
            # Get or create thread record
            thread_repo = EmailThreadRepository(self.session)
            thread = await thread_repo.get_by_thread_id(thread_id)
            
            if not thread:
                # Get subject from first email
                stmt = select(Email.subject, Email.project_id).where(
                    Email.thread_id == thread_id
                ).order_by(Email.datetime_sent).limit(1)
                result = await self.session.execute(stmt)
                first_email = result.first()
                
                if first_email:
                    await thread_repo.create(
                        thread_id=thread_id,
                        subject=first_email.subject,
                        email_count=stats.count,
                        participant_count=len(stats.participants or []),
                        first_email_date=stats.first,
                        last_email_date=stats.last,
                        participants=stats.participants or [],
                        project_id=first_email.project_id
                    )
            else:
                # Update existing thread
                await thread_repo.update(
                    thread.id,
                    email_count=stats.count,
                    participant_count=len(stats.participants or []),
                    last_email_date=stats.last,
                    participants=stats.participants or []
                )