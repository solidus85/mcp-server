from datetime import datetime, UTC
from typing import Optional, List, Dict, Any
from uuid import uuid4
import json

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Table
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from .connection import Base


# Association tables for many-to-many relationships
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class User(Base, TimestampMixin):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Profile information
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    preferences: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )
    api_keys: Mapped[List["ApiKey"]] = relationship(
        "ApiKey",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    queries: Mapped[List["Query"]] = relationship(
        "Query",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Role(Base, TimestampMixin):
    """Role model for role-based access control"""
    __tablename__ = "roles"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )


class ApiKey(Base, TimestampMixin):
    """API key model for authentication"""
    __tablename__ = "api_keys"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    
    @hybrid_property
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at


class Document(Base, TimestampMixin):
    """Document model for tracking documents in vector store"""
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_owner_created", "owner_id", "created_at"),
        Index("ix_documents_collection_type", "collection_name", "document_type"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    
    # Vector store reference
    vector_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    collection_name: Mapped[str] = mapped_column(String(100), default="default")
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Document metadata
    document_type: Mapped[str] = mapped_column(String(50), default="text")
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    doc_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    
    # Processing information
    chunk_count: Mapped[int] = mapped_column(Integer, default=1)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    processing_time: Mapped[Optional[float]] = mapped_column(Float)
    
    # Foreign keys
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="documents")
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=document_tags,
        back_populates="documents",
        lazy="selectin"
    )
    queries: Mapped[List["Query"]] = relationship(
        "Query",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class Tag(Base, TimestampMixin):
    """Tag model for categorizing documents"""
    __tablename__ = "tags"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color
    
    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        secondary=document_tags,
        back_populates="tags"
    )


class Tool(Base, TimestampMixin):
    """Custom tool definitions"""
    __tablename__ = "tools"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_schema: Mapped[Dict] = mapped_column(JSON, nullable=False)
    
    # Tool implementation
    handler_type: Mapped[str] = mapped_column(String(50), default="python")  # python, api, shell
    handler_config: Mapped[Dict] = mapped_column(JSON, nullable=False)
    
    # Metadata
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_execution_time: Mapped[Optional[float]] = mapped_column(Float)


class Resource(Base, TimestampMixin):
    """Custom resource definitions"""
    __tablename__ = "resources"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    uri: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="text/plain")
    
    # Resource data
    resource_type: Mapped[str] = mapped_column(String(50), default="static")  # static, dynamic, external
    content: Mapped[Optional[str]] = mapped_column(Text)
    config: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Access statistics
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Query(Base, TimestampMixin):
    """Search query history and analytics"""
    __tablename__ = "queries"
    __table_args__ = (
        Index("ix_queries_user_created", "user_id", "created_at"),
        Index("ix_queries_type_status", "query_type", "status"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_type: Mapped[str] = mapped_column(String(50), default="vector")  # vector, sql, hybrid
    
    # Results
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    relevance_scores: Mapped[Optional[List[float]]] = mapped_column(JSON)
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Metadata
    parameters: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, error, timeout
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Cost tracking
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float)
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="SET NULL")
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="queries")
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="queries")


class AuditLog(Base):
    """Audit log for tracking all operations"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_logs_entity_action", "entity_type", "action"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Action details
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create, read, update, delete, execute
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, document, tool, etc.
    entity_id: Mapped[Optional[str]] = mapped_column(String(36))
    
    # Request information
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # Support IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_id: Mapped[Optional[str]] = mapped_column(String(36))
    
    # Change tracking
    old_values: Mapped[Optional[Dict]] = mapped_column(JSON)
    new_values: Mapped[Optional[Dict]] = mapped_column(JSON)
    
    # Additional context
    audit_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    
    # Foreign keys
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")


class Session(Base, TimestampMixin):
    """User session tracking"""
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_user_active", "user_id", "is_active"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Session information
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    
    @hybrid_property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(UTC) > self.expires_at