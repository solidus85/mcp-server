from typing import Optional, List
from datetime import datetime, UTC
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .repositories import BaseRepository
from .email_models import Project, person_projects
from ..utils import setup_logging

logger = setup_logging("Database.ProjectRepository")


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)
    
    async def get_by_name(self, name: str) -> Optional[Project]:
        """Get project by name"""
        stmt = select(Project).where(
            func.lower(Project.name) == name.lower()
        ).options(selectinload(Project.people))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_domain(self, domain: str) -> Optional[Project]:
        """Get project by email domain"""
        # Get all projects and check domains in Python to avoid PostgreSQL array function issues
        stmt = select(Project).where(
            and_(
                Project.is_active == True,
                Project.email_domains.isnot(None)
            )
        )
        result = await self.session.execute(stmt)
        projects = result.scalars().all()
        
        domain_lower = domain.lower()
        for project in projects:
            if project.email_domains:
                for proj_domain in project.email_domains:
                    if proj_domain.lower() == domain_lower:
                        return project
        return None
    
    async def find_project_for_email(
        self,
        from_email: str,
        to_emails: List[str],
        cc_emails: List[str] = None
    ) -> Optional[Project]:
        """Find the best matching project for an email"""
        all_emails = [from_email] + to_emails + (cc_emails or [])
        domains = list(set(email.split('@')[-1].lower() for email in all_emails))
        
        # Get all active projects with auto-assign enabled
        stmt = select(Project).where(
            and_(
                Project.is_active == True,
                Project.auto_assign == True,
                Project.email_domains.isnot(None)
            )
        )
        result = await self.session.execute(stmt)
        projects = list(result.scalars().all())
        
        if not projects:
            return None
        
        # Find projects that match email domains
        best_project = None
        best_score = 0
        
        for project in projects:
            if not project.email_domains:
                continue
                
            # Count matching domains (case-insensitive)
            project_domains_lower = [d.lower() for d in project.email_domains]
            score = sum(1 for d in domains if d in project_domains_lower)
            
            if score > best_score:
                best_score = score
                best_project = project
        
        return best_project
    
    async def find_for_email(self, email: str) -> Optional[Project]:
        """Find project for a single email address"""
        domain = email.split('@')[-1].lower()
        return await self.get_by_domain(domain)
    
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
            joined_at=datetime.now(UTC)
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
    
    async def search_by_name(self, query: str) -> List[Project]:
        """Search projects by name"""
        search_term = f"%{query}%"
        stmt = select(Project).where(
            Project.name.ilike(search_term)
        ).options(selectinload(Project.people))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def search_by_domain(self, domain: str) -> List[Project]:
        """Search projects by email domain"""
        # Get all projects and check domains in Python
        stmt = select(Project).where(
            Project.email_domains.isnot(None)
        ).options(selectinload(Project.people))
        result = await self.session.execute(stmt)
        projects = result.scalars().all()
        
        domain_lower = domain.lower()
        matching_projects = []
        for project in projects:
            if project.email_domains:
                for proj_domain in project.email_domains:
                    if proj_domain.lower() == domain_lower:
                        matching_projects.append(project)
                        break
        
        return matching_projects
    
    async def get_email_count(self, project_id: str) -> int:
        """Get count of emails in a project"""
        from .email_models import Email
        stmt = select(func.count(Email.id)).where(Email.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def get_statistics(self) -> dict:
        """Get overall project statistics"""
        # Total projects
        total_stmt = select(func.count(Project.id))
        result = await self.session.execute(total_stmt)
        total_projects = result.scalar_one()
        
        # Active projects
        active_stmt = select(func.count(Project.id)).where(Project.is_active == True)
        result = await self.session.execute(active_stmt)
        active_projects = result.scalar_one()
        
        # Projects with auto-assign
        auto_stmt = select(func.count(Project.id)).where(Project.auto_assign == True)
        result = await self.session.execute(auto_stmt)
        auto_assign_projects = result.scalar_one()
        
        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "auto_assign_projects": auto_assign_projects
        }
    
    async def search(
        self,
        filters: dict = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Project]:
        """Search projects with filters"""
        stmt = select(Project).options(selectinload(Project.people))
        
        if filters:
            conditions = []
            if "is_active" in filters:
                conditions.append(Project.is_active == filters["is_active"])
            if "auto_assign" in filters:
                conditions.append(Project.auto_assign == filters["auto_assign"])
            if conditions:
                stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(self, filters: dict = None) -> int:
        """Count projects with filters"""
        stmt = select(func.count(Project.id))
        
        if filters:
            conditions = []
            if "is_active" in filters:
                conditions.append(Project.is_active == filters["is_active"])
            if "auto_assign" in filters:
                conditions.append(Project.auto_assign == filters["auto_assign"])
            if conditions:
                stmt = stmt.where(and_(*conditions))
        
        result = await self.session.execute(stmt)
        return result.scalar_one()