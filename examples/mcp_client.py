#!/usr/bin/env python
"""
Example MCP (Model Context Protocol) client
Demonstrates direct MCP protocol communication
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional


class MCPClient:
    """Client for Model Context Protocol communication"""
    
    def __init__(self):
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.request_id = 0
    
    async def connect(self, host: str = "localhost", port: int = 9000):
        """Connect to MCP server"""
        self.reader, self.writer = await asyncio.open_connection(host, port)
        print(f"Connected to MCP server at {host}:{port}")
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            print("Disconnected from MCP server")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict:
        """Send a request to the MCP server"""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        if params:
            request["params"] = params
        
        # Send request
        message = json.dumps(request) + "\n"
        self.writer.write(message.encode())
        await self.writer.drain()
        
        # Read response
        response_data = await self.reader.readline()
        response = json.loads(response_data.decode())
        
        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")
        
        return response.get("result", {})
    
    async def list_tools(self) -> list:
        """List available tools"""
        return await self.send_request("tools/list")
    
    async def call_tool(self, name: str, arguments: Dict = None) -> Any:
        """Call a specific tool"""
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        return await self.send_request("tools/call", params)
    
    async def list_resources(self) -> list:
        """List available resources"""
        return await self.send_request("resources/list")
    
    async def read_resource(self, uri: str) -> Any:
        """Read a specific resource"""
        return await self.send_request("resources/read", {"uri": uri})
    
    async def list_prompts(self) -> list:
        """List available prompts"""
        return await self.send_request("prompts/list")
    
    async def get_prompt(self, name: str, arguments: Dict = None) -> str:
        """Get a specific prompt"""
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        return await self.send_request("prompts/get", params)


async def main():
    """Example MCP client usage"""
    
    client = MCPClient()
    
    try:
        # Connect to MCP server
        print("MCP Client Example")
        print("=" * 50)
        print("\nConnecting to MCP server...")
        await client.connect()
        
        # Step 1: List available tools
        print("\n1. Available Tools:")
        print("-" * 30)
        tools = await client.list_tools()
        
        if isinstance(tools, dict) and "tools" in tools:
            tools = tools["tools"]
        
        for tool in tools:
            print(f"  • {tool.get('name', 'Unknown')}")
            if tool.get('description'):
                print(f"    {tool['description']}")
            if tool.get('inputSchema'):
                print(f"    Parameters: {list(tool['inputSchema'].get('properties', {}).keys())}")
        
        # Step 2: Call example tools
        print("\n2. Tool Demonstrations:")
        print("-" * 30)
        
        # Example: Search emails
        print("\n  Calling 'search_emails' tool...")
        try:
            result = await client.call_tool("search_emails", {
                "query": "project meeting",
                "limit": 5
            })
            print(f"  Found {len(result.get('emails', []))} emails")
            for email in result.get('emails', [])[:3]:
                print(f"    - {email.get('subject', 'No subject')}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Example: Generate embedding
        print("\n  Calling 'generate_embedding' tool...")
        try:
            result = await client.call_tool("generate_embedding", {
                "text": "Machine learning and artificial intelligence"
            })
            embedding = result.get('embedding', [])
            print(f"  Generated embedding with {len(embedding)} dimensions")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Step 3: List available resources
        print("\n3. Available Resources:")
        print("-" * 30)
        resources = await client.list_resources()
        
        if isinstance(resources, dict) and "resources" in resources:
            resources = resources["resources"]
        
        for resource in resources:
            print(f"  • {resource.get('uri', 'Unknown')}")
            if resource.get('name'):
                print(f"    Name: {resource['name']}")
            if resource.get('description'):
                print(f"    {resource['description']}")
            if resource.get('mimeType'):
                print(f"    Type: {resource['mimeType']}")
        
        # Step 4: Read a resource
        if resources:
            print("\n4. Reading a Resource:")
            print("-" * 30)
            first_resource = resources[0]
            uri = first_resource.get('uri')
            
            if uri:
                print(f"  Reading: {uri}")
                try:
                    content = await client.read_resource(uri)
                    if isinstance(content, dict):
                        print(f"  Content preview: {str(content)[:200]}...")
                    else:
                        print(f"  Content length: {len(str(content))} characters")
                except Exception as e:
                    print(f"  Error: {e}")
        
        # Step 5: List available prompts
        print("\n5. Available Prompts:")
        print("-" * 30)
        prompts = await client.list_prompts()
        
        if isinstance(prompts, dict) and "prompts" in prompts:
            prompts = prompts["prompts"]
        
        for prompt in prompts:
            print(f"  • {prompt.get('name', 'Unknown')}")
            if prompt.get('description'):
                print(f"    {prompt['description']}")
            if prompt.get('arguments'):
                print(f"    Arguments: {prompt['arguments']}")
        
        # Step 6: Get a prompt
        if prompts:
            print("\n6. Getting a Prompt:")
            print("-" * 30)
            first_prompt = prompts[0]
            name = first_prompt.get('name')
            
            if name:
                print(f"  Getting prompt: {name}")
                try:
                    prompt_text = await client.get_prompt(name, {
                        "topic": "machine learning",
                        "style": "technical"
                    })
                    print(f"  Prompt preview: {prompt_text[:200]}...")
                except Exception as e:
                    print(f"  Error: {e}")
        
    except ConnectionError as e:
        print(f"Connection error: {e}")
        print("\nMake sure the MCP server is running:")
        print("  python -m src.mcp.server")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())