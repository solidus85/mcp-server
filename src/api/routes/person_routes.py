"""
Person management API endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.email_repositories import PersonRepository
from src.api.schemas.email_schemas import (
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    PersonSummary,
    PersonSearchParams
)
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router
person_router = APIRouter(prefix="/people", tags=["people"])


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