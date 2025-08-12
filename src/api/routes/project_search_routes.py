"""
Project search and discovery API endpoints
"""

from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.email_repositories import ProjectRepository
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router (without prefix - will be added by main router)
project_search_router = APIRouter(tags=["project-search"])


@project_search_router.get("/search")
async def search_projects(
    q: Optional[str] = Query(None, description="Search query"),
    domain: Optional[str] = Query(None, description="Email domain filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search projects by name or domain"""
    repo = ProjectRepository(db)
    
    if q:
        # Search by name
        projects = await repo.search_by_name(q)
    elif domain:
        # Search by domain
        projects = await repo.search_by_domain(domain)
    else:
        # Return empty list if no search criteria
        projects = []
    
    return projects


@project_search_router.post("/find-for-email")
async def find_project_for_email(
    data: Dict[str, str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Find the appropriate project for an email address"""
    email = data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required"
        )
    
    repo = ProjectRepository(db)
    project = await repo.find_for_email(email)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No project found for this email domain"
        )
    
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "email_domains": project.email_domains
    }