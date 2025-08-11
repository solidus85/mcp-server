import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..utils import chunk_text, hash_text, get_timestamp


def register_builtin_tools(server):
    """Register built-in tools with the MCP server"""
    
    # File operations
    server.register_tool(
        name="read_file",
        description="Read contents of a file",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
            },
            "required": ["path"],
        },
        handler=read_file_handler,
    )
    
    server.register_tool(
        name="write_file",
        description="Write content to a file",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
                "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                "append": {"type": "boolean", "description": "Append to file", "default": False},
            },
            "required": ["path", "content"],
        },
        handler=write_file_handler,
    )
    
    server.register_tool(
        name="list_directory",
        description="List contents of a directory",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the directory"},
                "recursive": {"type": "boolean", "description": "List recursively", "default": False},
                "pattern": {"type": "string", "description": "Glob pattern to filter files", "default": "*"},
            },
            "required": ["path"],
        },
        handler=list_directory_handler,
    )
    
    # Text processing
    server.register_tool(
        name="chunk_text",
        description="Split text into chunks for processing",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to chunk"},
                "chunk_size": {"type": "integer", "description": "Size of each chunk", "default": 1000},
                "overlap": {"type": "integer", "description": "Overlap between chunks", "default": 200},
            },
            "required": ["text"],
        },
        handler=chunk_text_handler,
    )
    
    server.register_tool(
        name="hash_text",
        description="Generate SHA256 hash of text",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to hash"},
            },
            "required": ["text"],
        },
        handler=hash_text_handler,
    )
    
    # System information
    server.register_tool(
        name="get_system_info",
        description="Get system information",
        input_schema={
            "type": "object",
            "properties": {},
        },
        handler=get_system_info_handler,
    )
    
    server.register_tool(
        name="get_environment_variable",
        description="Get an environment variable value",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Environment variable name"},
                "default": {"type": "string", "description": "Default value if not found"},
            },
            "required": ["name"],
        },
        handler=get_env_var_handler,
    )


# Handler implementations
def read_file_handler(path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """Read file contents"""
    file_path = Path(path)
    
    if not file_path.exists():
        return {"error": f"File not found: {path}"}
    
    if not file_path.is_file():
        return {"error": f"Path is not a file: {path}"}
    
    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
        
        return {
            "path": str(file_path.absolute()),
            "content": content,
            "size": len(content),
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
        }
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}


def write_file_handler(
    path: str,
    content: str,
    encoding: str = "utf-8",
    append: bool = False
) -> Dict[str, Any]:
    """Write content to file"""
    file_path = Path(path)
    
    try:
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = "a" if append else "w"
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        
        return {
            "path": str(file_path.absolute()),
            "size": len(content),
            "appended": append,
            "timestamp": get_timestamp(),
        }
    except Exception as e:
        return {"error": f"Error writing file: {str(e)}"}


def list_directory_handler(
    path: str,
    recursive: bool = False,
    pattern: str = "*"
) -> Dict[str, Any]:
    """List directory contents"""
    dir_path = Path(path)
    
    if not dir_path.exists():
        return {"error": f"Directory not found: {path}"}
    
    if not dir_path.is_dir():
        return {"error": f"Path is not a directory: {path}"}
    
    try:
        files = []
        directories = []
        
        if recursive:
            items = dir_path.rglob(pattern)
        else:
            items = dir_path.glob(pattern)
        
        for item in items:
            info = {
                "name": item.name,
                "path": str(item.relative_to(dir_path)),
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
            }
            
            if item.is_file():
                files.append(info)
            elif item.is_dir():
                directories.append(info)
        
        return {
            "path": str(dir_path.absolute()),
            "files": files,
            "directories": directories,
            "total_files": len(files),
            "total_directories": len(directories),
        }
    except Exception as e:
        return {"error": f"Error listing directory: {str(e)}"}


def chunk_text_handler(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> Dict[str, Any]:
    """Split text into chunks"""
    chunks = chunk_text(text, chunk_size, overlap)
    
    return {
        "total_chunks": len(chunks),
        "chunk_size": chunk_size,
        "overlap": overlap,
        "chunks": [
            {
                "index": i,
                "content": chunk,
                "length": len(chunk),
            }
            for i, chunk in enumerate(chunks)
        ],
    }


def hash_text_handler(text: str) -> Dict[str, Any]:
    """Generate hash of text"""
    return {
        "hash": hash_text(text),
        "algorithm": "sha256",
        "text_length": len(text),
    }


def get_system_info_handler() -> Dict[str, Any]:
    """Get system information"""
    import platform
    import psutil
    
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        },
        "cpu": {
            "count": psutil.cpu_count(),
            "percent": psutil.cpu_percent(interval=1),
        },
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total": psutil.disk_usage("/").total,
            "used": psutil.disk_usage("/").used,
            "free": psutil.disk_usage("/").free,
            "percent": psutil.disk_usage("/").percent,
        },
        "timestamp": get_timestamp(),
    }


def get_env_var_handler(name: str, default: Optional[str] = None) -> Dict[str, Any]:
    """Get environment variable value"""
    value = os.environ.get(name, default)
    
    return {
        "name": name,
        "value": value,
        "exists": name in os.environ,
        "default_used": value == default and name not in os.environ,
    }