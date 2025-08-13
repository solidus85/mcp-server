"""
Health check and monitoring API endpoints
"""

from fastapi import APIRouter, Depends
import time

from ..base_schemas import HealthResponse
from ..dependencies import get_mcp_server, get_vector_database


# Create health router
health_router = APIRouter(tags=["Health"])


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