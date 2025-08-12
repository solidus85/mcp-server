"""
Tests for email ingestion and management endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import json


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
            "datetime": datetime.utcnow().isoformat()
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
                "datetime": datetime.utcnow().isoformat()
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
            "datetime": datetime.utcnow().isoformat(),
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
            "datetime": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
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
            "datetime": datetime.utcnow().isoformat(),
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
            "/api/v1/emails?page=1&size=5"
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
        base_date = datetime.utcnow()
        
        for i in range(5):
            await test_factory.create_test_email(
                test_session,
                datetime_sent=base_date - timedelta(days=i),
                subject=f"Date Email {i}"
            )
        
        # Search for emails from last 3 days
        start_date = (base_date - timedelta(days=2)).isoformat()
        end_date = base_date.isoformat()
        
        response = await authenticated_client.get(
            f"/api/v1/emails/search?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) >= 3
    
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


@pytest.mark.asyncio
@pytest.mark.database
class TestEmailOperations:
    """Test email operations and updates"""
    
    async def test_mark_email_as_read(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test marking email as read"""
        # Create unread email
        email = await test_factory.create_test_email(
            test_session,
            is_read=False
        )
        
        response = await authenticated_client.patch(
            f"/api/v1/emails/{email.id}",
            json={"is_read": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_read"] == True
    
    async def test_flag_email(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test flagging/unflagging email"""
        # Create email
        email = await test_factory.create_test_email(test_session)
        
        # Flag email
        response = await authenticated_client.patch(
            f"/api/v1/emails/{email.id}",
            json={"is_flagged": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_flagged"] == True
        
        # Unflag email
        response = await authenticated_client.patch(
            f"/api/v1/emails/{email.id}",
            json={"is_flagged": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_flagged"] == False
    
    async def test_assign_email_to_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test assigning email to project"""
        # Create email and project
        email = await test_factory.create_test_email(test_session)
        project = await test_factory.create_test_project(test_session)
        
        response = await authenticated_client.patch(
            f"/api/v1/emails/{email.id}",
            json={"project_id": str(project.id)}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["project_id"] == str(project.id)
    
    async def test_bulk_mark_as_read(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test bulk marking emails as read"""
        # Create multiple unread emails
        email_ids = []
        for i in range(5):
            email = await test_factory.create_test_email(
                test_session,
                is_read=False
            )
            email_ids.append(str(email.id))
        
        response = await authenticated_client.post(
            "/api/v1/emails/bulk/mark-read",
            json={"email_ids": email_ids}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["updated"] == 5
    
    async def test_bulk_assign_to_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test bulk assigning emails to project"""
        # Create emails and project
        project = await test_factory.create_test_project(test_session)
        
        email_ids = []
        for i in range(3):
            email = await test_factory.create_test_email(test_session)
            email_ids.append(str(email.id))
        
        response = await authenticated_client.post(
            "/api/v1/emails/bulk/assign-project",
            json={
                "email_ids": email_ids,
                "project_id": str(project.id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["updated"] == 3
    
    async def test_delete_email(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test deleting an email"""
        # Create email
        email = await test_factory.create_test_email(test_session)
        
        response = await authenticated_client.delete(
            f"/api/v1/emails/{email.id}"
        )
        
        assert response.status_code == 204
        
        # Verify email is deleted
        response = await authenticated_client.get(
            f"/api/v1/emails/{email.id}"
        )
        assert response.status_code == 404
    
    async def test_bulk_delete_emails(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test bulk deleting emails"""
        # Create multiple emails
        email_ids = []
        for i in range(3):
            email = await test_factory.create_test_email(test_session)
            email_ids.append(str(email.id))
        
        response = await authenticated_client.post(
            "/api/v1/emails/bulk/delete",
            json={"email_ids": email_ids}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["deleted"] == 3


@pytest.mark.asyncio
@pytest.mark.database
class TestEmailStatistics:
    """Test email statistics endpoints"""
    
    async def test_email_statistics_overall(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting overall email statistics"""
        # Create various emails
        for i in range(10):
            await test_factory.create_test_email(
                test_session,
                is_read=(i % 2 == 0),
                is_flagged=(i % 3 == 0)
            )
        
        response = await authenticated_client.get("/api/v1/emails/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_emails" in data
        assert "unread_count" in data
        assert "flagged_count" in data
        assert "thread_count" in data
        assert "sender_count" in data
        assert data["total_emails"] >= 10
    
    async def test_email_statistics_by_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting email statistics by project"""
        # Create project and emails
        project = await test_factory.create_test_project(test_session)
        
        for i in range(7):
            await test_factory.create_test_email(
                test_session,
                project=project
            )
        
        response = await authenticated_client.get(
            f"/api/v1/emails/stats/project/{project.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["project_id"] == str(project.id)
        assert data["email_count"] >= 7
    
    async def test_email_activity_timeline(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting email activity timeline"""
        # Create emails over time
        base_date = datetime.utcnow()
        
        for i in range(30):
            await test_factory.create_test_email(
                test_session,
                datetime_sent=base_date - timedelta(days=i)
            )
        
        response = await authenticated_client.get(
            "/api/v1/emails/stats/timeline?days=30"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timeline" in data
        assert len(data["timeline"]) > 0
        
        for entry in data["timeline"]:
            assert "date" in entry
            assert "count" in entry