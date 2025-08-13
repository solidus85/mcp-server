"""
Email CRUD (Create, Read, Update, Delete) API endpoints
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.email_repositories import EmailRepository
from src.api.schemas.email_schemas import (
    EmailUpdate,
    EmailResponse,
    EmailSummary
)
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router (without prefix - will be added by main router)
email_crud_router = APIRouter(tags=["email-crud"])


# List emails (root route)
@email_crud_router.get("/")
async def list_emails(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    project_id: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    is_flagged: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List emails with pagination"""
    repo = EmailRepository(db)
    
    filters = {}
    if project_id:
        filters["project_id"] = project_id
    if is_read is not None:
        filters["is_read"] = is_read
    if is_flagged is not None:
        filters["is_flagged"] = is_flagged
    
    offset = (page - 1) * size
    emails = await repo.search(
        filters=filters,
        limit=size,
        offset=offset
    )
    
    # Count total emails
    total = await repo.count_search_results(filters)
    
    return {
        "items": emails,
        "page": page,
        "size": size,
        "total": total,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


# Search emails - MUST come before /{email_id}
@email_crud_router.get("/search")
async def search_emails_advanced(
    q: Optional[str] = Query(None, description="Search query for subject/body"),
    from_email: Optional[str] = Query(None, alias="from", description="Filter by sender email"),
    to: Optional[str] = Query(None, description="Filter by recipient email"),
    start_date: Optional[datetime] = Query(None, description="Start date for date range"),
    end_date: Optional[datetime] = Query(None, description="End date for date range"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    thread_id: Optional[str] = Query(None, description="Filter by thread ID"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    is_flagged: Optional[bool] = Query(None, description="Filter by flagged status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search emails with various filters"""
    repo = EmailRepository(db)
    
    # Build filters
    filters = {}
    if q:
        filters["query"] = q
    if from_email:
        filters["from_email"] = from_email
    if to:
        filters["to_email"] = to
    if start_date:
        filters["date_from"] = start_date
    if end_date:
        filters["date_to"] = end_date
    if project_id:
        filters["project_id"] = project_id
    if thread_id:
        filters["thread_id"] = thread_id
    if is_read is not None:
        filters["is_read"] = is_read
    if is_flagged is not None:
        filters["is_flagged"] = is_flagged
    
    # Search emails
    emails = await repo.search(
        filters=filters,
        limit=size,
        offset=(page - 1) * size
    )
    
    # Count total results
    total = await repo.count_search_results(filters)
    
    return {
        "results": emails,
        "page": page,
        "size": size,
        "total": total
    }


# Get email by message ID - MUST come before /{email_id}
@email_crud_router.get("/by-message-id/{message_id}", response_model=EmailResponse)
async def get_email_by_message_id(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email by external message ID"""
    repo = EmailRepository(db)
    email = await repo.get_by_email_id(message_id)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    return email


# Get thread emails - MUST come before /{email_id}
@email_crud_router.get("/thread/{thread_id}", response_model=List[EmailSummary])
async def get_thread_emails(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all emails in a thread"""
    repo = EmailRepository(db)
    emails = await repo.get_thread_emails(thread_id)
    return emails


# Get email by ID - This MUST come AFTER all other specific routes
@email_crud_router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email by ID"""
    repo = EmailRepository(db)
    email = await repo.get(email_id)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    return email


# Update email
@email_crud_router.patch("/{email_id}", response_model=EmailResponse)
async def update_email(
    email_id: str,
    update_data: EmailUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update email properties"""
    repo = EmailRepository(db)
    email = await repo.update(email_id, update_data.model_dump(exclude_unset=True))
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    await db.commit()
    # Reload the email with all relationships
    return await repo.get(email_id)


# Delete email
@email_crud_router.delete("/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an email"""
    repo = EmailRepository(db)
    deleted = await repo.delete(email_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    await db.commit()
    # Return None for 204 No Content response
    return None


# Email operations - these can come after /{email_id} since they have more path segments
@email_crud_router.post("/{email_id}/mark-read", response_model=EmailResponse)
async def mark_email_as_read(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an email as read"""
    repo = EmailRepository(db)
    email = await repo.update(email_id, {"is_read": True})
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    await db.commit()
    # Reload the email with all relationships
    return await repo.get(email_id)


@email_crud_router.post("/{email_id}/mark-unread", response_model=EmailResponse)
async def mark_email_as_unread(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an email as unread"""
    repo = EmailRepository(db)
    email = await repo.update(email_id, {"is_read": False})
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    await db.commit()
    # Reload the email with all relationships
    return await repo.get(email_id)


@email_crud_router.post("/{email_id}/flag", response_model=EmailResponse)
async def flag_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Flag an email"""
    repo = EmailRepository(db)
    email = await repo.update(email_id, {"is_flagged": True})
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    await db.commit()
    # Reload the email with all relationships
    return await repo.get(email_id)


@email_crud_router.post("/{email_id}/unflag", response_model=EmailResponse)
async def unflag_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unflag an email"""
    repo = EmailRepository(db)
    email = await repo.update(email_id, {"is_flagged": False})
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    await db.commit()
    # Reload the email with all relationships
    return await repo.get(email_id)


@email_crud_router.post("/{email_id}/assign-project", response_model=EmailResponse)
async def assign_email_to_project(
    email_id: str,
    project_id: str = Body(..., description="Project ID to assign"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign an email to a project"""
    repo = EmailRepository(db)
    email = await repo.update(email_id, {"project_id": project_id})
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    await db.commit()
    # Reload the email with all relationships
    return await repo.get(email_id)