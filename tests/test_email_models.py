"""
Unit tests for email models and repositories
"""

import pytest
import asyncio
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.database.connection import Base
from src.database.email_models import Person, Project, Email, EmailRecipient, RecipientType
from src.database.email_repositories import PersonRepository, ProjectRepository, EmailRepository


# Test database URL (using SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_person(async_session: AsyncSession):
    """Test creating a person"""
    repo = PersonRepository(async_session)
    
    person = await repo.create(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        organization="Test Org"
    )
    
    assert person.id is not None
    assert person.email == "test@example.com"
    assert person.first_name == "Test"
    assert person.last_name == "User"
    assert person.full_name == "Test User"
    assert person.organization == "Test Org"


@pytest.mark.asyncio
async def test_get_or_create_person(async_session: AsyncSession):
    """Test get_or_create functionality"""
    repo = PersonRepository(async_session)
    
    # First creation
    person1, created1 = await repo.get_or_create(
        email="test@example.com",
        display_name="Test User"
    )
    assert created1 is True
    assert person1.email == "test@example.com"
    
    # Second call should return existing
    person2, created2 = await repo.get_or_create(
        email="test@example.com",
        display_name="Different Name"
    )
    assert created2 is False
    assert person1.id == person2.id
    assert person2.display_name == "Test User"  # Original name preserved


@pytest.mark.asyncio
async def test_create_project(async_session: AsyncSession):
    """Test creating a project"""
    repo = ProjectRepository(async_session)
    
    project = await repo.create(
        name="Test Project",
        description="Test Description",
        email_domains=["example.com", "test.org"],
        tags=["test", "demo"]
    )
    
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.email_domains == ["example.com", "test.org"]
    assert project.has_domain("user@example.com") is True
    assert project.has_domain("user@other.com") is False


@pytest.mark.asyncio
async def test_email_ingestion(async_session: AsyncSession):
    """Test email ingestion with automatic person and project creation"""
    email_repo = EmailRepository(async_session)
    project_repo = ProjectRepository(async_session)
    
    # Create a project first
    project = await project_repo.create(
        name="Test Project",
        email_domains=["example.com"],
        auto_assign=True
    )
    
    # Ingest an email
    email = await email_repo.ingest_email(
        email_id="test001",
        from_email="sender@example.com",
        to_emails=["recipient@example.com"],
        cc_emails=["cc@example.com"],
        subject="Test Email",
        body="<p>Test body</p>",
        body_text="Test body",
        datetime_sent=datetime.now(),
        headers={"X-Test": "true"}
    )
    
    assert email.id is not None
    assert email.email_id == "test001"
    assert email.subject == "Test Email"
    assert email.sender.email == "sender@example.com"
    assert len(email.recipients) == 2  # 1 TO + 1 CC
    
    # Check project assignment
    assert email.project is not None
    assert email.project.id == project.id


@pytest.mark.asyncio
async def test_email_thread_tracking(async_session: AsyncSession):
    """Test email thread tracking"""
    email_repo = EmailRepository(async_session)
    
    # First email in thread
    email1 = await email_repo.ingest_email(
        email_id="thread001",
        from_email="user1@example.com",
        to_emails=["user2@example.com"],
        subject="Thread Test",
        body="First message",
        body_text="First message",
        datetime_sent=datetime.now(),
        thread_id="thread_test_001"
    )
    
    # Reply in same thread
    email2 = await email_repo.ingest_email(
        email_id="thread002",
        from_email="user2@example.com",
        to_emails=["user1@example.com"],
        subject="RE: Thread Test",
        body="Reply message",
        body_text="Reply message",
        datetime_sent=datetime.now(),
        thread_id="thread_test_001",
        in_reply_to="thread001"
    )
    
    # Get thread emails
    thread_emails = await email_repo.get_thread_emails("thread_test_001")
    
    assert len(thread_emails) == 2
    assert all(e.thread_id == "thread_test_001" for e in thread_emails)


@pytest.mark.asyncio
async def test_person_project_association(async_session: AsyncSession):
    """Test many-to-many relationship between people and projects"""
    person_repo = PersonRepository(async_session)
    project_repo = ProjectRepository(async_session)
    
    # Create person and project
    person = await person_repo.create(
        email="member@example.com",
        first_name="Team",
        last_name="Member"
    )
    
    project = await project_repo.create(
        name="Team Project",
        email_domains=["example.com"]
    )
    
    # Add person to project
    success = await person_repo.add_to_project(
        person.id,
        project.id,
        role="developer"
    )
    
    assert success is True
    
    # Verify association
    await async_session.commit()
    people_in_project = await person_repo.get_by_project(project.id)
    
    assert len(people_in_project) == 1
    assert people_in_project[0].id == person.id


@pytest.mark.asyncio
async def test_email_search(async_session: AsyncSession):
    """Test email search functionality"""
    email_repo = EmailRepository(async_session)
    
    # Create test emails
    for i in range(5):
        await email_repo.ingest_email(
            email_id=f"search{i:03d}",
            from_email=f"sender{i}@example.com",
            to_emails=["recipient@example.com"],
            subject=f"Test Email {i}",
            body=f"Body {i}",
            body_text=f"Body {i}",
            datetime_sent=datetime.now()
        )
    
    # Search emails
    results = await email_repo.search_emails(
        query="Test Email",
        limit=3
    )
    
    assert len(results) <= 3
    assert all("Test Email" in e.subject for e in results)


@pytest.mark.asyncio
async def test_email_update(async_session: AsyncSession):
    """Test updating email properties"""
    email_repo = EmailRepository(async_session)
    
    # Create email
    email = await email_repo.ingest_email(
        email_id="update001",
        from_email="sender@example.com",
        to_emails=["recipient@example.com"],
        subject="Update Test",
        body="Body",
        body_text="Body",
        datetime_sent=datetime.now()
    )
    
    # Update email
    updated = await email_repo.update(
        email.id,
        is_read=True,
        is_flagged=True
    )
    
    assert updated.is_read is True
    assert updated.is_flagged is True


@pytest.mark.asyncio
async def test_person_external_detection(async_session: AsyncSession):
    """Test automatic detection of external users"""
    person_repo = PersonRepository(async_session)
    
    # Internal domain user
    internal_person, _ = await person_repo.get_or_create(
        email="user@company.com",
        internal_domains=["company.com", "company.org"]
    )
    
    # External domain user
    external_person, _ = await person_repo.get_or_create(
        email="user@external.com",
        internal_domains=["company.com", "company.org"]
    )
    
    assert internal_person.is_external is False
    assert external_person.is_external is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])