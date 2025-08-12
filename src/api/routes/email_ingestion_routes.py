"""
Email ingestion API endpoints
"""

from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.email_repositories import EmailRepository
from src.api.schemas.email_schemas import EmailIngest, EmailResponse
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db
import logging

logger = logging.getLogger(__name__)

# Create router (without prefix - will be added by main router)
email_ingestion_router = APIRouter(tags=["email-ingestion"])


@email_ingestion_router.post("/ingest", response_model=EmailResponse)
async def ingest_email(
    email_data: EmailIngest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest a new email into the system"""
    try:
        repo = EmailRepository(db)
        
        # Check if email already exists
        existing = await repo.get_by_email_id(email_data.email_id)
        is_update = existing is not None
        
        # Extract fields from EmailIngest
        email = await repo.ingest_email(
            email_id=email_data.email_id,
            from_email=email_data.from_email,
            to_emails=email_data.to,
            subject=email_data.subject,
            body=email_data.body,
            body_text=email_data.body_text or "",
            datetime_sent=email_data.datetime,
            cc_emails=email_data.cc,
            # Don't pass bcc_emails as it's not a field on the Email model
            message_id=email_data.message_id,
            in_reply_to=email_data.in_reply_to,
            thread_id=email_data.thread_id,
            headers=email_data.headers or {},
            attachments=email_data.attachments or [],
            size_bytes=email_data.size_bytes,
            is_update=is_update
        )
        await db.commit()
        
        # Set appropriate status code
        response.status_code = status.HTTP_200_OK if is_update else status.HTTP_201_CREATED
        
        return email
    except Exception as e:
        logger.error(f"Error ingesting email: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@email_ingestion_router.post("/ingest/bulk", status_code=status.HTTP_201_CREATED)
async def ingest_bulk_emails(
    data: Dict[str, List[EmailIngest]],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk ingest multiple emails"""
    emails_data = data.get("emails", [])
    repo = EmailRepository(db)
    
    results = []
    failed = 0
    ingested = 0
    
    for email_data in emails_data:
        try:
            email = await repo.ingest_email(
                email_id=email_data.email_id,
                from_email=email_data.from_email,
                to_emails=email_data.to,
                subject=email_data.subject,
                body=email_data.body,
                body_text=email_data.body_text or "",
                datetime_sent=email_data.datetime,
                cc_emails=email_data.cc,
                message_id=email_data.message_id,
                in_reply_to=email_data.in_reply_to,
                thread_id=email_data.thread_id,
                headers=email_data.headers or {},
                attachments=email_data.attachments or [],
                size_bytes=email_data.size_bytes
            )
            results.append(email)
            ingested += 1
        except Exception as e:
            logger.error(f"Failed to ingest email {email_data.email_id}: {e}")
            failed += 1
    
    await db.commit()
    
    return {
        "ingested": ingested,
        "failed": failed,
        "results": results
    }