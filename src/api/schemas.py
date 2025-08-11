from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class StatusEnum(str, Enum):
    """API response status"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"


class BaseResponse(BaseModel):
    """Base response model"""
    status: StatusEnum = Field(default=StatusEnum.SUCCESS)
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseResponse):
    """Error response model"""
    status: StatusEnum = Field(default=StatusEnum.ERROR)
    error_code: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]
    metrics: Optional[Dict[str, Any]] = None


# Tool-related schemas
class ToolExecutionRequest(BaseModel):
    """Request to execute a tool"""
    arguments: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[int] = Field(default=30, ge=1, le=300)
    
    class Config:
        json_schema_extra = {
            "example": {
                "arguments": {"path": "/tmp/file.txt", "encoding": "utf-8"},
                "timeout": 30
            }
        }


class ToolExecutionResponse(BaseResponse):
    """Tool execution result"""
    result: Any
    execution_time: float
    tool_name: str


class ToolInfo(BaseModel):
    """Tool information"""
    name: str
    description: str
    input_schema: Dict[str, Any]


class ToolListResponse(BaseResponse):
    """List of available tools"""
    tools: List[ToolInfo]
    count: int


# Resource-related schemas
class ResourceInfo(BaseModel):
    """Resource information"""
    uri: str
    name: str
    description: str
    mime_type: str


class ResourceListResponse(BaseResponse):
    """List of available resources"""
    resources: List[ResourceInfo]
    count: int


class ResourceReadResponse(BaseResponse):
    """Resource content response"""
    uri: str
    content: str
    mime_type: str


# Vector operation schemas
class EmbeddingRequest(BaseModel):
    """Request to generate embeddings"""
    texts: Union[str, List[str]]
    model: Optional[str] = None
    normalize: bool = Field(default=True)
    
    @validator('texts')
    def validate_texts(cls, v):
        if isinstance(v, str):
            return [v]
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "texts": ["Sample text to embed"],
                "normalize": True
            }
        }


class EmbeddingResponse(BaseResponse):
    """Embedding generation result"""
    embeddings: List[List[float]]
    model: str
    dimension: int
    count: int


class VectorSearchRequest(BaseModel):
    """Vector search request"""
    query: str
    limit: int = Field(default=10, ge=1, le=100)
    filter: Optional[Dict[str, Any]] = None
    include_metadata: bool = Field(default=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning algorithms",
                "limit": 10,
                "include_metadata": True
            }
        }


class SearchResult(BaseModel):
    """Individual search result"""
    id: str
    document: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class VectorSearchResponse(BaseResponse):
    """Vector search results"""
    results: List[SearchResult]
    query: str
    count: int
    search_time: float


class DocumentIngestionRequest(BaseModel):
    """Request to ingest documents"""
    documents: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None
    ids: Optional[List[str]] = None
    
    @validator('metadatas')
    def validate_metadatas(cls, v, values):
        if v and 'documents' in values:
            if len(v) != len(values['documents']):
                raise ValueError('metadatas must have same length as documents')
        return v
    
    @validator('ids')
    def validate_ids(cls, v, values):
        if v and 'documents' in values:
            if len(v) != len(values['documents']):
                raise ValueError('ids must have same length as documents')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": ["Document 1 content", "Document 2 content"],
                "metadatas": [{"source": "file1.txt"}, {"source": "file2.txt"}]
            }
        }


class DocumentIngestionResponse(BaseResponse):
    """Document ingestion result"""
    document_ids: List[str]
    count: int
    processing_time: float


# Authentication schemas
class TokenRequest(BaseModel):
    """Token request for authentication"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    """User information"""
    username: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    created_at: datetime


# LLM operation schemas
class LLMGenerateRequest(BaseModel):
    """LLM text generation request"""
    prompt: str
    model: Optional[str] = None
    max_tokens: int = Field(default=1000, ge=1, le=8000)
    temperature: float = Field(default=0.7, ge=0, le=2)
    stream: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain quantum computing in simple terms",
                "max_tokens": 500,
                "temperature": 0.7
            }
        }


class LLMGenerateResponse(BaseResponse):
    """LLM generation result"""
    text: str
    model: str
    tokens_used: int
    generation_time: float


class LLMAnalyzeRequest(BaseModel):
    """LLM analysis request"""
    text: str
    analysis_type: str = Field(default="general")
    model: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Text to analyze",
                "analysis_type": "sentiment"
            }
        }


class LLMAnalyzeResponse(BaseResponse):
    """LLM analysis result"""
    analysis: Dict[str, Any]
    model: str
    analysis_type: str


# Data transformation schemas
class DataTransformRequest(BaseModel):
    """Data transformation request"""
    data: Any
    transform_type: str
    options: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {"key": "value"},
                "transform_type": "json_to_csv"
            }
        }


class DataTransformResponse(BaseResponse):
    """Data transformation result"""
    transformed_data: Any
    transform_type: str
    original_format: str
    output_format: str


# Pagination
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseResponse):
    """Paginated response base"""
    page: int
    page_size: int
    total_pages: int
    total_items: int
    has_next: bool
    has_previous: bool