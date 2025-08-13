"""
Tests for email ingestion endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, UTC


@pytest.mark.asyncio
@pytest.mark.database
class TestEmailIngestion:
    """Test email ingestion endpoints"""
    
    async def test_ingest_single_email(
        self,
        authenticated_client: AsyncClient,
        test_email_data
    ):
        """Test ingesting a single email"""
        response = await authenticated_client.post(
            "/api/v1/emails/ingest",
            json=test_email_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["email_id"] == test_email_data["email_id"]
        assert data["subject"] == test_email_data["subject"]
        assert data["sender"]["email"] == test_email_data["from"]
        # Check recipients
        to_emails = [r["person"]["email"] for r in data["recipients"] if r["recipient_type"] == "TO"]
        assert set(to_emails) == set(test_email_data["to"])
        assert "id" in data
        assert "thread_id" in data
    
    async def test_ingest_email_with_auto_project_assignment(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test email auto-assignment to project based on domain"""
        # Create project with auto-assign
        project = await test_factory.create_test_project(
            test_session,
            name="Auto Project",
            email_domains=["autoassign.com"],
            auto_assign=True
        )
        
        email_data = {
            "email_id": "auto-001",
            "from": "sender@autoassign.com",
            "to": ["recipient@autoassign.com"],
            "subject": "Auto Assignment Test",
            "body": "Test body",
            "body_text": "Test body",
            "datetime": datetime.now(UTC).isoformat()
        }
        
        response = await authenticated_client.post(
            "/api/v1/emails/ingest",
            json=email_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["project_id"] == str(project.id)
        assert data["project_name"] == project.name
    
    async def test_ingest_email_duplicate(
        self,
        authenticated_client: AsyncClient,
        test_email_data
    ):
        """Test ingesting duplicate email (should update, not create new)"""
        # Ingest first time
        response1 = await authenticated_client.post(
            "/api/v1/emails/ingest",
            json=test_email_data
        )
        assert response1.status_code == 201
        data1 = response1.json()
        
        # Ingest again with same email_id
        response2 = await authenticated_client.post(
            "/api/v1/emails/ingest",
            json=test_email_data
        )
        
        assert response2.status_code == 200  # 200 for update, not 201
        data2 = response2.json()
        
        assert data1["id"] == data2["id"]  # Same database ID
        assert data2["email_id"] == test_email_data["email_id"]
    
    async def test_ingest_bulk_emails(
        self,
        authenticated_client: AsyncClient
    ):
        """Test bulk email ingestion"""
        emails = []
        for i in range(5):
            emails.append({
                "email_id": f"bulk-{i:03d}",
                "from": f"sender{i}@example.com",
                "to": ["recipient@example.com"],
                "subject": f"Bulk Email {i}",
                "body": f"Body {i}",
                "body_text": f"Body {i}",
                "datetime": datetime.now(UTC).isoformat()
            })
        
        response = await authenticated_client.post(
            "/api/v1/emails/ingest/bulk",
            json={"emails": emails}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["ingested"] == 5
        assert data["failed"] == 0
        assert len(data["results"]) == 5
    
    async def test_ingest_email_with_thread(
        self,
        authenticated_client: AsyncClient
    ):
        """Test email threading"""
        # First email in thread
        email1 = {
            "email_id": "thread-001",
            "from": "alice@example.com",
            "to": ["bob@example.com"],
            "subject": "Thread Test",
            "body": "Initial message",
            "body_text": "Initial message",
            "datetime": datetime.now(UTC).isoformat(),
            "thread_id": "thread-test-001"
        }
        
        response1 = await authenticated_client.post(
            "/api/v1/emails/ingest",
            json=email1
        )
        assert response1.status_code == 201
        data1 = response1.json()
        
        # Reply in same thread
        email2 = {
            "email_id": "thread-002",
            "from": "bob@example.com",
            "to": ["alice@example.com"],
            "subject": "RE: Thread Test",
            "body": "Reply message",
            "body_text": "Reply message",
            "datetime": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "thread_id": "thread-test-001",
            "in_reply_to": "thread-001"
        }
        
        response2 = await authenticated_client.post(
            "/api/v1/emails/ingest",
            json=email2
        )
        assert response2.status_code == 201
        data2 = response2.json()
        
        assert data1["thread_id"] == data2["thread_id"]
        assert data2["in_reply_to"] == email1["email_id"]
    
    async def test_ingest_email_with_attachments(
        self,
        authenticated_client: AsyncClient
    ):
        """Test email with attachment metadata"""
        email_data = {
            "email_id": "attach-001",
            "from": "sender@example.com",
            "to": ["recipient@example.com"],
            "subject": "Email with Attachments",
            "body": "See attached",
            "body_text": "See attached",
            "datetime": datetime.now(UTC).isoformat(),
            "attachments": [
                {
                    "filename": "document.pdf",
                    "size": 102400,
                    "mime_type": "application/pdf"
                },
                {
                    "filename": "image.jpg",
                    "size": 51200,
                    "mime_type": "image/jpeg"
                }
            ]
        }
        
        response = await authenticated_client.post(
            "/api/v1/emails/ingest",
            json=email_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["has_attachments"] == True
        assert data["attachment_count"] == 2
        assert len(data["attachments"]) == 2