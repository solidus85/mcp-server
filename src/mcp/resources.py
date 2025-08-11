import asyncio
from typing import Any, Callable, Dict, List, Optional
from mcp.types import Resource
import logging
from pathlib import Path
import mimetypes

from ..utils import setup_logging


class ResourceManager:
    """Manager for MCP resources"""

    def __init__(self):
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Callable] = {}
        self.logger = setup_logging("ResourceManager")

    def register_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str,
        handler: Callable,
    ) -> None:
        """Register a new resource"""
        if uri in self.resources:
            raise ValueError(f"Resource '{uri}' is already registered")

        if not callable(handler):
            raise TypeError(f"Handler for resource '{uri}' must be callable")

        self.resources[uri] = {
            "uri": uri,
            "name": name,
            "description": description,
            "mimeType": mime_type,
        }
        self.handlers[uri] = handler
        self.logger.info(f"Registered resource: {uri}")

    def unregister_resource(self, uri: str) -> None:
        """Unregister a resource"""
        if uri not in self.resources:
            raise ValueError(f"Resource '{uri}' is not registered")

        del self.resources[uri]
        del self.handlers[uri]
        self.logger.info(f"Unregistered resource: {uri}")

    def get_resource(self, uri: str) -> Optional[Resource]:
        """Get a specific resource definition"""
        if uri not in self.resources:
            return None

        res = self.resources[uri]
        return Resource(
            uri=res["uri"],
            name=res["name"],
            description=res["description"],
            mimeType=res["mimeType"],
        )

    def get_all_resources(self) -> List[Resource]:
        """Get all registered resources"""
        return [
            Resource(
                uri=res["uri"],
                name=res["name"],
                description=res["description"],
                mimeType=res["mimeType"],
            )
            for res in self.resources.values()
        ]

    async def read_resource(self, uri: str) -> str:
        """Read a resource by URI"""
        if uri not in self.handlers:
            # Try to handle file:// URIs
            if uri.startswith("file://"):
                return await self._read_file_resource(uri)
            raise ValueError(f"Resource '{uri}' is not registered")

        handler = self.handlers[uri]
        
        try:
            if asyncio.iscoroutinefunction(handler):
                content = await handler()
            else:
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(None, handler)
            
            self.logger.info(f"Successfully read resource: {uri}")
            return content
            
        except Exception as e:
            self.logger.error(f"Error reading resource '{uri}': {e}")
            raise

    async def _read_file_resource(self, uri: str) -> str:
        """Read a file resource from disk"""
        # Convert file:// URI to path
        if not uri.startswith("file://"):
            raise ValueError(f"Invalid file URI: {uri}")
        
        path = uri[7:]  # Remove 'file://' prefix
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            raise

    def register_directory(
        self,
        directory: Path,
        base_uri: str = "file://",
        pattern: str = "*",
    ) -> int:
        """Register all files in a directory as resources"""
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory}")
        
        count = 0
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                uri = f"{base_uri}{file_path.absolute()}"
                mime_type, _ = mimetypes.guess_type(str(file_path))
                mime_type = mime_type or "text/plain"
                
                def make_handler(path):
                    def handler():
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read()
                    return handler
                
                self.register_resource(
                    uri=uri,
                    name=file_path.name,
                    description=f"File resource: {file_path.name}",
                    mime_type=mime_type,
                    handler=make_handler(file_path),
                )
                count += 1
        
        self.logger.info(f"Registered {count} file resources from {directory}")
        return count


def create_resource_decorator(manager: ResourceManager):
    """Create a decorator for registering resources"""
    
    def resource(uri: str, name: str, description: str, mime_type: str = "text/plain"):
        def decorator(func: Callable):
            manager.register_resource(uri, name, description, mime_type, func)
            return func
        return decorator
    
    return resource