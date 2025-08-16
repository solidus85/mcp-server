"""
MCP (Model Context Protocol) tools and resources API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..base_schemas import (
    ToolExecutionRequest, ToolExecutionResponse, ToolListResponse, ToolInfo,
    ResourceListResponse, ResourceReadResponse, ResourceInfo,
)
from ..dependencies import (
    get_mcp_server, check_rate_limit, get_optional_user,
)
from ...utils import Timer


# Create routers
tools_router = APIRouter(prefix="/tools", tags=["Tools"])
resources_router = APIRouter(prefix="/resources", tags=["Resources"])


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
                uri=str(res.uri),
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