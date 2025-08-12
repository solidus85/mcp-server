"""
Email bulk operations API endpoints
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.email_repositories import EmailRepository
from src.api.schemas.email_schemas import BulkEmailUpdate
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router (without prefix - will be added by main router)
email_bulk_router = APIRouter(tags=["email-bulk"])


@email_bulk_router.post("/bulk-update")
async def bulk_update_emails(
    bulk_update: BulkEmailUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update multiple emails"""
    repo = EmailRepository(db)
    updated_count = 0
    
    for email_id in bulk_update.email_ids:
        email = await repo.update(
            email_id,
            bulk_update.update.model_dump(exclude_unset=True)
        )
        if email:
            updated_count += 1
    
    await db.commit()
    return {"updated": updated_count}


@email_bulk_router.post("/bulk/mark-read")
async def bulk_mark_emails_read(
    data: Dict[str, List[str]],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk mark emails as read"""
    email_ids = data.get("email_ids", [])
    repo = EmailRepository(db)
    updated_count = 0
    
    for email_id in email_ids:
        email = await repo.update(email_id, {"is_read": True})
        if email:
            updated_count += 1
    
    await db.commit()
    return {"updated": updated_count}


@email_bulk_router.post("/bulk/assign-project")
async def bulk_assign_emails_to_project(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk assign emails to a project"""
    email_ids = data.get("email_ids", [])
    project_id = data.get("project_id")
    
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id is required"
        )
    
    repo = EmailRepository(db)
    updated_count = 0
    
    for email_id in email_ids:
        email = await repo.update(email_id, {"project_id": project_id})
        if email:
            updated_count += 1
    
    await db.commit()
    return {"updated": updated_count}


@email_bulk_router.post("/bulk/delete")
async def bulk_delete_emails(
    data: Dict[str, List[str]],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk delete emails"""
    email_ids = data.get("email_ids", [])
    repo = EmailRepository(db)
    deleted_count = 0
    
    for email_id in email_ids:
        deleted = await repo.delete(email_id)
        if deleted:
            deleted_count += 1
    
    await db.commit()
    return {"deleted": deleted_count}