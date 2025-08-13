"""
Tests for project people management
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.database
class TestProjectPeople:
    """Test project people management"""
    
    async def test_add_person_to_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test adding a person to a project"""
        # Create project and person
        project = await test_factory.create_test_project(test_session)
        person = await test_factory.create_test_person(test_session)
        
        response = await authenticated_client.post(
            f"/api/v1/projects/{project.id}/people",
            json={
                "person_id": str(person.id),
                "role": "developer"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Person added to project"
    
    async def test_remove_person_from_project(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test removing a person from a project"""
        # Create project and person
        project = await test_factory.create_test_project(test_session)
        person = await test_factory.create_test_person(test_session)
        
        # Add person first
        await authenticated_client.post(
            f"/api/v1/projects/{project.id}/people",
            json={
                "person_id": str(person.id),
                "role": "developer"
            }
        )
        
        # Remove person
        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/people/{person.id}"
        )
        
        assert response.status_code == 204
    
    async def test_list_project_people(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test listing people in a project"""
        # Create project and people
        project = await test_factory.create_test_project(test_session)
        
        for i in range(3):
            person = await test_factory.create_test_person(
                test_session,
                email=f"person{i}@test.com"
            )
            await authenticated_client.post(
                f"/api/v1/projects/{project.id}/people",
                json={
                    "person_id": str(person.id),
                    "role": f"role{i}"
                }
            )
        
        response = await authenticated_client.get(
            f"/api/v1/projects/{project.id}/people"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 3
        for person in data:
            assert "id" in person
            assert "email" in person
            assert "role" in person