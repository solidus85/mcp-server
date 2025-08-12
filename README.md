# MCP Server - Model Context Protocol Server with LLM Integration

A comprehensive Model Context Protocol (MCP) server implementation with vector database support, PostgreSQL integration, and LLM capabilities. This server provides a robust platform for building AI-powered applications with email management, document processing, and semantic search capabilities.

## Features

### Core Capabilities
- **Model Context Protocol (MCP)** - Full implementation with stdio transport
- **Vector Database** - ChromaDB integration for semantic search and embeddings
- **PostgreSQL Database** - Relational data storage with async SQLAlchemy
- **LLM Integration** - Support for OpenAI and Anthropic Claude APIs
- **REST API** - FastAPI-based API with authentication and rate limiting
- **Email Management** - Comprehensive email ingestion and organization system

### Email Management System
- Automatic person and project discovery from emails
- Thread tracking and conversation management
- Domain-based project assignment
- Rich metadata storage using PostgreSQL JSONB
- Full-text and semantic search capabilities

### Technical Features
- Async/await throughout for high performance
- Database migrations with Alembic
- Comprehensive logging and monitoring
- Docker support for easy deployment
- JWT-based authentication
- Rate limiting and request throttling

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16+
- Docker and Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/mcp-server.git
cd mcp-server
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.template .env
# Edit .env with your configuration
```

5. **Set up PostgreSQL database**
```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE mcp_db;
CREATE USER mcp_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE mcp_db TO mcp_user;
\q

# Run setup script
sudo -u postgres psql -d mcp_db -f scripts/setup_database.sql
```

6. **Run database migrations**
```bash
alembic upgrade head
```

7. **Start the server**
```bash
python -m uvicorn src.api.app:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Setup

1. **Start all services**
```bash
docker-compose up -d
```

2. **View logs**
```bash
docker-compose logs -f mcp-server
```

3. **Stop services**
```bash
docker-compose down
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

### Key Endpoints

#### Email Management
- `POST /api/v1/emails/ingest` - Ingest a new email
- `GET /api/v1/emails/` - Search emails
- `GET /api/v1/emails/{email_id}` - Get email details
- `PATCH /api/v1/emails/{email_id}` - Update email properties

#### People Management
- `POST /api/v1/people/` - Create a person
- `GET /api/v1/people/` - Search people
- `GET /api/v1/people/{person_id}` - Get person details
- `POST /api/v1/people/{person_id}/projects/{project_id}` - Assign person to project

#### Project Management
- `POST /api/v1/projects/` - Create a project
- `GET /api/v1/projects/` - Search projects
- `GET /api/v1/projects/{project_id}` - Get project details

#### Vector Search
- `POST /api/v1/vectors/embed` - Generate embeddings
- `POST /api/v1/vectors/search` - Semantic search
- `POST /api/v1/vectors/index` - Index documents

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

## Configuration

### Environment Variables

Key environment variables (see `.env.template` for full list):

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mcp_db

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=mcp_vectors

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# JWT Settings
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Server Settings
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

## Project Structure

```
mcp-server/
├── src/
│   ├── mcp/              # MCP protocol implementation
│   │   ├── server.py      # MCP server core
│   │   ├── tools.py       # Tool definitions
│   │   └── resources.py   # Resource management
│   ├── database/          # Database layer
│   │   ├── connection.py  # Database connection manager
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── email_models.py # Email-specific models
│   │   ├── repositories.py # Repository pattern implementation
│   │   └── migrations/    # Alembic migrations
│   ├── api/              # REST API
│   │   ├── app.py        # FastAPI application
│   │   ├── routes/       # API endpoints
│   │   ├── schemas/      # Pydantic schemas
│   │   └── middleware.py # Middleware stack
│   ├── vector/           # Vector database
│   │   ├── database.py   # ChromaDB integration
│   │   └── embeddings.py # Embedding generation
│   ├── llm/              # LLM integration
│   │   ├── client.py     # LLM client abstraction
│   │   └── prompts.py    # Prompt management
│   └── utils/            # Utilities
├── scripts/              # Utility scripts
├── tests/               # Test suite
├── config/              # Configuration files
├── docker-compose.yml   # Docker composition
├── Dockerfile          # Docker image definition
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_email_pipeline.py
```

### Test Email Pipeline
```bash
python scripts/test_email_pipeline.py
```

### Check Database Connection
```bash
python scripts/check_db.py
```

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

### Adding New LLM Providers

1. Create provider client in `src/llm/providers/`
2. Implement the `BaseLLMClient` interface
3. Register in `src/llm/client.py`

### Extending the Email System

1. Add new fields to models in `src/database/email_models.py`
2. Create migration: `alembic revision --autogenerate -m "Add new fields"`
3. Update schemas in `src/api/schemas/email_schemas.py`
4. Add business logic to `src/database/email_repositories.py`

## Production Deployment

### Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **Database Passwords**: Use strong, unique passwords
3. **JWT Secret**: Generate a secure random key
4. **API Keys**: Store securely, rotate regularly
5. **HTTPS**: Always use HTTPS in production
6. **Rate Limiting**: Configure appropriate limits

### Scaling

- Use PostgreSQL connection pooling
- Deploy multiple API server instances behind a load balancer
- Consider Redis for caching and session storage
- Use dedicated ChromaDB cluster for vector storage
- Implement horizontal scaling for compute-intensive operations

### Monitoring

- Health check endpoint: `/health`
- Metrics endpoint: `/metrics` (Prometheus format)
- Structured logging with correlation IDs
- Database query performance monitoring
- API response time tracking

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify credentials in `.env`
   - Run `scripts/check_db.py` to test connection

2. **Permission Denied for Schema Public**
   - Run: `sudo -u postgres psql -d mcp_db -f scripts/setup_database.sql`

3. **ChromaDB Connection Failed**
   - Ensure ChromaDB is running
   - Check CHROMA_HOST and CHROMA_PORT settings

4. **LLM API Errors**
   - Verify API keys are set correctly
   - Check rate limits and quotas

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and linting
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [github.com/yourusername/mcp-server/issues](https://github.com/yourusername/mcp-server/issues)
- Documentation: [docs.example.com](https://docs.example.com)

## Acknowledgments

- Model Context Protocol specification
- FastAPI framework
- ChromaDB vector database
- PostgreSQL database
- SQLAlchemy ORM
- Anthropic and OpenAI for LLM APIs