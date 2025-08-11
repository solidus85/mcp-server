import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional
from mcp.types import Tool
import logging

from ..utils import setup_logging


class ToolRegistry:
    """Registry for managing MCP tools"""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Callable] = {}
        self.logger = setup_logging("ToolRegistry")

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
    ) -> None:
        """Register a new tool"""
        if name in self.tools:
            raise ValueError(f"Tool '{name}' is already registered")

        # Validate handler is callable
        if not callable(handler):
            raise TypeError(f"Handler for tool '{name}' must be callable")

        # Store tool definition
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self.handlers[name] = handler
        self.logger.info(f"Registered tool: {name}")

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' is not registered")

        del self.tools[name]
        del self.handlers[name]
        self.logger.info(f"Unregistered tool: {name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a specific tool definition"""
        if name not in self.tools:
            return None

        tool_def = self.tools[name]
        return Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            inputSchema=tool_def["inputSchema"],
        )

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return [
            Tool(
                name=tool["name"],
                description=tool["description"],
                inputSchema=tool["inputSchema"],
            )
            for tool in self.tools.values()
        ]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments"""
        if name not in self.handlers:
            raise ValueError(f"Tool '{name}' is not registered")

        handler = self.handlers[name]
        
        try:
            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                # Run sync handler in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, handler, **arguments)
            
            self.logger.info(f"Successfully executed tool: {name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing tool '{name}': {e}")
            raise

    def validate_arguments(self, name: str, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments against schema"""
        if name not in self.tools:
            return False

        schema = self.tools[name]["inputSchema"]
        
        # Check required properties
        required = schema.get("required", [])
        for prop in required:
            if prop not in arguments:
                self.logger.error(f"Missing required argument '{prop}' for tool '{name}'")
                return False

        # Check property types (basic validation)
        properties = schema.get("properties", {})
        for key, value in arguments.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type:
                    if not self._check_type(value, expected_type):
                        self.logger.error(
                            f"Invalid type for argument '{key}' in tool '{name}': "
                            f"expected {expected_type}, got {type(value).__name__}"
                        )
                        return False

        return True

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type"""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        
        expected = type_map.get(expected_type)
        if expected is None:
            return True  # Unknown type, allow
            
        return isinstance(value, expected)


def create_tool_decorator(registry: ToolRegistry):
    """Create a decorator for registering tools"""
    
    def tool(name: str, description: str, input_schema: Dict[str, Any]):
        def decorator(func: Callable):
            registry.register_tool(name, description, input_schema, func)
            return func
        return decorator
    
    return tool