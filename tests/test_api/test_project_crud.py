"""
Tests for project CRUD operations
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.database
class TestProjectCRUD:
    """Test project CRUD operations"""
    
    async def test_create_project(self, authenticated_client: AsyncClient, test_project_data):
        """Test creating a new project"""
        response = await authenticated_client.post(
            "/api/v1/projects/",
            json=test_project_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == test_project_data["name"]
        assert data["description"] == test_project_data["description"]
        assert data["email_domains"] == test_project_data["email_domains"]
        assert data["is_active"] == test_project_data["is_active"]
        assert data["auto_assign"] == test_project_data["auto_assign"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_project_duplicate_name(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test creating project with duplicate name"""
        # Create first project
        await test_factory.create_test_project(
            test_session,
            name="Duplicate Project"
        )
        
        # Try to create another with same name
        response = await authenticated_client.post(
            "/api/v1/projects/",
            json={
                "name": "Duplicate Project",
                "description": "Another project",
                "email_domains": ["test.com"]
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
    
    async def test_get_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting a project by ID"""
        # Create project
        project = await test_factory.create_test_project(test_session)
        
        response = await authenticated_client.get(f"/api/v1/projects/{project.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(project.id)
        assert data["name"] == project.name
        assert data["description"] == project.description
    
    async def test_get_project_not_found(self, authenticated_client: AsyncClient):
        """Test getting non-existent project"""
        response = await authenticated_client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    async def test_list_projects(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test listing all projects"""
        # Create multiple projects
        for i in range(3):
            await test_factory.create_test_project(
                test_session,
                name=f"Project {i}"
            )
        
        response = await authenticated_client.get("/api/v1/projects/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        
        assert len(data["items"]) >= 3
        assert data["total"] >= 3
    
    async def test_list_projects_with_pagination(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test project listing with pagination"""
        # Create multiple projects
        for i in range(10):
            await test_factory.create_test_project(
                test_session,
                name=f"Page Project {i}"
            )
        
        # Get first page
        response = await authenticated_client.get(
            "/api/v1/projects/?page=1&size=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) <= 5
        assert data["page"] == 1
        assert data["size"] == 5
        
        # Get second page
        response = await authenticated_client.get(
            "/api/v1/projects/?page=2&size=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
    
    async def test_list_active_projects(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test filtering projects by active status"""
        # Create active and inactive projects
        await test_factory.create_test_project(
            test_session,
            name="Active Project",
            is_active=True
        )
        await test_factory.create_test_project(
            test_session,
            name="Inactive Project",
            is_active=False
        )
        
        # Get only active projects
        response = await authenticated_client.get(
            "/api/v1/projects/?is_active=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for project in data["items"]:
            assert project["is_active"] == True
    
    async def test_update_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test updating a project"""
        # Create project
        project = await test_factory.create_test_project(test_session)
        
        update_data = {
            "description": "Updated description",
            "email_domains": ["updated.com", "new.com"],
            "auto_assign": False
        }
        
        response = await authenticated_client.put(
            f"/api/v1/projects/{project.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["description"] == update_data["description"]
        assert data["email_domains"] == update_data["email_domains"]
        assert data["auto_assign"] == update_data["auto_assign"]
        assert data["name"] == project.name  # Name unchanged
    
    async def test_patch_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test partial update of a project"""
        # Create project
        project = await test_factory.create_test_project(test_session)
        
        patch_data = {"description": "Patched description"}
        
        response = await authenticated_client.patch(
            f"/api/v1/projects/{project.id}",
            json=patch_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["description"] == patch_data["description"]
        assert data["name"] == project.name  # Unchanged
        assert data["email_domains"] == project.email_domains  # Unchanged
    
    async def test_delete_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test deleting a project"""
        # Create project
        project = await test_factory.create_test_project(test_session)
        
        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}"
        )
        
        assert response.status_code == 204
        
        # Verify project is deleted
        response = await authenticated_client.get(
            f"/api/v1/projects/{project.id}"
        )
        assert response.status_code == 404