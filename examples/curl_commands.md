# Curl Commands for Testing MCP Server API

Copy and paste these commands to test the MCP Server endpoints. Replace `localhost:8000` with your server address if different.

## Basic Health Checks

### Check server health
```bash
curl -X GET http://localhost:8000/health
```

### Get API info
```bash
curl -X GET http://localhost:8000/api/v1/info
```

## Authentication

### Register a new user
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }'
```

### Login (get JWT token)
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPassword123!"
  }'
```

Save the token from the response and use it in subsequent requests as:
```bash
-H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Project Management

### Create a project
```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "description": "Main client project",
    "email_domains": ["acme.com", "acme.org"],
    "is_active": true,
    "auto_assign": true,
    "tags": ["client", "important"]
  }'
```

### List all projects
```bash
curl -X GET http://localhost:8000/api/v1/projects/
```

### Get project by ID
```bash
curl -X GET http://localhost:8000/api/v1/projects/PROJECT_ID
```

### Update a project
```bash
curl -X PATCH http://localhost:8000/api/v1/projects/PROJECT_ID \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "tags": ["client", "priority", "Q4"]
  }'
```

## People Management

### Create a person
```bash
curl -X POST http://localhost:8000/api/v1/people/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@acme.com",
    "first_name": "John",
    "last_name": "Doe",
    "organization": "Acme Corporation",
    "phone": "+1-555-0123"
  }'
```

### Search people
```bash
curl -X GET "http://localhost:8000/api/v1/people/?query=john&limit=10"
```

### Get person by ID
```bash
curl -X GET http://localhost:8000/api/v1/people/PERSON_ID
```

### Add person to project
```bash
curl -X POST http://localhost:8000/api/v1/people/PERSON_ID/projects/PROJECT_ID?role=member
```

## Email Management

### Ingest an email
```bash
curl -X POST http://localhost:8000/api/v1/emails/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "msg-001",
    "from": "alice@ourcompany.com",
    "to": ["john.doe@acme.com", "jane.smith@acme.com"],
    "cc": ["bob@ourcompany.com"],
    "subject": "Project Update - Q4 Planning",
    "body": "<html><body><p>Hi team,</p><p>Here is the project update.</p></body></html>",
    "body_text": "Hi team,\n\nHere is the project update.",
    "datetime": "2024-01-15T10:30:00Z",
    "headers": {"X-Priority": "High"}
  }'
```

### Search emails
```bash
# Basic search
curl -X GET "http://localhost:8000/api/v1/emails/?limit=10"

# Search with filters
curl -X GET "http://localhost:8000/api/v1/emails/?project_id=PROJECT_ID&limit=10"

# Search by date range
curl -X GET "http://localhost:8000/api/v1/emails/?date_from=2024-01-01T00:00:00Z&date_to=2024-12-31T23:59:59Z"

# Search by sender
curl -X GET "http://localhost:8000/api/v1/emails/?from_email=alice@ourcompany.com"
```

### Get email by ID
```bash
curl -X GET http://localhost:8000/api/v1/emails/EMAIL_ID
```

### Update email status
```bash
curl -X PATCH http://localhost:8000/api/v1/emails/EMAIL_ID \
  -H "Content-Type: application/json" \
  -d '{
    "is_read": true,
    "is_flagged": true
  }'
```

### Get emails in thread
```bash
curl -X GET http://localhost:8000/api/v1/emails/thread/THREAD_ID
```

### Bulk update emails
```bash
curl -X POST http://localhost:8000/api/v1/emails/bulk-update \
  -H "Content-Type: application/json" \
  -d '{
    "email_ids": ["id1", "id2", "id3"],
    "update": {
      "is_read": true,
      "is_flagged": false
    }
  }'
```

## Vector Search

### Generate embedding
```bash
curl -X POST http://localhost:8000/api/v1/vectors/embed \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning and artificial intelligence"
  }'
```

### Index a document
```bash
curl -X POST http://localhost:8000/api/v1/vectors/index \
  -H "Content-Type: application/json" \
  -d '{
    "id": "doc-001",
    "title": "AI Overview",
    "content": "Artificial Intelligence is the simulation of human intelligence in machines.",
    "metadata": {
      "category": "technology",
      "author": "John Doe",
      "year": 2024
    }
  }'
```

### Semantic search
```bash
curl -X POST http://localhost:8000/api/v1/vectors/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "limit": 5,
    "threshold": 0.7
  }'
```

### Search with filters
```bash
curl -X POST http://localhost:8000/api/v1/vectors/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "filters": {
      "category": "technology",
      "year": 2024
    },
    "limit": 10
  }'
```

## Statistics

### Get email statistics
```bash
curl -X GET http://localhost:8000/api/v1/emails/statistics/overview
```

### Get project statistics
```bash
curl -X GET http://localhost:8000/api/v1/projects/statistics/overview
```

## Tips for Testing

### Format JSON output
Add `| python -m json.tool` to format JSON responses:
```bash
curl -X GET http://localhost:8000/api/v1/projects/ | python -m json.tool
```

### Save response to file
```bash
curl -X GET http://localhost:8000/api/v1/emails/ -o emails.json
```

### Include response headers
```bash
curl -i -X GET http://localhost:8000/health
```

### Verbose output for debugging
```bash
curl -v -X GET http://localhost:8000/health
```

### Using authentication token
After login, save your token and use it like this:
```bash
TOKEN="your_jwt_token_here"
curl -X GET http://localhost:8000/api/v1/emails/ \
  -H "Authorization: Bearer $TOKEN"
```

## Quick Test Sequence

1. First, check if server is running:
```bash
curl http://localhost:8000/health
```

2. Create a project:
```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "email_domains": ["test.com"]}'
```

3. Ingest an email:
```bash
curl -X POST http://localhost:8000/api/v1/emails/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test-001",
    "from": "sender@test.com",
    "to": ["recipient@test.com"],
    "subject": "Test Email",
    "body": "This is a test",
    "body_text": "This is a test",
    "datetime": "2024-01-15T10:00:00Z"
  }'
```

4. Search for the email:
```bash
curl "http://localhost:8000/api/v1/emails/?query=Test"
```