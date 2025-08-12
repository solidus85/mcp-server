"""
Email statistics and analytics API endpoints
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.email_repositories import EmailRepository
from src.api.schemas.email_schemas import EmailStatistics
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router (without prefix - will be added by main router)
email_stats_router = APIRouter(tags=["email-stats"])


@email_stats_router.get("/stats")
async def get_email_statistics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall email statistics"""
    repo = EmailRepository(db)
    stats = await repo.get_statistics(date_from, date_to)
    return stats


@email_stats_router.get("/stats/project/{project_id}")
async def get_project_email_statistics(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email statistics for a specific project"""
    repo = EmailRepository(db)
    stats = await repo.get_project_statistics(project_id)
    return stats


@email_stats_router.get("/stats/timeline")
async def get_email_activity_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email activity timeline"""
    repo = EmailRepository(db)
    timeline = await repo.get_activity_timeline(days)
    return {"timeline": timeline}


@email_stats_router.get("/statistics/overview", response_model=EmailStatistics)
async def get_email_statistics_legacy(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email statistics (legacy endpoint for backward compatibility)"""
    repo = EmailRepository(db)
    stats = await repo.get_statistics(date_from, date_to)
    return stats