"""
API schema modules
"""

# Import from base_schemas.py file (one level up)
from ..base_schemas import (
    BaseResponse,
    ErrorResponse,
    HealthResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolListResponse,
    ToolInfo,
    ResourceListResponse,
    ResourceReadResponse,
    ResourceInfo,
    VectorSearchRequest,
    VectorSearchResponse,
    SearchResult,
    DocumentIngestionRequest,
    DocumentIngestionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    TokenRequest,
    TokenResponse,
)

# Import from email_schemas.py
from .email_schemas import (
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    EmailCreate,
    EmailIngest,
    EmailUpdate,
    EmailResponse,
)

__all__ = [
    # Base schemas
    "BaseResponse",
    "ErrorResponse",
    "HealthResponse",
    "ToolExecutionRequest",
    "ToolExecutionResponse",
    "ToolListResponse",
    "ToolInfo",
    "ResourceListResponse",
    "ResourceReadResponse",
    "ResourceInfo",
    "VectorSearchRequest",
    "VectorSearchResponse",
    "SearchResult",
    "DocumentIngestionRequest",
    "DocumentIngestionResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "TokenRequest",
    "TokenResponse",
    # Email schemas
    "PersonCreate",
    "PersonUpdate",
    "PersonResponse",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "EmailCreate",
    "EmailIngest",
    "EmailUpdate",
    "EmailResponse",
]