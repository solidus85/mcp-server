"""
Tests for project statistics
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.database
class TestProjectStats:
    """Test project statistics"""
    
    async def test_project_statistics(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting project statistics"""
        # Create project with emails
        project = await test_factory.create_test_project(test_session)
        
        # Create emails for the project
        for i in range(5):
            await test_factory.create_test_email(
                test_session,
                project=project
            )
        
        response = await authenticated_client.get(
            f"/api/v1/projects/{project.id}/stats"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email_count" in data
        assert "person_count" in data
        assert "thread_count" in data
        assert "last_activity" in data
        assert data["email_count"] >= 5