#!/bin/bash
# Test MCP Server API endpoints with curl
# Usage: ./curl_test_endpoints.sh

# Configuration
BASE_URL="http://localhost:8000"
API_PREFIX="/api/v1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# JWT token (will be set after login)
TOKEN=""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MCP Server API Test with Curl${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}$1${NC}"
    echo "----------------------------------------"
}

# Function to execute curl and format output
exec_curl() {
    local description="$1"
    shift
    echo -e "${GREEN}→ $description${NC}"
    echo "Command: curl $@"
    curl "$@" 2>/dev/null | python3 -m json.tool 2>/dev/null || curl "$@"
    echo ""
}

# 1. Health Check
print_section "1. HEALTH CHECK"

exec_curl "Check server health" \
    -X GET "$BASE_URL/health"

# 2. API Info
print_section "2. API INFORMATION"

exec_curl "Get API info" \
    -X GET "$BASE_URL$API_PREFIX/info"

# 3. Authentication (if needed)
print_section "3. AUTHENTICATION"

# Register a test user
exec_curl "Register new user" \
    -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }'

# Login to get JWT token
echo -e "${GREEN}→ Login to get JWT token${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "password": "TestPassword123!"
    }')

# Extract token (adjust based on your actual response format)
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}Note: No token received. Continuing without authentication...${NC}"
    AUTH_HEADER=""
else
    echo "Token received: ${TOKEN:0:20}..."
    AUTH_HEADER="Authorization: Bearer $TOKEN"
fi

# 4. Project Management
print_section "4. PROJECT MANAGEMENT"

# Create a project
exec_curl "Create a new project" \
    -X POST "$BASE_URL$API_PREFIX/projects/" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "name": "Acme Corporation",
        "description": "Main client project",
        "email_domains": ["acme.com", "acme.org"],
        "is_active": true,
        "auto_assign": true,
        "tags": ["client", "important"]
    }'

# List projects
exec_curl "List all projects" \
    -X GET "$BASE_URL$API_PREFIX/projects/" \
    -H "$AUTH_HEADER"

# Get specific project (assuming ID 1 exists)
exec_curl "Get project details" \
    -X GET "$BASE_URL$API_PREFIX/projects/1" \
    -H "$AUTH_HEADER"

# 5. People Management
print_section "5. PEOPLE MANAGEMENT"

# Create a person
exec_curl "Create a new person" \
    -X POST "$BASE_URL$API_PREFIX/people/" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "email": "john.doe@acme.com",
        "first_name": "John",
        "last_name": "Doe",
        "organization": "Acme Corporation",
        "phone": "+1-555-0123"
    }'

# Search people
exec_curl "Search people" \
    -X GET "$BASE_URL$API_PREFIX/people/?query=john" \
    -H "$AUTH_HEADER"

# 6. Email Ingestion
print_section "6. EMAIL INGESTION"

# Ingest an email
exec_curl "Ingest a new email" \
    -X POST "$BASE_URL$API_PREFIX/emails/ingest" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "email_id": "msg-001",
        "from": "alice@ourcompany.com",
        "to": ["john.doe@acme.com", "jane.smith@acme.com"],
        "cc": ["bob@ourcompany.com"],
        "subject": "Project Update - Q4 Planning",
        "body": "<html><body><p>Hi team,</p><p>Here is the project update for Q4 planning.</p></body></html>",
        "body_text": "Hi team,\n\nHere is the project update for Q4 planning.",
        "datetime": "2024-01-15T10:30:00Z",
        "message_id": "<msg-001@ourcompany.com>",
        "headers": {
            "X-Priority": "High",
            "X-Mailer": "Outlook"
        },
        "size_bytes": 1024
    }'

# Search emails
exec_curl "Search emails" \
    -X GET "$BASE_URL$API_PREFIX/emails/?limit=10" \
    -H "$AUTH_HEADER"

# Get email by ID (adjust ID as needed)
exec_curl "Get email details" \
    -X GET "$BASE_URL$API_PREFIX/emails/1" \
    -H "$AUTH_HEADER"

# Update email status
exec_curl "Mark email as read" \
    -X PATCH "$BASE_URL$API_PREFIX/emails/1" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "is_read": true,
        "is_flagged": true
    }'

# 7. Vector Search
print_section "7. VECTOR SEARCH"

# Generate embedding
exec_curl "Generate text embedding" \
    -X POST "$BASE_URL$API_PREFIX/vectors/embed" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "text": "Machine learning and artificial intelligence"
    }'

# Index a document
exec_curl "Index a document for vector search" \
    -X POST "$BASE_URL$API_PREFIX/vectors/index" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "id": "doc-001",
        "title": "AI Overview",
        "content": "Artificial Intelligence (AI) is the simulation of human intelligence in machines.",
        "metadata": {
            "category": "technology",
            "author": "John Doe"
        }
    }'

# Perform semantic search
exec_curl "Semantic search for similar documents" \
    -X POST "$BASE_URL$API_PREFIX/vectors/search" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "query": "What is machine learning?",
        "limit": 5,
        "threshold": 0.7
    }'

# 8. Bulk Operations
print_section "8. BULK OPERATIONS"

# Bulk update emails
exec_curl "Bulk update multiple emails" \
    -X POST "$BASE_URL$API_PREFIX/emails/bulk-update" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "email_ids": ["1", "2", "3"],
        "update": {
            "is_read": true
        }
    }'

# Bulk assign people to project
exec_curl "Bulk assign people to project" \
    -X POST "$BASE_URL$API_PREFIX/projects/bulk-assign-people" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{
        "person_ids": ["1", "2"],
        "project_id": "1",
        "role": "member"
    }'

# 9. Statistics
print_section "9. STATISTICS & ANALYTICS"

# Email statistics
exec_curl "Get email statistics" \
    -X GET "$BASE_URL$API_PREFIX/emails/statistics/overview" \
    -H "$AUTH_HEADER"

# Project statistics
exec_curl "Get project statistics" \
    -X GET "$BASE_URL$API_PREFIX/projects/statistics/overview" \
    -H "$AUTH_HEADER"

# 10. Thread Management
print_section "10. EMAIL THREADS"

# Get emails in a thread
exec_curl "Get emails in thread" \
    -X GET "$BASE_URL$API_PREFIX/emails/thread/thread-001" \
    -H "$AUTH_HEADER"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Test Complete!${NC}"
echo -e "${BLUE}========================================${NC}"

# Cleanup note
echo -e "\n${YELLOW}Note:${NC}"
echo "- Adjust IDs in the commands based on actual data"
echo "- Some endpoints may require authentication"
echo "- Install jq for better JSON formatting: apt-get install jq"
echo "- Run with: chmod +x curl_test_endpoints.sh && ./curl_test_endpoints.sh"