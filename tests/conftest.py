"""
Global pytest fixtures and configuration for all tests
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load test environment
load_dotenv(Path(__file__).parent / ".env.test")

from src.database.connection import Base, DatabaseManager
from src.database import email_models  # Import to register email tables
from src.database import models  # Import to register other tables
from src.api.app import app
from src.config import settings

# Override settings for testing
# Note: Settings is immutable, so we can't set attributes directly
# Instead, we'll use environment variables or fixture overrides
test_database_url = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://test_mcp_user:test_mcp_pass@localhost:5432/test_mcp_db")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    # For PostgreSQL, we need to ensure isolation between tests
    engine = create_async_engine(
        test_database_url,
        echo=False,
        poolclass=NullPool,
        pool_pre_ping=True,  # Check connections before using
    )
    
    # Drop all tables first to ensure clean state
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.commit()  # Commit any pending changes


@pytest_asyncio.fixture(scope="function")
async def test_client(test_session, test_user_data) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for API testing."""
    from httpx import ASGITransport
    from src.database.user_repository import UserRepository
    from src.database.auth_repositories import RoleRepository
    
    # Override the database dependency
    from src.api.routes.base import get_db
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test user in database for login tests
    user_repo = UserRepository(test_session)
    role_repo = RoleRepository(test_session)
    
    # Create default roles
    await role_repo.create_default_roles()
    
    # Create test user if not exists
    existing_user = await user_repo.get_by_username(test_user_data["username"])
    if not existing_user:
        user = await user_repo.create_with_password(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"]
        )
        await test_session.commit()
        
        # Add roles using direct SQL to avoid lazy loading issues
        from src.database.models import user_roles
        from sqlalchemy import insert
        
        # Add user role
        user_role = await role_repo.get_by_name("user")
        if user_role:
            stmt = insert(user_roles).values(user_id=user.id, role_id=user_role.id)
            await test_session.execute(stmt)
        
        # Add admin role
        admin_role = await role_repo.get_by_name("admin")
        if admin_role:
            stmt = insert(user_roles).values(user_id=user.id, role_id=admin_role.id)
            await test_session.execute(stmt)
        
        await test_session.commit()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(test_client: AsyncClient, test_session: AsyncSession, test_user_data) -> AsyncClient:
    """Create an authenticated test client with a valid JWT token."""
    from src.api.dependencies import create_access_token
    from src.database.user_repository import UserRepository
    from src.database.auth_repositories import RoleRepository
    
    # Create test user in database
    user_repo = UserRepository(test_session)
    role_repo = RoleRepository(test_session)
    
    # Create default roles
    await role_repo.create_default_roles()
    
    # User should already be created by test_client fixture
    # Just verify it exists
    existing_user = await user_repo.get_by_username(test_user_data["username"])
    if not existing_user:
        user = await user_repo.create_with_password(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"]
        )
        await test_session.commit()
        
        # Add roles using direct SQL
        from src.database.models import user_roles
        from sqlalchemy import insert
        
        # Add admin role
        admin_role = await role_repo.get_by_name("admin")
        if admin_role:
            stmt = insert(user_roles).values(user_id=user.id, role_id=admin_role.id)
            await test_session.execute(stmt)
        
        await test_session.commit()
    
    # Create a test user token
    token_data = {
        "sub": test_user_data["username"],
        "email": test_user_data["email"],
        "roles": ["user", "admin"]
    }
    token = create_access_token(token_data)
    
    # Set authorization header
    test_client.headers["Authorization"] = f"Bearer {token}"
    return test_client


@pytest_asyncio.fixture(scope="function")
async def db_manager(test_engine) -> DatabaseManager:
    """Create a test database manager."""
    manager = DatabaseManager()
    manager._engine = test_engine
    manager._session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    yield manager
    await manager.close()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for testing",
        "email_domains": ["test.com", "example.com"],
        "is_active": True,
        "auto_assign": True,
        "tags": ["test", "sample"]
    }


@pytest.fixture
def test_email_data():
    """Sample email data for testing."""
    from datetime import datetime
    
    return {
        "email_id": "test-msg-001",
        "from": "sender@test.com",
        "to": ["recipient1@test.com", "recipient2@example.com"],
        "cc": ["cc@test.com"],
        "subject": "Test Email Subject",
        "body": "<html><body><p>Test email body</p></body></html>",
        "body_text": "Test email body",
        "datetime": datetime.utcnow().isoformat(),
        "headers": {"X-Test": "true"},
        "size_bytes": 1024
    }


@pytest.fixture
def test_person_data():
    """Sample person data for testing."""
    return {
        "email": "john.doe@test.com",
        "first_name": "John",
        "last_name": "Doe",
        "organization": "Test Corp",
        "phone": "+1-555-0123",
        "is_active": True,
        "is_external": False
    }


class TestDataFactory:
    """Factory for creating test data consistently."""
    
    @staticmethod
    async def create_test_user(session: AsyncSession, **kwargs):
        """Create a test user in the database."""
        from src.database.models import User
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": pwd_context.hash("TestPassword123!"),
            "full_name": "Test User",
            "is_active": True,
            **kwargs
        }
        
        user = User(**data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    @staticmethod
    async def create_test_project(session: AsyncSession, **kwargs):
        """Create a test project in the database."""
        from src.database.email_models import Project
        
        data = {
            "name": "Test Project",
            "description": "Test Description",
            "email_domains": ["test.com"],
            "is_active": True,
            "auto_assign": True,
            **kwargs
        }
        
        project = Project(**data)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project
    
    @staticmethod
    async def create_test_person(session: AsyncSession, **kwargs):
        """Create a test person in the database."""
        from src.database.email_models import Person
        from uuid import uuid4
        import time
        
        # Generate unique email if not provided
        unique_suffix = f"{uuid4().hex[:8]}_{int(time.time() * 1000)}"
        default_email = f"test_{unique_suffix}@example.com"
        
        data = {
            "email": kwargs.pop("email", default_email),
            "first_name": "Test",
            "last_name": "Person",
            "organization": "Test Org",
            **kwargs
        }
        
        person = Person(**data)
        session.add(person)
        await session.commit()
        await session.refresh(person)
        return person
    
    @staticmethod
    async def create_test_email(session: AsyncSession, sender=None, project=None, **kwargs):
        """Create a test email in the database."""
        from src.database.email_models import Email
        from datetime import datetime
        
        if not sender:
            sender = await TestDataFactory.create_test_person(session)
        
        data = {
            "email_id": f"test-{datetime.utcnow().timestamp()}",
            "from_person_id": sender.id,
            "subject": "Test Email",
            "body": "<p>Test body</p>",
            "body_text": "Test body",
            "datetime_sent": datetime.utcnow(),
            "project_id": project.id if project else None,
            **kwargs
        }
        
        email = Email(**data)
        session.add(email)
        await session.commit()
        await session.refresh(email)
        return email


@pytest.fixture
def test_factory():
    """Provide test data factory."""
    return TestDataFactory


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )