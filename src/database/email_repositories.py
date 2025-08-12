from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, update, delete, and_, or_, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from .repositories import BaseRepository
from .email_models import (
    Person, Project, Email, EmailRecipient, EmailThread,
    RecipientType, person_projects
)
from ..utils import setup_logging

logger = setup_logging("Database.EmailRepositories")


class PersonRepository(BaseRepository[Person]):
    """Repository for Person operations"""
    
    async def get_by_email(self, email: str) -> Optional[Person]:
        """Get person by email address"""
        stmt = select(Person).where(
            func.lower(Person.email) == email.lower()
        ).options(selectinload(Person.projects))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_or_create(
        self,
        email: str,
        display_name: Optional[str] = None,
        **kwargs
    ) -> Tuple[Person, bool]:
        """Get existing person or create new one"""
        # Check if person exists
        existing = await self.get_by_email(email)
        if existing:
            return existing, False
        
        # Parse name from display name if provided
        first_name = None
        last_name = None
        if display_name:
            parts = display_name.strip().split(' ', 1)
            if len(parts) == 2:
                first_name, last_name = parts
            else:
                first_name = parts[0]
        
        # Determine if external email
        domain = email.split('@')[-1].lower()
        is_external = domain not in kwargs.get('internal_domains', [])
        
        # Create new person
        person = await self.create(
            email=email.lower(),
            display_name=display_name,
            first_name=first_name,
            last_name=last_name,
            is_external=is_external,
            **{k: v for k, v in kwargs.items() if k != 'internal_domains'}
        )
        
        logger.info(f"Created new person: {email}")
        return person, True
    
    async def search(
        self,
        query: str,
        limit: int = 20
    ) -> List[Person]:
        """Search people by name or email"""
        search_term = f"%{query}%"
        stmt = select(Person).where(
            or_(
                Person.email.ilike(search_term),
                Person.display_name.ilike(search_term),
                Person.first_name.ilike(search_term),
                Person.last_name.ilike(search_term),
            )
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_project(self, project_id: str) -> List[Person]:
        """Get all people in a project"""
        stmt = (
            select(Person)
            .join(person_projects)
            .where(person_projects.c.project_id == project_id)
            .options(selectinload(Person.projects))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project operations"""
    
    async def get_by_name(self, name: str) -> Optional[Project]:
        """Get project by name"""
        stmt = select(Project).where(
            func.lower(Project.name) == name.lower()
        ).options(selectinload(Project.people))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_domain(self, domain: str) -> Optional[Project]:
        """Get project by email domain"""
        stmt = select(Project).where(
            func.lower(domain) == func.any(func.lower(Project.email_domains))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_project_for_email(
        self,
        from_email: str,
        to_emails: List[str],
        cc_emails: List[str] = None
    ) -> Optional[Project]:
        """Find the best matching project for an email"""
        all_emails = [from_email] + to_emails + (cc_emails or [])
        domains = list(set(email.split('@')[-1].lower() for email in all_emails))
        
        # Find projects that match any of the domains
        stmt = select(Project).where(
            and_(
                Project.is_active == True,
                Project.auto_assign == True,
                or_(*[func.lower(d) == func.any(func.lower(Project.email_domains)) for d in domains])
            )
        )
        result = await self.session.execute(stmt)
        projects = list(result.scalars().all())
        
        if not projects:
            return None
        
        # Return the project with the most domain matches
        best_project = None
        best_score = 0
        
        for project in projects:
            score = sum(1 for d in domains if project.has_domain(f"test@{d}"))
            if score > best_score:
                best_score = score
                best_project = project
        
        return best_project
    
    async def add_person(
        self,
        project_id: str,
        person_id: str,
        role: str = "member"
    ) -> bool:
        """Add a person to a project"""
        # Check if already in project
        stmt = select(person_projects).where(
            and_(
                person_projects.c.project_id == project_id,
                person_projects.c.person_id == person_id
            )
        )
        result = await self.session.execute(stmt)
        if result.first():
            return False
        
        # Add to project
        stmt = person_projects.insert().values(
            project_id=project_id,
            person_id=person_id,
            role=role,
            joined_at=datetime.utcnow()
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return True
    
    async def remove_person(self, project_id: str, person_id: str) -> bool:
        """Remove a person from a project"""
        stmt = person_projects.delete().where(
            and_(
                person_projects.c.project_id == project_id,
                person_projects.c.person_id == person_id
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0


class EmailRepository(BaseRepository[Email]):
    """Repository for Email operations"""
    
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
        **kwargs
    ) -> Email:
        """Ingest a new email, creating people and project associations as needed"""
        # Check if email already exists
        existing = await self.get_by_email_id(email_id)
        if existing:
            logger.info(f"Email {email_id} already exists")
            return existing
        
        # Get or create people
        person_repo = PersonRepository(Person, self.session)
        project_repo = ProjectRepository(Project, self.session)
        
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
        
        return email
    
    async def update_thread_stats(self, thread_id: str):
        """Update email thread statistics"""
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
            thread_repo = EmailThreadRepository(EmailThread, self.session)
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
    
    async def search_emails(
        self,
        query: Optional[str] = None,
        person_id: Optional[str] = None,
        project_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        thread_id: Optional[str] = None,
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
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(Email.datetime_sent.desc())
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class EmailThreadRepository(BaseRepository[EmailThread]):
    """Repository for EmailThread operations"""
    
    async def get_by_thread_id(self, thread_id: str) -> Optional[EmailThread]:
        """Get thread by thread ID"""
        stmt = select(EmailThread).where(EmailThread.thread_id == thread_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_thread_emails(self, thread_id: str) -> List[Email]:
        """Get all emails in a thread"""
        email_repo = EmailRepository(Email, self.session)
        return await email_repo.search_emails(thread_id=thread_id, limit=1000)