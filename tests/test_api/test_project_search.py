"""
Tests for project search functionality
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.database
class TestProjectSearch:
    """Test project search functionality"""
    
    async def test_search_projects_by_name(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test searching projects by name"""
        # Create projects with different names
        await test_factory.create_test_project(
            test_session,
            name="Alpha Project"
        )
        await test_factory.create_test_project(
            test_session,
            name="Beta Project"
        )
        await test_factory.create_test_project(
            test_session,
            name="Gamma System"
        )
        
        response = await authenticated_client.get(
            "/api/v1/projects/search?q=Project"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        for project in data:
            assert "Project" in project["name"]
    
    async def test_search_projects_by_domain(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test searching projects by email domain"""
        # Create projects with different domains
        await test_factory.create_test_project(
            test_session,
            name="Domain Test 1",
            email_domains=["example.com", "test.com"]
        )
        await test_factory.create_test_project(
            test_session,
            name="Domain Test 2",
            email_domains=["other.org"]
        )
        
        response = await authenticated_client.get(
            "/api/v1/projects/search?domain=example.com"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        for project in data:
            assert "example.com" in project["email_domains"]
    
    async def test_find_project_for_email(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test finding the right project for an email address"""
        # Create projects with specific domains
        project = await test_factory.create_test_project(
            test_session,
            name="Company Project",
            email_domains=["company.com"],
            auto_assign=True
        )
        
        response = await authenticated_client.post(
            "/api/v1/projects/find-for-email",
            json={"email": "user@company.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(project.id)
        assert data["name"] == project.name