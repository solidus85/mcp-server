#!/usr/bin/env python3
"""
Generate comprehensive API documentation in Markdown format

This script reads the OpenAPI schema and generates human-readable
markdown documentation with all endpoints, parameters, and examples.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.app import app


def format_path_params(path: str) -> str:
    """Format path parameters for display"""
    # Replace {param} with **{param}** for markdown emphasis
    import re
    return re.sub(r'\{([^}]+)\}', r'**{\1}**', path)


def get_method_badge(method: str) -> str:
    """Get a colored badge for HTTP method"""
    colors = {
        'GET': '🟢',
        'POST': '🔵',
        'PUT': '🟡',
        'PATCH': '🟠',
        'DELETE': '🔴',
        'HEAD': '⚪',
        'OPTIONS': '⚫'
    }
    return f"{colors.get(method.upper(), '⚪')} **{method.upper()}**"


def generate_parameter_table(parameters: List[Dict]) -> str:
    """Generate a markdown table for parameters"""
    if not parameters:
        return ""
    
    table = "\n| Parameter | Type | Required | Description |\n"
    table += "|-----------|------|----------|-------------|\n"
    
    for param in parameters:
        name = param.get('name', '')
        param_type = param.get('schema', {}).get('type', 'string')
        required = "✅" if param.get('required', False) else "❌"
        description = param.get('description', '-')
        
        table += f"| `{name}` | {param_type} | {required} | {description} |\n"
    
    return table


def generate_request_body_info(request_body: Dict) -> str:
    """Generate information about request body"""
    if not request_body:
        return ""
    
    content = request_body.get('content', {})
    if 'application/json' not in content:
        return ""
    
    schema_ref = content['application/json'].get('schema', {})
    
    info = "\n**Request Body:**\n"
    
    if '$ref' in schema_ref:
        schema_name = schema_ref['$ref'].split('/')[-1]
        info += f"- Schema: `{schema_name}`\n"
    
    if request_body.get('required'):
        info += "- Required: ✅\n"
    
    return info


def generate_response_info(responses: Dict) -> str:
    """Generate information about responses"""
    if not responses:
        return ""
    
    info = "\n**Responses:**\n"
    
    for status_code, response_data in sorted(responses.items()):
        description = response_data.get('description', '')
        info += f"- `{status_code}`: {description}\n"
        
        content = response_data.get('content', {})
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            if '$ref' in schema:
                schema_name = schema['$ref'].split('/')[-1]
                info += f"  - Returns: `{schema_name}`\n"
    
    return info


def group_endpoints_by_tag(paths: Dict) -> Dict[str, List]:
    """Group endpoints by their tags"""
    grouped = {}
    
    for path, path_info in paths.items():
        for method, endpoint_info in path_info.items():
            if isinstance(endpoint_info, dict):
                tags = endpoint_info.get('tags', ['Other'])
                for tag in tags:
                    if tag not in grouped:
                        grouped[tag] = []
                    
                    grouped[tag].append({
                        'path': path,
                        'method': method,
                        'info': endpoint_info
                    })
    
    return grouped


def generate_markdown_docs(openapi_schema: Dict) -> str:
    """Generate comprehensive markdown documentation"""
    
    info = openapi_schema.get('info', {})
    paths = openapi_schema.get('paths', {})
    components = openapi_schema.get('components', {})
    
    # Start building the markdown
    md = f"# {info.get('title', 'API Documentation')}\n\n"
    md += f"**Version:** {info.get('version', '1.0.0')}  \n"
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n"
    
    if info.get('description'):
        md += f"{info['description']}\n\n"
    
    # Add base URL information
    servers = openapi_schema.get('servers', [])
    if servers:
        md += "## Base URL\n\n"
        for server in servers:
            md += f"- {server.get('url', 'http://localhost:8000')}\n"
        md += "\n"
    else:
        md += "## Base URL\n\n"
        md += "- http://localhost:8000/api/v1\n\n"
    
    # Table of Contents
    md += "## Table of Contents\n\n"
    grouped = group_endpoints_by_tag(paths)
    
    for tag in sorted(grouped.keys()):
        tag_display = tag.replace('-', ' ').title()
        md += f"- [{tag_display}](#{tag.lower().replace(' ', '-')})\n"
    md += "\n---\n\n"
    
    # Generate documentation for each tag group
    for tag in sorted(grouped.keys()):
        tag_display = tag.replace('-', ' ').title()
        endpoints = grouped[tag]
        
        md += f"## {tag_display}\n\n"
        
        # Sort endpoints by path and method
        endpoints.sort(key=lambda x: (x['path'], x['method']))
        
        for endpoint in endpoints:
            path = endpoint['path']
            method = endpoint['method']
            info = endpoint['info']
            
            # Endpoint header
            md += f"### {get_method_badge(method)} {format_path_params(path)}\n\n"
            
            # Summary and description
            if info.get('summary'):
                md += f"**{info['summary']}**\n\n"
            
            if info.get('description'):
                md += f"{info['description']}\n\n"
            
            # Operation ID
            if info.get('operationId'):
                md += f"**Operation ID:** `{info['operationId']}`\n\n"
            
            # Parameters
            parameters = info.get('parameters', [])
            if parameters:
                md += "**Parameters:**\n"
                md += generate_parameter_table(parameters)
                md += "\n"
            
            # Request body
            request_body = info.get('requestBody')
            if request_body:
                md += generate_request_body_info(request_body)
                md += "\n"
            
            # Responses
            responses = info.get('responses', {})
            if responses:
                md += generate_response_info(responses)
                md += "\n"
            
            # Security requirements
            security = info.get('security', [])
            if security:
                md += "**Authentication Required:** ✅\n\n"
            
            md += "---\n\n"
    
    # Add schemas section
    schemas = components.get('schemas', {})
    if schemas:
        md += "## Schemas\n\n"
        md += "The following data models are used by the API:\n\n"
        
        for schema_name in sorted(schemas.keys()):
            schema = schemas[schema_name]
            md += f"### {schema_name}\n\n"
            
            if schema.get('description'):
                md += f"{schema['description']}\n\n"
            
            # Properties table
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            if properties:
                md += "| Property | Type | Required | Description |\n"
                md += "|----------|------|----------|-------------|\n"
                
                for prop_name, prop_info in properties.items():
                    prop_type = prop_info.get('type', 'any')
                    if 'format' in prop_info:
                        prop_type += f" ({prop_info['format']})"
                    is_required = "✅" if prop_name in required else "❌"
                    description = prop_info.get('description', '-')
                    
                    md += f"| `{prop_name}` | {prop_type} | {is_required} | {description} |\n"
                
                md += "\n"
    
    return md


def main():
    """Main function to generate API documentation"""
    
    print("📝 Generating API documentation from FastAPI application...")
    
    # Get OpenAPI schema
    openapi_schema = app.openapi()
    
    # Generate markdown
    markdown_docs = generate_markdown_docs(openapi_schema)
    
    # Create docs directory if it doesn't exist
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Save markdown file
    md_path = docs_dir / "API_REFERENCE.md"
    with open(md_path, 'w') as f:
        f.write(markdown_docs)
    
    print(f"✅ Generated API documentation at {md_path}")
    
    # Generate a summary README
    readme_content = f"""# API Documentation

