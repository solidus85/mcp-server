"""
Document management routes (protected endpoints for testing)
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.database.document_repositories import DocumentRepository
from src.api.dependencies import get_current_user, require_role
from src.api.routes.base import get_db


# Schemas
class DocumentCreate(BaseModel):
    """Document creation schema"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    tags: List[str] = []


class DocumentResponse(BaseModel):
    """Document response schema"""
    id: str
    title: str
    content: str
    tags: List[str] = []
    owner_id: str
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    """Document list response"""
    items: List[DocumentResponse]
    total: int
    page: int
    size: int


# Create router
document_router = APIRouter(prefix="/documents", tags=["Documents"])


@document_router.get("/", response_model=DocumentList)
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all documents (protected endpoint)"""
    repo = DocumentRepository(db)
    
    # Calculate offset
    offset = (page - 1) * size
    
    # Get documents
    documents = await repo.get_all(skip=offset, limit=size)
    total = await repo.count()
    
    # Convert to response format
    items = []
    for doc in documents:
        items.append(DocumentResponse(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            tags=doc.tags or [],
            owner_id=doc.user_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        ))
    
    return DocumentList(
        items=items,
        total=total,
        page=page,
        size=size
    )


@document_router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new document (protected endpoint)"""
    repo = DocumentRepository(db)
    
    # Get user ID from token
    # In a real app, you'd get this from the database
    user_id = current_user.get("username")  # Using username as ID for simplicity
    
    # Create document
    doc = await repo.create(
        title=document.title,
        content=document.content,
        tags=document.tags,
        user_id=user_id
    )
    
    await db.commit()
    await db.refresh(doc)
    
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        tags=doc.tags or [],
        owner_id=doc.user_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@document_router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific document (protected endpoint)"""
    repo = DocumentRepository(db)
    
    document = await repo.get(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        tags=document.tags or [],
        owner_id=document.user_id,
        created_at=document.created_at,
        updated_at=document.updated_at
    )


@document_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a document (protected endpoint)"""
    repo = DocumentRepository(db)
    
    # Check if document exists
    document = await repo.get(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete document
    await repo.delete(document_id)
    await db.commit()


# Protected resource endpoint for testing
protected_router = APIRouter(prefix="/protected", tags=["Protected"])


@protected_router.get("/resource")
async def get_protected_resource(
    current_user: dict = Depends(get_current_user)
):
    """A protected resource endpoint for testing"""
    return {
        "message": "This is a protected resource",
        "user": current_user["username"],
        "roles": current_user.get("roles", [])
    }


# Admin endpoints
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@admin_router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """List all users (admin only)"""
    from src.database.user_repository import UserRepository
    
    repo = UserRepository(db)
    users = await repo.get_all(limit=100)
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "roles": [role.name for role in user.roles] if user.roles else []
        }
        for user in users
    ]