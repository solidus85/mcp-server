"""
Project CRUD (Create, Read, Update, Delete) API endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.project_repository import ProjectRepository
from src.api.schemas.email_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)
from src.api.dependencies import get_current_user
from src.database.models import User
from .base import get_db

# Create router (without prefix - will be added by main router)
project_crud_router = APIRouter(tags=["project-crud"])


@project_crud_router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
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
            status_code=status.HTTP_409_CONFLICT,
            detail="Project with this name already exists"
        )
    
    project = await repo.create(**project_data.model_dump())
    await db.commit()
    
    # Convert to dict for response
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "email_domains": project.email_domains,
        "is_active": project.is_active,
        "auto_assign": project.auto_assign,
        "project_metadata": project.project_metadata or {},
        "tags": project.tags or [],
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None
    }


@project_crud_router.get("/{project_id}", response_model=ProjectResponse)
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
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "email_domains": project.email_domains,
        "is_active": project.is_active,
        "auto_assign": project.auto_assign,
        "project_metadata": project.project_metadata or {},
        "tags": project.tags or [],
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "people": project.people if hasattr(project, 'people') else [],
        "email_count": email_count
    }
    
    return project_dict


@project_crud_router.get("/")
async def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List projects with pagination"""
    repo = ProjectRepository(db)
    
    offset = (page - 1) * size
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    
    projects = await repo.search(
        filters=filters,
        limit=size,
        offset=offset
    )
    
    # Get total count
    total = await repo.count(filters=filters)
    
    # Format response with pagination metadata
    return {
        "items": projects,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@project_crud_router.put("/{project_id}", response_model=ProjectResponse)
async def replace_project(
    project_id: str,
    update_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Replace/fully update a project"""
    repo = ProjectRepository(db)
    project = await repo.update(project_id, update_data.model_dump(exclude_unset=True))
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    await db.commit()
    await db.refresh(project)
    
    # Add email count
    email_count = await repo.get_email_count(project_id)
    project_dict = {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "email_domains": project.email_domains,
        "is_active": project.is_active,
        "auto_assign": project.auto_assign,
        "project_metadata": project.project_metadata or {},
        "tags": project.tags or [],
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "people": project.people if hasattr(project, 'people') else [],
        "email_count": email_count
    }
    
    return project_dict


@project_crud_router.patch("/{project_id}", response_model=ProjectResponse)
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
    await db.refresh(project)
    
    # Add email count
    email_count = await repo.get_email_count(project_id)
    project_dict = {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "email_domains": project.email_domains,
        "is_active": project.is_active,
        "auto_assign": project.auto_assign,
        "project_metadata": project.project_metadata or {},
        "tags": project.tags or [],
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "people": project.people if hasattr(project, 'people') else [],
        "email_count": email_count
    }
    
    return project_dict


@project_crud_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)