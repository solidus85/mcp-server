import json
from pathlib import Path
from typing import Dict, Any

from ..config import settings
from ..utils import get_timestamp


def register_builtin_resources(server):
    """Register built-in resources with the MCP server"""
    
    # Server information resource
    server.register_resource(
        uri="mcp://server/info",
        name="Server Information",
        description="Information about the MCP server",
        mime_type="application/json",
        handler=server_info_handler,
    )
    
    # Configuration resource
    server.register_resource(
        uri="mcp://server/config",
        name="Server Configuration",
        description="Current server configuration (non-sensitive)",
        mime_type="application/json",
        handler=config_handler,
    )
    
    # Health check resource
    server.register_resource(
        uri="mcp://server/health",
        name="Health Status",
        description="Server health and status information",
        mime_type="application/json",
        handler=health_handler,
    )
    
    # Documentation resource
    server.register_resource(
        uri="mcp://server/docs",
        name="API Documentation",
        description="Server API documentation",
        mime_type="text/markdown",
        handler=docs_handler,
    )
    
    # Examples resource
    server.register_resource(
        uri="mcp://server/examples",
        name="Usage Examples",
        description="Example usage of server tools and resources",
        mime_type="application/json",
        handler=examples_handler,
    )


# Handler implementations
def server_info_handler() -> str:
    """Get server information"""
    info = {
        "name": "MCP Server",
        "version": "0.1.0",
        "description": "MCP server with vector database and LLM integration",
        "capabilities": {
            "tools": True,
            "resources": True,
            "vector_search": True,
            "llm_integration": True,
            "api_endpoints": True,
        },
        "timestamp": get_timestamp(),
    }
    return json.dumps(info, indent=2)


def config_handler() -> str:
    """Get non-sensitive configuration"""
    config = {
        "server": {
            "host": settings.mcp_server_host,
            "port": settings.mcp_server_port,
            "debug": settings.debug,
            "log_level": settings.log_level,
        },
        "api": {
            "prefix": settings.api_prefix,
            "rate_limit": settings.api_rate_limit,
            "rate_limit_period": settings.api_rate_limit_period,
        },
        "vector_db": {
            "collection_name": settings.chroma_collection_name,
            "embedding_model": settings.embedding_model,
        },
        "llm": {
            "default_provider": settings.default_llm_provider,
            "default_model": settings.default_model,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
        },
        "monitoring": {
            "metrics_enabled": settings.enable_metrics,
            "metrics_port": settings.metrics_port,
        },
    }
    return json.dumps(config, indent=2)


def health_handler() -> str:
    """Get health status"""
    import psutil
    
    health = {
        "status": "healthy",
        "timestamp": get_timestamp(),
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        },
        "services": {
            "mcp_server": "running",
            "vector_db": check_vector_db_status(),
            "api": "ready",
        },
    }
    return json.dumps(health, indent=2)


def docs_handler() -> str:
    """Get API documentation"""
    docs = """# MCP Server API Documentation

## Overview
This MCP server provides tools and resources for vector database operations,
LLM integration, and data processing.

## Available Tools

### File Operations
- **read_file**: Read contents of a file
- **write_file**: Write content to a file
- **list_directory**: List contents of a directory

### Text Processing
- **chunk_text**: Split text into chunks for processing
- **hash_text**: Generate SHA256 hash of text

### System Information
- **get_system_info**: Get system information
- **get_environment_variable**: Get environment variable value

### Vector Operations (when enabled)
- **embed_text**: Generate embeddings for text
- **search_vectors**: Search for similar vectors
- **store_document**: Store document in vector database

### LLM Operations (when enabled)
- **generate_text**: Generate text using LLM
- **analyze_text**: Analyze text using LLM
- **summarize_text**: Summarize text using LLM

## Available Resources

### System Resources
- `mcp://server/info`: Server information
- `mcp://server/config`: Server configuration
- `mcp://server/health`: Health status
- `mcp://server/docs`: This documentation
- `mcp://server/examples`: Usage examples

### Data Resources
- `file://path/to/file`: Access local files
- `vector://collection/document`: Access vector database documents

## API Endpoints

### REST API
- `GET /api/v1/health`: Health check
- `GET /api/v1/tools`: List available tools
- `POST /api/v1/tools/{name}/execute`: Execute a tool
- `GET /api/v1/resources`: List available resources
- `GET /api/v1/resources/{uri}`: Read a resource

### Vector Operations
- `POST /api/v1/vectors/embed`: Generate embeddings
- `POST /api/v1/vectors/search`: Search vectors
- `POST /api/v1/vectors/store`: Store document

### LLM Operations
- `POST /api/v1/llm/generate`: Generate text
- `POST /api/v1/llm/analyze`: Analyze text
- `POST /api/v1/llm/summarize`: Summarize text

## Authentication
API endpoints support JWT authentication. Include the token in the
Authorization header: `Bearer <token>`

## Rate Limiting
API endpoints are rate limited based on configuration. Default is 100
requests per 60 seconds.

## Error Responses
Errors are returned in JSON format:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

## WebSocket Support
Real-time updates are available via WebSocket at `/ws`
"""
    return docs


def examples_handler() -> str:
    """Get usage examples"""
    examples = {
        "tools": {
            "read_file": {
                "description": "Read a text file",
                "arguments": {
                    "path": "/path/to/file.txt",
                    "encoding": "utf-8"
                },
            },
            "chunk_text": {
                "description": "Split text into chunks",
                "arguments": {
                    "text": "Long text to be chunked...",
                    "chunk_size": 1000,
                    "overlap": 200,
                },
            },
            "get_system_info": {
                "description": "Get system information",
                "arguments": {},
            },
        },
        "resources": {
            "server_info": {
                "uri": "mcp://server/info",
                "description": "Get server information",
            },
            "health_check": {
                "uri": "mcp://server/health",
                "description": "Check server health",
            },
        },
        "api": {
            "execute_tool": {
                "method": "POST",
                "endpoint": "/api/v1/tools/read_file/execute",
                "body": {
                    "arguments": {
                        "path": "/path/to/file.txt"
                    }
                },
            },
            "search_vectors": {
                "method": "POST",
                "endpoint": "/api/v1/vectors/search",
                "body": {
                    "query": "search query",
                    "limit": 10,
                },
            },
        },
    }
    return json.dumps(examples, indent=2)


def check_vector_db_status() -> str:
    """Check if vector database is operational"""
    try:
        # Check if ChromaDB directory exists
        if settings.chroma_persist_directory.exists():
            return "connected"
        return "not_initialized"
    except Exception:
        return "error"