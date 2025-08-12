"""
Project statistics and analytics API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.email_repositories import (
    EmailRepository,
    ProjectRepository
)
from src.api.schemas.email_schemas import ProjectStatistics
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router (without prefix - will be added by main router)
project_stats_router = APIRouter(tags=["project-stats"])


@project_stats_router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific project"""
    repo = ProjectRepository(db)
    
    # Get project to ensure it exists
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get statistics
    email_count = await repo.get_email_count(project_id)
    person_count = len(project.people) if project.people else 0
    
    # Get thread count
    email_repo = EmailRepository(db)
    emails = await email_repo.search_emails(filters={"project_id": project_id})
    thread_ids = set()
    for email in emails:
        if email.thread_id:
            thread_ids.add(email.thread_id)
    
    # Get last activity
    last_activity = None
    if emails:
        last_activity = max(email.datetime_sent for email in emails)
    
    return {
        "email_count": email_count,
        "person_count": person_count,
        "thread_count": len(thread_ids),
        "last_activity": last_activity.isoformat() if last_activity else None
    }


@project_stats_router.get("/statistics/overview", response_model=ProjectStatistics)
async def get_project_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project statistics"""
    repo = ProjectRepository(db)
    stats = await repo.get_statistics()
    return stats