"""
Project search and discovery API endpoints
"""

from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.project_repository import ProjectRepository
from src.api.dependencies import get_current_user
from .base import get_db

# Create router (without prefix - will be added by main router)
project_search_router = APIRouter(tags=["project-search"])


@project_search_router.get("/test")
async def test_endpoint():
    """Test endpoint to verify routing works - no auth required"""
    return {"message": "Test endpoint works", "status": "success"}


@project_search_router.get("/search")
async def search_projects(
    q: Optional[str] = Query(None, description="Search query"),
    domain: Optional[str] = Query(None, description="Email domain filter"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search projects by name or domain"""
    
    try:
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
        
        # Convert projects to dictionaries for JSON serialization
        result = []
        for project in projects:
            result.append({
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "email_domains": project.email_domains,
                "is_active": project.is_active,
                "auto_assign": project.auto_assign,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None
            })
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching projects: {str(e)}"
        )


@project_search_router.post("/find-for-email")
async def find_project_for_email(
    data: Dict[str, str],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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