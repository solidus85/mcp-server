from typing import Optional, List, Tuple
from sqlalchemy import select, delete, and_, or_, func, insert
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