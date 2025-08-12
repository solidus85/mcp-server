from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Table, Enum
)
from .types import JSONType, ArrayType, MutableJSONType, get_mutable_array_type
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from .connection import Base
# Import TimestampMixin definition directly to avoid circular import
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime
from sqlalchemy.sql import func


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


# Enum for recipient types
class RecipientType(str, PyEnum):
    TO = "TO"
    CC = "CC"
    BCC = "BCC"


# Association table for many-to-many relationship between Person and Project
person_projects = Table(
    "person_projects",
    Base.metadata,
    Column("person_id", ForeignKey("people.id", ondelete="CASCADE"), primary_key=True),
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String(50), default="member"),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Index("ix_person_projects_person_project", "person_id", "project_id"),
)


class Person(Base, TimestampMixin):
    """Person model for email participants"""
    __tablename__ = "people"
    __table_args__ = (
        # The email column already has unique=True which creates an index automatically
        Index("ix_people_name", "first_name", "last_name"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    display_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Additional metadata
    organization: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    person_metadata: Mapped[Optional[Dict]] = mapped_column(MutableJSONType, default=dict)
    
    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_external: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        secondary=person_projects,
        back_populates="people",
        lazy="selectin"
    )
    sent_emails: Mapped[List["Email"]] = relationship(
        "Email",
        back_populates="sender",
        foreign_keys="Email.from_person_id",
        cascade="all, delete-orphan"
    )
    email_recipients: Mapped[List["EmailRecipient"]] = relationship(
        "EmailRecipient",
        back_populates="person",
        cascade="all, delete-orphan"
    )
    
    @hybrid_property
    def full_name(self) -> str:
        """Get full name of person"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.display_name:
            return self.display_name
        else:
            return self.email.split("@")[0]
    
    def __repr__(self):
        return f"<Person(id={self.id}, email={self.email})>"


class Project(Base, TimestampMixin):
    """Project model for grouping emails and people"""
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_name", "name"),
        Index("ix_projects_active", "is_active"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # PostgreSQL ARRAY type for multiple email domains
    email_domains: Mapped[Optional[List[str]]] = mapped_column(
        get_mutable_array_type(String),
        default=list,
        comment="List of email domains associated with this project"
    )
    
    # Project settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_assign: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="Automatically assign emails from project domains"
    )
    
    # Additional metadata
    project_metadata: Mapped[Optional[Dict]] = mapped_column(MutableJSONType, default=dict)
    tags: Mapped[Optional[List[str]]] = mapped_column(get_mutable_array_type(String), default=list)
    
    # Relationships
    people: Mapped[List["Person"]] = relationship(
        "Person",
        secondary=person_projects,
        back_populates="projects",
        lazy="selectin"
    )
    emails: Mapped[List["Email"]] = relationship(
        "Email",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    def has_domain(self, email_address: str) -> bool:
        """Check if an email address belongs to this project's domains"""
        if not self.email_domains:
            return False
        domain = email_address.split("@")[-1].lower()
        return domain in [d.lower() for d in self.email_domains]
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"


class Email(Base, TimestampMixin):
    """Email model for storing email messages"""
    __tablename__ = "emails"
    __table_args__ = (
        Index("ix_emails_email_id", "email_id"),
        Index("ix_emails_datetime", "datetime_sent"),
        Index("ix_emails_sender_date", "from_person_id", "datetime_sent"),
        Index("ix_emails_project_date", "project_id", "datetime_sent"),
        Index("ix_emails_thread", "thread_id"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Email identifiers
    email_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    message_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    in_reply_to: Mapped[Optional[str]] = mapped_column(String(255))
    thread_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Email content
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_text: Mapped[Optional[str]] = mapped_column(Text)  # Plain text version
    
    # Metadata
    datetime_sent: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    headers: Mapped[Optional[Dict]] = mapped_column(MutableJSONType, default=dict)
    attachments: Mapped[Optional[List[Dict]]] = mapped_column(JSONType, default=list)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Flags
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Foreign keys
    from_person_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False
    )
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    
    # Relationships
    sender: Mapped["Person"] = relationship(
        "Person",
        back_populates="sent_emails",
        foreign_keys=[from_person_id]
    )
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="emails"
    )
    recipients: Mapped[List["EmailRecipient"]] = relationship(
        "EmailRecipient",
        back_populates="email",
        cascade="all, delete-orphan"
    )
    
    @hybrid_property
    def to_recipients(self) -> List["Person"]:
        """Get TO recipients"""
        return [r.person for r in self.recipients if r.recipient_type == RecipientType.TO]
    
    @hybrid_property
    def cc_recipients(self) -> List["Person"]:
        """Get CC recipients"""
        return [r.person for r in self.recipients if r.recipient_type == RecipientType.CC]
    
    @hybrid_property
    def bcc_recipients(self) -> List["Person"]:
        """Get BCC recipients"""
        return [r.person for r in self.recipients if r.recipient_type == RecipientType.BCC]
    
    def __repr__(self):
        return f"<Email(id={self.id}, subject={self.subject[:50]}...)>"


class EmailRecipient(Base):
    """Junction table for email recipients with additional metadata"""
    __tablename__ = "email_recipients"
    __table_args__ = (
        UniqueConstraint("email_id", "person_id", "recipient_type", name="uq_email_person_type"),
        Index("ix_email_recipients_email", "email_id"),
        Index("ix_email_recipients_person", "person_id"),
    )
    
    # Composite primary key
    email_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("emails.id", ondelete="CASCADE"),
        primary_key=True
    )
    person_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True
    )
    recipient_type: Mapped[RecipientType] = mapped_column(
        Enum(RecipientType),
        primary_key=True
    )
    
    # Additional metadata
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    email: Mapped["Email"] = relationship("Email", back_populates="recipients")
    person: Mapped["Person"] = relationship("Person", back_populates="email_recipients")
    
    def __repr__(self):
        return f"<EmailRecipient(email={self.email_id}, person={self.person_id}, type={self.recipient_type})>"


class EmailThread(Base, TimestampMixin):
    """Email thread/conversation tracking"""
    __tablename__ = "email_threads"
    __table_args__ = (
        Index("ix_email_threads_subject", "subject"),
        Index("ix_email_threads_dates", "first_email_date", "last_email_date"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    thread_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Thread statistics
    email_count: Mapped[int] = mapped_column(Integer, default=1)
    participant_count: Mapped[int] = mapped_column(Integer, default=1)
    first_email_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_email_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Participants list (stored as JSON array of email addresses)
    participants: Mapped[List[str]] = mapped_column(JSONType, default=list)
    
    # Project association
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    
    def __repr__(self):
        return f"<EmailThread(id={self.id}, subject={self.subject[:50]}...)>"