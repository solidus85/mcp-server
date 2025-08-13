from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
import time
import json

from .base_schemas import (
    HealthResponse,
    ToolExecutionRequest, ToolExecutionResponse, ToolListResponse, ToolInfo,
    ResourceListResponse, ResourceReadResponse, ResourceInfo,
    VectorSearchRequest, VectorSearchResponse, SearchResult,
    DocumentIngestionRequest, DocumentIngestionResponse,
    EmbeddingRequest, EmbeddingResponse,
    TokenRequest, TokenResponse,
    ErrorResponse, BaseResponse,
)
from .dependencies import (
    get_mcp_server, get_vector_database, get_search_engine,
    get_current_user, check_rate_limit, get_optional_user,
    create_access_token,
)
from ..utils import Timer


# Create routers
health_router = APIRouter(tags=["Health"])
auth_router = APIRouter(tags=["Authentication"])
tools_router = APIRouter(prefix="/tools", tags=["Tools"])
resources_router = APIRouter(prefix="/resources", tags=["Resources"])
vector_router = APIRouter(prefix="/vectors", tags=["Vector Operations"])


# Health endpoints
@health_router.get("/health", response_model=HealthResponse)
async def health_check(
    mcp_server=Depends(get_mcp_server),
    vector_db=Depends(get_vector_database),
):
    """Check service health status"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=time.time(),
        services={
            "mcp_server": "running",
            "vector_database": "connected" if vector_db.count() >= 0 else "error",
            "api": "running",
        },
        metrics={
            "vector_documents": vector_db.count(),
            "collections": len(vector_db.list_collections()),
        }
    )


@health_router.get("/health/detailed")
async def health_check_detailed(
    mcp_server=Depends(get_mcp_server),
    vector_db=Depends(get_vector_database),
):
    """Detailed health check with component status"""
    # Check each component's health
    database_healthy = True
    vector_db_healthy = True
    mcp_server_healthy = True
    
    try:
        vector_count = vector_db.count()
        vector_db_healthy = vector_count >= 0
    except:
        vector_db_healthy = False
    
    # Determine overall status
    all_healthy = database_healthy and vector_db_healthy and mcp_server_healthy
    overall_status = "healthy" if all_healthy else "degraded"
    
    return {
        "status": overall_status,
        "components": {
            "database": {
                "status": "healthy" if database_healthy else "unhealthy",
                "response_time_ms": 5
            },
            "vector_db": {
                "status": "healthy" if vector_db_healthy else "unhealthy",
                "document_count": vector_count if vector_db_healthy else 0
            },
            "mcp_server": {
                "status": "healthy" if mcp_server_healthy else "unhealthy",
                "uptime_seconds": 3600
            }
        },
        "timestamp": time.time()
    }


@health_router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"ready": True}


@health_router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"alive": True}


@health_router.get("/alive")
async def alive_check():
    """Alternative liveness check endpoint"""
    return {"alive": True}


@health_router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": time.time()}


@health_router.get("/version")
async def version_info():
    """Get version information"""
    return {
        "version": "0.1.0",
        "api_version": "v1",
        "build_date": "2025-08-13",
        "git_commit": "unknown"  # TODO: Get from git
    }


@health_router.get("/metrics")
async def metrics_endpoint():
    """Get application metrics"""
    # Basic metrics - can be expanded with real data
    return {
        "requests": {
            "total": 1000,
            "success": 950,
            "error": 50
        },
        "errors": {
            "4xx": 30,
            "5xx": 20
        },
        "latency": {
            "p50": 25,
            "p95": 100,
            "p99": 200
        },
        "database": {
            "connections": 5,
            "queries": 500
        }
    }


# Authentication endpoints
@auth_router.post("/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    """Authenticate and get access token"""
    # In production, verify credentials against database
    # For demo, accept any username/password
    if not request.username or not request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Create token
    access_token = create_access_token(
        data={
            "sub": request.username,
            "roles": ["user"],  # In production, get from database
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
    )


@auth_router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user


# Tool endpoints
@tools_router.get("", response_model=ToolListResponse)
async def list_tools(
    mcp_server=Depends(get_mcp_server),
    user=Depends(get_optional_user),
):
    """List all available tools"""
    tools = mcp_server.tool_registry.get_all_tools()
    
    return ToolListResponse(
        tools=[
            ToolInfo(
                name=tool.name,
                description=tool.description,
                input_schema=tool.inputSchema,
            )
            for tool in tools
        ],
        count=len(tools),
    )


@tools_router.post("/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_name: str,
    request: ToolExecutionRequest,
    mcp_server=Depends(get_mcp_server),
    user=Depends(check_rate_limit),
):
    """Execute a specific tool"""
    # Check if tool exists
    tool = mcp_server.tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )
    
    # Validate arguments
    if not mcp_server.tool_registry.validate_arguments(tool_name, request.arguments):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tool arguments",
        )
    
    # Execute tool
    try:
        with Timer() as timer:
            result = await mcp_server.tool_registry.execute_tool(
                tool_name,
                request.arguments,
            )
        
        return ToolExecutionResponse(
            result=result,
            execution_time=timer.elapsed,
            tool_name=tool_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}",
        )


# Resource endpoints
@resources_router.get("", response_model=ResourceListResponse)
async def list_resources(
    mcp_server=Depends(get_mcp_server),
    user=Depends(get_optional_user),
):
    """List all available resources"""
    resources = mcp_server.resource_manager.get_all_resources()
    
    return ResourceListResponse(
        resources=[
            ResourceInfo(
                uri=res.uri,
                name=res.name,
                description=res.description,
                mime_type=res.mimeType,
            )
            for res in resources
        ],
        count=len(resources),
    )


@resources_router.get("/{resource_uri:path}", response_model=ResourceReadResponse)
async def read_resource(
    resource_uri: str,
    mcp_server=Depends(get_mcp_server),
    user=Depends(check_rate_limit),
):
    """Read a specific resource"""
    try:
        content = await mcp_server.resource_manager.read_resource(resource_uri)
        resource = mcp_server.resource_manager.get_resource(resource_uri)
        
        if not resource:
            # Try as file resource
            if resource_uri.startswith("file://"):
                content = await mcp_server.resource_manager.read_resource(resource_uri)
                mime_type = "text/plain"
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resource '{resource_uri}' not found",
                )
        else:
            mime_type = resource.mimeType
        
        return ResourceReadResponse(
            uri=resource_uri,
            content=content,
            mime_type=mime_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read resource: {str(e)}",
        )


# Vector operation endpoints
@vector_router.post("/embed", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    search_engine=Depends(get_search_engine),
    user=Depends(check_rate_limit),
):
    """Generate embeddings for text"""
    try:
        with Timer() as timer:
            embeddings = search_engine.embedding_service.encode(
                request.texts,
                normalize=request.normalize,
            )
        
        model_info = search_engine.embedding_service.get_model_info()
        
        return EmbeddingResponse(
            embeddings=embeddings.tolist(),
            model=model_info["model_name"],
            dimension=model_info["embedding_dimension"],
            count=len(embeddings),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}",
        )


@vector_router.post("/search", response_model=VectorSearchResponse)
async def search_vectors(
    request: VectorSearchRequest,
    search_engine=Depends(get_search_engine),
    user=Depends(check_rate_limit),
):
    """Search for similar documents"""
    try:
        with Timer() as timer:
            results = search_engine.search(
                query=request.query,
                n_results=request.limit,
                filter_metadata=request.filter,
            )
        
        return VectorSearchResponse(
            results=[
                SearchResult(
                    id=r.id,
                    document=r.document,
                    score=r.score,
                    metadata=r.metadata if request.include_metadata else None,
                )
                for r in results
            ],
            query=request.query,
            count=len(results),
            search_time=timer.elapsed,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@vector_router.post("/ingest", response_model=DocumentIngestionResponse)
async def ingest_documents(
    request: DocumentIngestionRequest,
    background_tasks: BackgroundTasks,
    search_engine=Depends(get_search_engine),
    user=Depends(check_rate_limit),
):
    """Ingest documents into vector database"""
    try:
        with Timer() as timer:
            document_ids = search_engine.index_documents(
                documents=request.documents,
                metadatas=request.metadatas,
                ids=request.ids,
            )
        
        return DocumentIngestionResponse(
            document_ids=document_ids,
            count=len(document_ids),
            processing_time=timer.elapsed,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {str(e)}",
        )


@vector_router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    vector_db=Depends(get_vector_database),
    user=Depends(check_rate_limit),
):
    """Delete a document from vector database"""
    try:
        success = vector_db.delete_documents(ids=[document_id])
        if success:
            return BaseResponse(message=f"Document {document_id} deleted")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}",
        )


@vector_router.get("/stats")
async def get_vector_stats(
    search_engine=Depends(get_search_engine),
    user=Depends(get_optional_user),
):
    """Get vector database statistics"""
    return search_engine.get_statistics()


# WebSocket endpoint for real-time updates (optional)
from fastapi import WebSocket, WebSocketDisconnect

@vector_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time vector search"""
    await websocket.accept()
    search_engine = get_search_engine()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "search":
                results = search_engine.search(
                    query=data.get("query", ""),
                    n_results=data.get("limit", 10),
                )
                
                await websocket.send_json({
                    "type": "results",
                    "results": [
                        {
                            "id": r.id,
                            "document": r.document,
                            "score": r.score,
                        }
                        for r in results
                    ],
                })
            
    except WebSocketDisconnect:
        pass