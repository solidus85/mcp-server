import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent, ImageContent, EmbeddedResource

from ..config import settings
from ..utils import setup_logging, generate_id, get_timestamp
from .tools import ToolRegistry
from .resources import ResourceManager


class MCPServer:
    """Main MCP Server implementation with stdio transport"""

    def __init__(self, name: str = "mcp-server", version: str = "0.1.0"):
        self.name = name
        self.version = version
        self.server = Server(name)
        self.tool_registry = ToolRegistry()
        self.resource_manager = ResourceManager()
        self.logger = setup_logging(
            name=self.name,
            level=settings.log_level,
            log_file=Path("logs") / f"{self.name}.log",
        )
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP protocol handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools"""
            tools = self.tool_registry.get_all_tools()
            self.logger.debug(f"Listing {len(tools)} tools")
            return tools

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Execute a tool with given arguments"""
            self.logger.info(f"Calling tool: {name} with arguments: {arguments}")
            try:
                result = await self.tool_registry.execute_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                self.logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List all available resources"""
            resources = self.resource_manager.get_all_resources()
            self.logger.debug(f"Listing {len(resources)} resources")
            return resources

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a specific resource by URI"""
            self.logger.info(f"Reading resource: {uri}")
            try:
                content = await self.resource_manager.read_resource(uri)
                return content
            except Exception as e:
                self.logger.error(f"Error reading resource {uri}: {e}")
                raise

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
    ):
        """Register a new tool with the server"""
        self.tool_registry.register_tool(name, description, input_schema, handler)
        self.logger.info(f"Registered tool: {name}")

    def register_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str,
        handler: Callable,
    ):
        """Register a new resource with the server"""
        self.resource_manager.register_resource(
            uri, name, description, mime_type, handler
        )
        self.logger.info(f"Registered resource: {uri}")

    async def run(self):
        """Run the MCP server with stdio transport"""
        self.logger.info(f"Starting {self.name} v{self.version}")
        
        # Create necessary directories
        settings.create_directories()
        
        # Set up initialization options
        init_options = InitializationOptions(
            server_name=self.name,
            server_version=self.version,
            capabilities=self.server.get_capabilities(
                notification_options=None,
                experimental_capabilities={},
            ),
        )
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            self.logger.info("MCP server running on stdio transport")
            await self.server.run(
                read_stream,
                write_stream,
                init_options,
            )


async def main():
    """Main entry point for the MCP server"""
    server = MCPServer()
    
    # Register built-in tools
    from .builtin_tools import register_builtin_tools
    register_builtin_tools(server)
    
    # Register built-in resources
    from .builtin_resources import register_builtin_resources
    register_builtin_resources(server)
    
    # Run the server
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())