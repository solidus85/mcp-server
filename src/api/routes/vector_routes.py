"""
Vector database and embedding operations API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, WebSocket, WebSocketDisconnect

from ..base_schemas import (
    VectorSearchRequest, VectorSearchResponse, SearchResult,
    DocumentIngestionRequest, DocumentIngestionResponse,
    EmbeddingRequest, EmbeddingResponse,
    BaseResponse,
)
from ..dependencies import (
    get_vector_database, get_search_engine,
    check_rate_limit, get_optional_user,
)
from ...utils import Timer


# Create vector router
vector_router = APIRouter(prefix="/vectors", tags=["Vector Operations"])


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


# WebSocket endpoint for real-time updates
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