#!/bin/bash
# Update API documentation

echo "📚 Updating API Documentation..."
echo "================================"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Export OpenAPI schema
echo "→ Exporting OpenAPI schema..."
python scripts/export_openapi.py

echo ""

# Generate markdown documentation
echo "→ Generating markdown documentation..."
python scripts/generate_api_docs.py

echo ""
echo "✅ Documentation update complete!"
echo ""
echo "📁 Generated files:"
echo "   - docs/openapi.json"
echo "   - docs/openapi.yaml"
echo "   - docs/API_REFERENCE.md"
echo "   - docs/README.md"
echo ""
echo "🌐 View interactive docs at:"
echo "   - http://localhost:8000/docs (Swagger UI)"
echo "   - http://localhost:8000/redoc (ReDoc)"