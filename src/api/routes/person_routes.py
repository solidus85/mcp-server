"""
Person management API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from src.database.email_repositories import PersonRepository
from src.api.schemas.email_schemas import (
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    PersonSummary,
    PersonStatistics,
    EmailSummary
)
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router
person_router = APIRouter(prefix="/people", tags=["people"])


@person_router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
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
            status_code=status.HTTP_409_CONFLICT,
            detail="Person with this email already exists"
        )
    
    person = await repo.create(**person_data.model_dump())
    await db.commit()
    return person


@person_router.get("/search", response_model=List[PersonResponse])
async def search_people(
    q: Optional[str] = Query(None, description="Search query"),
    organization: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_external: Optional[bool] = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search people with various filters"""
    repo = PersonRepository(db)
    
    # Handle domain search
    if domain:
        people = await repo.search_by_domain(domain, limit=limit)
        return people
    
    # Build filters
    filters = {}
    if q:
        filters["query"] = q
    if organization:
        filters["organization"] = organization
    if is_active is not None:
        filters["is_active"] = is_active
    if is_external is not None:
        filters["is_external"] = is_external
    
    people = await repo.search(filters=filters, limit=limit)
    return people


@person_router.get("/autocomplete")
async def autocomplete_people(
    prefix: str = Query(..., description="Name or email prefix"),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Autocomplete people for UI"""
    repo = PersonRepository(db)
    people = await repo.autocomplete(prefix, limit=limit)
    
    # Format for autocomplete
    results = []
    for person in people:
        results.append({
            "id": str(person.id),
            "email": person.email,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "display_name": person.display_name or f"{person.first_name} {person.last_name}".strip() or person.email
        })
    
    return results


@person_router.get("/by-email/{email}", response_model=PersonResponse)
async def get_person_by_email(
    email: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get person by email address"""
    repo = PersonRepository(db)
    person = await repo.get_by_email(email)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    return person


@person_router.get("/")
async def list_people(
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    is_active: Optional[bool] = Query(None),
    is_external: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all people with pagination"""
    repo = PersonRepository(db)
    
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if is_external is not None:
        filters["is_external"] = is_external
    
    offset = (page - 1) * size
    people = await repo.search(filters=filters, limit=size, offset=offset)
    total = await repo.count_search_results(filters)
    
    return {
        "items": people,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


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


@person_router.put("/{person_id}", response_model=PersonResponse)
async def replace_person(
    person_id: str,
    person_data: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Replace person information (full update)"""
    repo = PersonRepository(db)
    # For PUT, we exclude unset fields to avoid overwriting with None
    # This allows partial updates while preserving existing data
    person = await repo.update(person_id, data=person_data.model_dump(exclude_unset=True))
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    await db.commit()
    await db.refresh(person)  # Refresh to avoid detached instance issues
    return person


@person_router.patch("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: str,
    update_data: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update person information (partial update)"""
    repo = PersonRepository(db)
    person = await repo.update(person_id, data=update_data.model_dump(exclude_unset=True))
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    await db.commit()
    await db.refresh(person)  # Refresh to avoid detached instance issues
    return person


@person_router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
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


class MergeRequest(BaseModel):
    merge_with_id: str


@person_router.post("/{person_id}/merge")
async def merge_people(
    person_id: str,
    merge_request: MergeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Merge two person records"""
    repo = PersonRepository(db)
    
    # Check both persons exist
    primary = await repo.get(person_id)
    if not primary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Primary person not found"
        )
    
    merge = await repo.get(merge_request.merge_with_id)
    if not merge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merge person not found"
        )
    
    success = await repo.merge_persons(person_id, merge_request.merge_with_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to merge persons"
        )
    
    await db.commit()
    return {"message": "People merged successfully"}


@person_router.get("/{person_id}/projects")
async def get_person_projects(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get projects associated with a person"""
    repo = PersonRepository(db)
    
    # Check person exists
    person = await repo.get(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    projects = await repo.get_person_projects(person_id)
    return projects


@person_router.post("/{person_id}/projects/{project_id}")
async def add_person_to_project(
    person_id: str,
    project_id: str,
    person_id_param: Optional[str] = Body(None, embed=True, alias="person_id"),
    role: str = Body("member", embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add person to project"""
    repo = PersonRepository(db)
    
    # Use person_id from body if provided (for compatibility with tests)
    actual_person_id = person_id_param if person_id_param else person_id
    
    success = await repo.add_to_project(actual_person_id, project_id, role)
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


@person_router.get("/{person_id}/emails")
async def get_person_emails(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get emails sent and received by a person"""
    repo = PersonRepository(db)
    
    # Check person exists
    person = await repo.get(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    emails = await repo.get_person_emails(person_id)
    return emails


@person_router.get("/{person_id}/stats", response_model=PersonStatistics)
async def get_person_statistics(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a person"""
    repo = PersonRepository(db)
    
    # Check person exists
    person = await repo.get(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    stats = await repo.get_person_statistics(person_id)
    return PersonStatistics(**stats)