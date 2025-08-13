from typing import Optional, List, Tuple
from sqlalchemy import select, delete, and_, or_, func, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .repositories import BaseRepository
from .email_models import Person, person_projects
from ..utils import setup_logging

logger = setup_logging("Database.PersonRepository")


class PersonRepository(BaseRepository[Person]):
    """Repository for Person operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Person, session)
    
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
        filters: dict = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Person]:
        """Search people by various filters"""
        stmt = select(Person)
        
        if filters:
            # Handle text search
            if "query" in filters:
                search_term = f"%{filters['query']}%"
                stmt = stmt.where(
                    or_(
                        Person.email.ilike(search_term),
                        Person.display_name.ilike(search_term),
                        Person.first_name.ilike(search_term),
                        Person.last_name.ilike(search_term),
                    )
                )
            
            # Handle specific field filters
            if "email" in filters:
                stmt = stmt.where(func.lower(Person.email) == filters["email"].lower())
            
            if "organization" in filters:
                stmt = stmt.where(Person.organization == filters["organization"])
            
            if "is_active" in filters:
                stmt = stmt.where(Person.is_active == filters["is_active"])
            
            if "is_external" in filters:
                stmt = stmt.where(Person.is_external == filters["is_external"])
            
            if "project_id" in filters:
                stmt = stmt.join(person_projects).where(
                    person_projects.c.project_id == filters["project_id"]
                )
        
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count_search_results(self, filters: dict = None) -> int:
        """Count search results with filters"""
        stmt = select(func.count()).select_from(Person)
        
        if filters:
            if "query" in filters:
                search_term = f"%{filters['query']}%"
                stmt = stmt.where(
                    or_(
                        Person.email.ilike(search_term),
                        Person.display_name.ilike(search_term),
                        Person.first_name.ilike(search_term),
                        Person.last_name.ilike(search_term),
                    )
                )
            
            if "email" in filters:
                stmt = stmt.where(func.lower(Person.email) == filters["email"].lower())
            
            if "organization" in filters:
                stmt = stmt.where(Person.organization == filters["organization"])
            
            if "is_active" in filters:
                stmt = stmt.where(Person.is_active == filters["is_active"])
            
            if "is_external" in filters:
                stmt = stmt.where(Person.is_external == filters["is_external"])
            
            if "project_id" in filters:
                stmt = stmt.join(person_projects).where(
                    person_projects.c.project_id == filters["project_id"]
                )
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
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
    
    async def add_to_project(
        self,
        person_id: str,
        project_id: str,
        role: str = "member"
    ) -> bool:
        """Add person to project"""
        try:
            stmt = insert(person_projects).values(
                person_id=person_id,
                project_id=project_id,
                role=role
            )
            await self.session.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Error adding person to project: {e}")
            return False
    
    async def remove_from_project(
        self,
        person_id: str,
        project_id: str
    ) -> bool:
        """Remove person from project"""
        try:
            stmt = delete(person_projects).where(
                and_(
                    person_projects.c.person_id == person_id,
                    person_projects.c.project_id == project_id
                )
            )
            await self.session.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Error removing person from project: {e}")
            return False
    
    async def search_by_domain(self, domain: str, limit: int = 20) -> List[Person]:
        """Search people by email domain"""
        stmt = select(Person).where(
            Person.email.ilike(f"%@{domain}")
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def autocomplete(self, prefix: str, limit: int = 10) -> List[Person]:
        """Autocomplete people by name prefix"""
        search_term = f"{prefix}%"
        stmt = select(Person).where(
            or_(
                Person.first_name.ilike(search_term),
                Person.last_name.ilike(search_term),
                Person.display_name.ilike(search_term),
                Person.email.ilike(search_term)
            )
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_person_statistics(self, person_id: str) -> dict:
        """Get statistics for a person"""
        from .email_models import Email
        
        # Count emails sent
        sent_stmt = select(func.count()).select_from(Email).where(
            Email.from_person_id == person_id
        )
        sent_result = await self.session.execute(sent_stmt)
        emails_sent = sent_result.scalar() or 0
        
        # Count emails received (as recipient)
        from .email_models import EmailRecipient
        received_stmt = select(func.count()).select_from(EmailRecipient).where(
            EmailRecipient.person_id == person_id
        )
        received_result = await self.session.execute(received_stmt)
        emails_received = received_result.scalar() or 0
        
        # Count projects
        projects_stmt = select(func.count()).select_from(person_projects).where(
            person_projects.c.person_id == person_id
        )
        projects_result = await self.session.execute(projects_stmt)
        projects_count = projects_result.scalar() or 0
        
        # Get first and last email dates
        date_stmt = select(
            func.min(Email.datetime_sent),
            func.max(Email.datetime_sent)
        ).where(Email.from_person_id == person_id)
        date_result = await self.session.execute(date_stmt)
        first_date, last_date = date_result.one()
        
        return {
            "emails_sent": emails_sent,
            "emails_received": emails_received,
            "projects_count": projects_count,
            "first_email_date": first_date,
            "last_email_date": last_date
        }
    
    async def get_person_emails(self, person_id: str, limit: int = 100) -> dict:
        """Get emails sent and received by a person"""
        from .email_models import Email, EmailRecipient
        
        # Get sent emails
        sent_stmt = select(Email).where(
            Email.from_person_id == person_id
        ).limit(limit)
        sent_result = await self.session.execute(sent_stmt)
        sent_emails = list(sent_result.scalars().all())
        
        # Get received emails
        received_stmt = (
            select(Email)
            .join(EmailRecipient)
            .where(EmailRecipient.person_id == person_id)
            .limit(limit)
        )
        received_result = await self.session.execute(received_stmt)
        received_emails = list(received_result.scalars().all())
        
        return {
            "sent": sent_emails,
            "received": received_emails
        }
    
    async def get_person_projects(self, person_id: str) -> List[dict]:
        """Get projects for a person with role information"""
        from .email_models import Project
        
        stmt = (
            select(Project, person_projects.c.role)
            .join(person_projects)
            .where(person_projects.c.person_id == person_id)
        )
        result = await self.session.execute(stmt)
        
        projects = []
        for project, role in result:
            project_dict = {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "role": role
            }
            projects.append(project_dict)
        
        return projects
    
    async def merge_persons(self, primary_id: str, merge_id: str) -> bool:
        """Merge two person records"""
        try:
            from .email_models import Email, EmailRecipient
            
            # Update emails sent by the merge person
            update_sent = (
                update(Email)
                .where(Email.from_person_id == merge_id)
                .values(from_person_id=primary_id)
            )
            await self.session.execute(update_sent)
            
            # Update email recipients
            update_recipients = (
                update(EmailRecipient)
                .where(EmailRecipient.person_id == merge_id)
                .values(person_id=primary_id)
            )
            await self.session.execute(update_recipients)
            
            # Update project memberships (avoid duplicates)
            # First get existing projects for primary person
            existing_stmt = select(person_projects.c.project_id).where(
                person_projects.c.person_id == primary_id
            )
            existing_result = await self.session.execute(existing_stmt)
            existing_projects = set(row[0] for row in existing_result)
            
            # Get projects for merge person
            merge_stmt = select(
                person_projects.c.project_id,
                person_projects.c.role
            ).where(person_projects.c.person_id == merge_id)
            merge_result = await self.session.execute(merge_stmt)
            
            # Add non-duplicate projects
            for project_id, role in merge_result:
                if project_id not in existing_projects:
                    insert_stmt = insert(person_projects).values(
                        person_id=primary_id,
                        project_id=project_id,
                        role=role
                    )
                    await self.session.execute(insert_stmt)
            
            # Delete the merge person
            await self.delete(merge_id)
            
            return True
        except Exception as e:
            logger.error(f"Error merging persons: {e}")
            return False