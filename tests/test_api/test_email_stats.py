"""
Tests for email statistics endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta


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