from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import db_manager
from src.database.email_repositories import (
    EmailRepository,
    PersonRepository,
    ProjectRepository
)
from src.api.schemas.email_schemas import (
    # Email schemas
    EmailCreate,
    EmailIngest,
    EmailUpdate,
    EmailResponse,
    EmailSummary,
    EmailSearchParams,
    EmailStatistics,
    BulkEmailUpdate,
    # Person schemas
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    PersonSummary,
    PersonSearchParams,
    # Project schemas
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectSummary,
    ProjectSearchParams,
    ProjectStatistics,
    # Other schemas
    EmailThreadResponse,
    BulkPersonProjectAssign
)
from src.api.dependencies import get_current_user
from src.database.models import User
import logging

logger = logging.getLogger(__name__)

# Create routers
email_router = APIRouter(prefix="/emails", tags=["emails"])
person_router = APIRouter(prefix="/people", tags=["people"])
project_router = APIRouter(prefix="/projects", tags=["projects"])


async def get_db() -> AsyncSession:
    """Get database session"""
    async with db_manager.get_session() as session:
        yield session


# Email Endpoints
@email_router.post("/ingest", response_model=EmailResponse)
async def ingest_email(
    email_data: EmailIngest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest a new email into the system"""
    try:
        repo = EmailRepository(db)
        
        # Convert EmailIngest to dict for repository
        email_dict = email_data.model_dump()
        email_dict["from"] = email_dict.pop("from_email")  # Handle field alias
        email_dict["datetime_sent"] = email_dict.pop("datetime")
        
        email = await repo.ingest_email(email_dict)
        await db.commit()
        
        return email
    except Exception as e:
        logger.error(f"Error ingesting email: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@email_router.get("/{email_id}", response_model=EmailResponse)
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


@email_router.get("/", response_model=List[EmailSummary])
async def search_emails(
    params: EmailSearchParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search emails with filters"""
    repo = EmailRepository(db)
    
    filters = {}
    if params.from_email:
        filters["from_email"] = params.from_email
    if params.to_email:
        filters["to_email"] = params.to_email
    if params.subject_contains:
        filters["subject_contains"] = params.subject_contains
    if params.body_contains:
        filters["body_contains"] = params.body_contains
    if params.project_id:
        filters["project_id"] = params.project_id
    if params.thread_id:
        filters["thread_id"] = params.thread_id
    if params.is_read is not None:
        filters["is_read"] = params.is_read
    if params.is_flagged is not None:
        filters["is_flagged"] = params.is_flagged
    if params.date_from:
        filters["date_from"] = params.date_from
    if params.date_to:
        filters["date_to"] = params.date_to
    
    emails = await repo.search(
        filters=filters,
        limit=params.limit,
        offset=params.offset,
        sort_by=params.sort_by,
        sort_order=params.sort_order
    )
    
    return emails


@email_router.patch("/{email_id}", response_model=EmailResponse)
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
    return email


@email_router.post("/bulk-update")
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


@email_router.delete("/{email_id}")
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
    return {"deleted": True}


@email_router.get("/thread/{thread_id}", response_model=List[EmailSummary])
async def get_thread_emails(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all emails in a thread"""
    repo = EmailRepository(db)
    emails = await repo.get_thread_emails(thread_id)
    return emails


@email_router.get("/statistics/overview", response_model=EmailStatistics)
async def get_email_statistics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email statistics"""
    repo = EmailRepository(db)
    stats = await repo.get_statistics(date_from, date_to)
    return stats


# Person Endpoints
@person_router.post("/", response_model=PersonResponse)
async def create_person(
    person_data: PersonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new person"""
    repo = PersonRepository(db)
    
    # Check if person with email already exists
    existing = await repo.get_by_email(person_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person with this email already exists"
        )
    
    person = await repo.create(person_data.model_dump())
    await db.commit()
    return person


@person_router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get person by ID"""
    repo = PersonRepository(db)
    person = await repo.get(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    return person


@person_router.get("/", response_model=List[PersonSummary])
async def search_people(
    params: PersonSearchParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search people with filters"""
    repo = PersonRepository(db)
    
    filters = {}
    if params.query:
        filters["query"] = params.query
    if params.email:
        filters["email"] = params.email
    if params.organization:
        filters["organization"] = params.organization
    if params.project_id:
        filters["project_id"] = params.project_id
    if params.is_active is not None:
        filters["is_active"] = params.is_active
    if params.is_external is not None:
        filters["is_external"] = params.is_external
    
    people = await repo.search(
        filters=filters,
        limit=params.limit,
        offset=params.offset
    )
    
    return people


@person_router.patch("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: str,
    update_data: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update person information"""
    repo = PersonRepository(db)
    person = await repo.update(person_id, update_data.model_dump(exclude_unset=True))
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    await db.commit()
    return person


@person_router.delete("/{person_id}")
async def delete_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a person"""
    repo = PersonRepository(db)
    deleted = await repo.delete(person_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    await db.commit()
    return {"deleted": True}


@person_router.post("/{person_id}/projects/{project_id}")
async def add_person_to_project(
    person_id: str,
    project_id: str,
    role: str = Query("member"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add person to project"""
    repo = PersonRepository(db)
    success = await repo.add_to_project(person_id, project_id, role)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add person to project"
        )
    await db.commit()
    return {"success": True}


@person_router.delete("/{person_id}/projects/{project_id}")
async def remove_person_from_project(
    person_id: str,
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove person from project"""
    repo = PersonRepository(db)
    success = await repo.remove_from_project(person_id, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove person from project"
        )
    await db.commit()
    return {"success": True}


# Project Endpoints
@project_router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    repo = ProjectRepository(db)
    
    # Check if project with name already exists
    existing = await repo.get_by_name(project_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists"
        )
    
    project = await repo.create(project_data.model_dump())
    await db.commit()
    return project


@project_router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project by ID"""
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Add email count
    email_count = await repo.get_email_count(project_id)
    project_dict = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "email_domains": project.email_domains,
        "is_active": project.is_active,
        "auto_assign": project.auto_assign,
        "project_metadata": project.project_metadata,
        "tags": project.tags,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "people": project.people,
        "email_count": email_count
    }
    
    return project_dict


@project_router.get("/", response_model=List[ProjectSummary])
async def search_projects(
    params: ProjectSearchParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search projects with filters"""
    repo = ProjectRepository(db)
    
    filters = {}
    if params.query:
        filters["query"] = params.query
    if params.name_contains:
        filters["name_contains"] = params.name_contains
    if params.domain:
        filters["domain"] = params.domain
    if params.is_active is not None:
        filters["is_active"] = params.is_active
    if params.has_tag:
        filters["has_tag"] = params.has_tag
    
    projects = await repo.search(
        filters=filters,
        limit=params.limit,
        offset=params.offset
    )
    
    return projects


@project_router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project information"""
    repo = ProjectRepository(db)
    project = await repo.update(project_id, update_data.model_dump(exclude_unset=True))
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    await db.commit()
    
    # Add email count
    email_count = await repo.get_email_count(project_id)
    project_dict = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "email_domains": project.email_domains,
        "is_active": project.is_active,
        "auto_assign": project.auto_assign,
        "project_metadata": project.project_metadata,
        "tags": project.tags,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "people": project.people,
        "email_count": email_count
    }
    
    return project_dict


@project_router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project"""
    repo = ProjectRepository(db)
    deleted = await repo.delete(project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    await db.commit()
    return {"deleted": True}


@project_router.post("/bulk-assign-people")
async def bulk_assign_people(
    assignment: BulkPersonProjectAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk assign people to a project"""
    person_repo = PersonRepository(db)
    assigned_count = 0
    
    for person_id in assignment.person_ids:
        success = await person_repo.add_to_project(
            person_id,
            assignment.project_id,
            assignment.role
        )
        if success:
            assigned_count += 1
    
    await db.commit()
    return {"assigned": assigned_count}


@project_router.get("/statistics/overview", response_model=ProjectStatistics)
async def get_project_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project statistics"""
    repo = ProjectRepository(db)
    stats = await repo.get_statistics()
    return stats