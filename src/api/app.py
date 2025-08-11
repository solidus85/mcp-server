import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, generate_latest
from pathlib import Path
import uvicorn

from ..config import settings
from ..utils import setup_logging
from .middleware import setup_middleware
from .routes import health_router, auth_router, tools_router, resources_router, vector_router


# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

logger = setup_logging("API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MCP Server API...")
    
    # Create necessary directories
    settings.create_directories()
    
    # Initialize services
    from .dependencies import get_mcp_server, get_vector_database
    mcp_server = get_mcp_server()
    vector_db = get_vector_database()
    
    logger.info(f"MCP Server initialized: {mcp_server.name}")
    logger.info(f"Vector database connected: {vector_db.collection_name}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Server API...")


# Create FastAPI app
app = FastAPI(
    title="MCP Server API",
    description="Model Context Protocol server with vector database and LLM integration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(health_router, prefix="")
app.include_router(auth_router, prefix="/auth")
app.include_router(tools_router, prefix=f"{settings.api_prefix}/tools")
app.include_router(resources_router, prefix=f"{settings.api_prefix}/resources")
app.include_router(vector_router, prefix=f"{settings.api_prefix}/vectors")


# Root endpoint
@app.get("/")
async def root():
    """Redirect to documentation"""
    return RedirectResponse(url="/docs")


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 error handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested URL {request.url.path} was not found",
            "path": request.url.path,
        }
    )


# Additional API info endpoint
@app.get(f"{settings.api_prefix}/info")
async def api_info():
    """Get API information"""
    return {
        "name": "MCP Server API",
        "version": "0.1.0",
        "description": "Model Context Protocol server with vector database and LLM integration",
        "features": {
            "mcp_tools": True,
            "mcp_resources": True,
            "vector_search": True,
            "embeddings": True,
            "authentication": True,
            "rate_limiting": True,
            "websocket": True,
        },
        "endpoints": {
            "documentation": "/docs",
            "openapi": "/openapi.json",
            "health": "/health",
            "metrics": "/metrics",
        },
        "configuration": {
            "api_prefix": settings.api_prefix,
            "rate_limit": settings.api_rate_limit,
            "rate_limit_period": settings.api_rate_limit_period,
        }
    }


def create_app() -> FastAPI:
    """Factory function to create FastAPI app"""
    return app


def main():
    """Main entry point for running the API server"""
    logger.info(f"Starting API server on {settings.mcp_server_host}:{settings.mcp_server_port}")
    
    uvicorn.run(
        "src.api.app:app",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()