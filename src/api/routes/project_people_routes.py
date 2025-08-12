"""
Project people management API endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.email_repositories import PersonRepository
from src.api.schemas.email_schemas import BulkPersonProjectAssign
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router (without prefix - will be added by main router)
project_people_router = APIRouter(tags=["project-people"])


@project_people_router.post("/{project_id}/people", status_code=status.HTTP_201_CREATED)
async def add_person_to_project(
    project_id: str,
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a person to a project"""
    person_repo = PersonRepository(db)
    person_id = data.get("person_id")
    role = data.get("role", "member")
    
    success = await person_repo.add_to_project(person_id, project_id, role)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add person to project"
        )
    
    await db.commit()
    return {"message": "Person added to project"}


@project_people_router.delete("/{project_id}/people/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_person_from_project(
    project_id: str,
    person_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a person from a project"""
    person_repo = PersonRepository(db)
    success = await person_repo.remove_from_project(person_id, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person or project not found"
        )
    
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@project_people_router.get("/{project_id}/people")
async def list_project_people(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all people in a project"""
    person_repo = PersonRepository(db)
    people = await person_repo.get_by_project(project_id)
    
    # Format response with role information
    result = []
    for person in people:
        # Get role from junction table if available
        role = "member"  # Default role
        for project in person.projects:
            if str(project.id) == project_id:
                # Check if there's a role attribute
                role = getattr(project, 'role', 'member')
                break
        
        result.append({
            "id": str(person.id),
            "email": person.email,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "full_name": person.full_name,
            "organization": person.organization,
            "role": role
        })
    
    return result


@project_people_router.post("/bulk-assign-people")
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