#!/usr/bin/env python3
"""
Export OpenAPI schema from FastAPI application

This script extracts the OpenAPI specification from the FastAPI app
and saves it in multiple formats for documentation and client generation.
"""

import json
import yaml
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.app import app


def export_openapi_schema():
    """Export OpenAPI schema in JSON and YAML formats"""
    
    # Get the OpenAPI schema from FastAPI
    openapi_schema = app.openapi()
    
    # Create docs directory if it doesn't exist
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Export as JSON
    json_path = docs_dir / "openapi.json"
    with open(json_path, 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"✅ Exported OpenAPI schema to {json_path}")
    
    # Export as YAML (more readable)
    yaml_path = docs_dir / "openapi.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(openapi_schema, f, default_flow_style=False, sort_keys=False)
    print(f"✅ Exported OpenAPI schema to {yaml_path}")
    
    # Print summary statistics
    paths = openapi_schema.get('paths', {})
    total_endpoints = 0
    methods_count = {}
    
    for path, path_info in paths.items():
        for method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
            if method in path_info:
                total_endpoints += 1
                methods_count[method.upper()] = methods_count.get(method.upper(), 0) + 1
    
    print("\n📊 API Statistics:")
    print(f"   Total endpoints: {total_endpoints}")
    print(f"   HTTP Methods breakdown:")
    for method, count in sorted(methods_count.items()):
        print(f"     - {method}: {count}")
    
    # Group by tags
    tags_count = {}
    for path, path_info in paths.items():
        for method, endpoint_info in path_info.items():
            if isinstance(endpoint_info, dict):
                tags = endpoint_info.get('tags', ['untagged'])
                for tag in tags:
                    tags_count[tag] = tags_count.get(tag, 0) + 1
    
    print(f"\n   Endpoints by tag:")
    for tag, count in sorted(tags_count.items()):
        print(f"     - {tag}: {count}")
    
    return openapi_schema


if __name__ == "__main__":
    print("🚀 Exporting OpenAPI schema from FastAPI application...")
    export_openapi_schema()
    print("\n✨ Export complete! You can now:")
    print("   - View the API documentation at http://localhost:8000/docs (when server is running)")
    print("   - Use docs/openapi.json to generate client libraries")
    print("   - Import docs/openapi.yaml into API testing tools like Postman")