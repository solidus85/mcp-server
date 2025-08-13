"""
Tests for email retrieval and search endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, UTC


@pytest.mark.asyncio
@pytest.mark.database
class TestEmailRetrieval:
    """Test email retrieval and search endpoints"""
    
    async def test_get_email_by_id(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting email by ID"""
        # Create email
        email = await test_factory.create_test_email(test_session)
        
        response = await authenticated_client.get(
            f"/api/v1/emails/{email.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(email.id)
        assert data["email_id"] == email.email_id
        assert data["subject"] == email.subject
    
    async def test_get_email_by_message_id(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting email by message ID"""
        # Create email
        email = await test_factory.create_test_email(
            test_session,
            email_id="msg-unique-001"
        )
        
        response = await authenticated_client.get(
            "/api/v1/emails/by-message-id/msg-unique-001"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(email.id)
        assert data["email_id"] == "msg-unique-001"
    
    async def test_list_emails(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test listing emails with pagination"""
        # Create multiple emails
        for i in range(10):
            await test_factory.create_test_email(
                test_session,
                subject=f"List Email {i}"
            )
        
        response = await authenticated_client.get(
            "/api/v1/emails/?page=1&size=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 5
        assert data["page"] == 1
        assert data["size"] == 5
    
    async def test_search_emails_by_subject(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test searching emails by subject"""
        # Create emails with different subjects
        await test_factory.create_test_email(
            test_session,
            subject="Important Meeting Tomorrow"
        )
        await test_factory.create_test_email(
            test_session,
            subject="Meeting Notes"
        )
        await test_factory.create_test_email(
            test_session,
            subject="Random Subject"
        )
        
        response = await authenticated_client.get(
            "/api/v1/emails/search?q=Meeting"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) >= 2
        for email in data["results"]:
            assert "Meeting" in email["subject"]
    
    async def test_search_emails_by_sender(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test searching emails by sender"""
        # Create sender
        sender = await test_factory.create_test_person(
            test_session,
            email="specific@sender.com"
        )
        
        # Create emails from this sender
        for i in range(3):
            await test_factory.create_test_email(
                test_session,
                sender=sender,
                subject=f"From Sender {i}"
            )
        
        response = await authenticated_client.get(
            "/api/v1/emails/search?from=specific@sender.com"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) >= 3
        for email in data["results"]:
            assert email["from"] == "specific@sender.com"
    
    async def test_search_emails_by_date_range(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test searching emails by date range"""
        # Create emails with different dates
        base_date = datetime.now(UTC).replace(tzinfo=None)
        
        for i in range(5):
            await test_factory.create_test_email(
                test_session,
                datetime_sent=base_date - timedelta(days=i),
                subject=f"Date Email {i}"
            )
        
        # Search for emails from last 3 days
        start_date = (base_date - timedelta(days=2)).replace(microsecond=0).isoformat()
        end_date = base_date.replace(microsecond=0).isoformat()
        
        response = await authenticated_client.get(
            f"/api/v1/emails/search?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) >= 2  # At least emails from last 2 days
    
    async def test_get_email_thread(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting all emails in a thread"""
        # Create thread with multiple emails
        thread_id = "test-thread-001"
        
        for i in range(4):
            await test_factory.create_test_email(
                test_session,
                thread_id=thread_id,
                subject=f"Thread Message {i}"
            )
        
        response = await authenticated_client.get(
            f"/api/v1/emails/thread/{thread_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 4
        for email in data:
            assert email["thread_id"] == thread_id