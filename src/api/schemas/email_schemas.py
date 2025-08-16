from datetime import datetime
from typing import Optional, List, Dict, Any, ForwardRef
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator, computed_field
from enum import Enum


class RecipientTypeSchema(str, Enum):
    TO = "TO"
    CC = "CC"
    BCC = "BCC"


# Person Schemas
class PersonBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    is_external: bool = False
    person_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_external: Optional[bool] = None
    person_metadata: Optional[Dict[str, Any]] = None


class PersonResponse(PersonBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    full_name: str
    created_at: datetime
    updated_at: datetime


class PersonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    is_active: bool = True
    is_external: bool = False
    
    @model_validator(mode='after')
    def compute_full_name(self):
        """Compute full_name if not set"""
        if not self.full_name:
            if self.first_name and self.last_name:
                self.full_name = f"{self.first_name} {self.last_name}"
            elif self.display_name:
                self.full_name = self.display_name
            elif self.email:
                self.full_name = self.email.split("@")[0]
        return self


# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    email_domains: List[str] = Field(default_factory=list)
    is_active: bool = True
    auto_assign: bool = True
    project_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email_domains: Optional[List[str]] = None
    is_active: Optional[bool] = None
    auto_assign: Optional[bool] = None
    project_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime
    people: List[PersonSummary] = []
    email_count: int = Field(default=0)


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    email_domains: List[str] = []


# Email Recipient Schemas
class EmailRecipientCreate(BaseModel):
    email: EmailStr
    recipient_type: RecipientTypeSchema


class EmailRecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    person: PersonSummary
    recipient_type: RecipientTypeSchema


# Email Schemas
class EmailBase(BaseModel):
    email_id: str
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    subject: str
    body: str
    body_text: Optional[str] = None
    datetime_sent: datetime
    headers: Optional[Dict[str, Any]] = Field(default_factory=dict)
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    size_bytes: Optional[int] = None


class EmailCreate(EmailBase):
    from_email: EmailStr
    to_emails: List[EmailStr]
    cc_emails: List[EmailStr] = Field(default_factory=list)
    bcc_emails: List[EmailStr] = Field(default_factory=list)
    project_id: Optional[str] = None


class EmailIngest(BaseModel):
    """Simplified email ingestion schema"""
    to: List[EmailStr]
    from_email: EmailStr = Field(alias="from")
    subject: str
    datetime: datetime
    body: str
    cc: List[EmailStr] = Field(default_factory=list)
    body_text: Optional[str] = None
    email_id: str
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    headers: Optional[Dict[str, Any]] = Field(default_factory=dict)
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    size_bytes: Optional[int] = None


class EmailUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_flagged: Optional[bool] = None
    is_draft: Optional[bool] = None
    project_id: Optional[str] = None


class EmailResponse(EmailBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    is_read: bool
    is_flagged: bool
    is_draft: bool
    from_person_id: str
    project_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sender: PersonSummary
    project: Optional[ProjectSummary] = None
    recipients: List[EmailRecipientResponse] = []
    
    # Computed fields for convenience
    project_name: Optional[str] = None
    has_attachments: bool = False
    attachment_count: int = 0
    from_: Optional[str] = Field(None, alias="from")
    
    @model_validator(mode='after')
    def compute_fields(self):
        """Compute derived fields after model initialization"""
        # Set project_name from project object
        if self.project and hasattr(self.project, 'name'):
            self.project_name = self.project.name
        
        # Set from field from sender
        if self.sender:
            self.from_ = self.sender.email
        
        # Calculate attachment-related fields
        if self.attachments:
            self.has_attachments = len(self.attachments) > 0
            self.attachment_count = len(self.attachments)
        else:
            self.has_attachments = False
            self.attachment_count = 0
        
        return self


class EmailSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email_id: str
    subject: str
    datetime_sent: datetime
    sender: PersonSummary
    is_read: bool
    is_flagged: bool
    thread_id: Optional[str] = None


# Email Thread Schemas
class EmailThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    thread_id: str
    subject: str
    email_count: int
    participant_count: int
    first_email_date: datetime
    last_email_date: datetime
    participants: List[str]
    project_id: Optional[str] = None


# Search and Filter Schemas
class EmailSearchParams(BaseModel):
    query: Optional[str] = None
    from_email: Optional[EmailStr] = None
    to_email: Optional[EmailStr] = None
    subject_contains: Optional[str] = None
    body_contains: Optional[str] = None
    project_id: Optional[str] = None
    thread_id: Optional[str] = None
    is_read: Optional[bool] = None
    is_flagged: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="datetime_sent")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PersonSearchParams(BaseModel):
    query: Optional[str] = None
    email: Optional[EmailStr] = None
    organization: Optional[str] = None
    project_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_external: Optional[bool] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class ProjectSearchParams(BaseModel):
    query: Optional[str] = None
    name_contains: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None
    has_tag: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


# Bulk Operations
class BulkEmailUpdate(BaseModel):
    email_ids: List[str]
    update: EmailUpdate


class BulkPersonProjectAssign(BaseModel):
    person_ids: List[str]
    project_id: str
    role: str = "member"


# Statistics
class EmailStatistics(BaseModel):
    total_emails: int
    unread_count: int
    flagged_count: int
    draft_count: int
    emails_by_project: Dict[str, int]
    emails_by_sender: List[Dict[str, Any]]
    emails_by_date: List[Dict[str, Any]]
    average_response_time: Optional[float] = None


class PersonStatistics(BaseModel):
    emails_sent: int
    emails_received: int
    projects_count: int
    first_email_date: Optional[datetime] = None
    last_email_date: Optional[datetime] = None


# Pagination
from typing import Generic, TypeVar
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: Optional[int] = None


class ProjectStatistics(BaseModel):
    total_projects: int
    active_projects: int
    total_people: int
    emails_per_project: List[Dict[str, Any]]
    most_active_domains: List[Dict[str, Any]]