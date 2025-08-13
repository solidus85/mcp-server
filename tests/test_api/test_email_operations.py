"""
Tests for email operations and bulk update endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


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