This directory contains the API documentation for the MCP Server.

## Files

- **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete API reference with all endpoints
- **[openapi.json](./openapi.json)** - OpenAPI specification in JSON format
- **[openapi.yaml](./openapi.yaml)** - OpenAPI specification in YAML format

## Quick Links

### Interactive Documentation

When the server is running, you can access interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Statistics

- Total Endpoints: {len(openapi_schema.get('paths', {}))}
- API Version: {openapi_schema.get('info', {}).get('version', '1.0.0')}

### Using the API

1. Most endpoints require authentication via JWT tokens
2. Obtain a token by calling `/api/v1/auth/login`
3. Include the token in the `Authorization: Bearer <token>` header

### Generating Client Libraries

You can use the `openapi.json` file to generate client libraries in various languages:

```bash
# Example using OpenAPI Generator
openapi-generator generate -i docs/openapi.json -g python -o client/python
openapi-generator generate -i docs/openapi.json -g typescript-axios -o client/typescript
```

---

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    readme_path = docs_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Generated README at {readme_path}")
    
    # Print summary
    paths = openapi_schema.get('paths', {})
    total_endpoints = sum(
        1 for path_info in paths.values() 
        for method in path_info.keys() 
        if method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    )
    
    print(f"\n📊 Documentation Summary:")
    print(f"   - Total endpoints documented: {total_endpoints}")
    print(f"   - Markdown file size: {len(markdown_docs):,} characters")
    print(f"   - Schemas documented: {len(openapi_schema.get('components', {}).get('schemas', {}))}")


if __name__ == "__main__":
    main()