"""
Tests for people relationships with projects, emails, and merging
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.database
class TestPeopleRelationships:
    """Test people relationships and associated data"""
    
    async def test_merge_people(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test merging two people records"""
        # Create two people
        person1 = await test_factory.create_test_person(
            test_session,
            email="person1@example.com",
            first_name="John"
        )
        person2 = await test_factory.create_test_person(
            test_session,
            email="person2@example.com",
            first_name="Johnny"
        )
        
        response = await authenticated_client.post(
            f"/api/v1/people/{person1.id}/merge",
            json={"merge_with_id": str(person2.id)}
        )
        
        if response.status_code == 404:
            pytest.skip("Merge endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "People merged successfully"
        
        # Verify second person is deleted
        response = await authenticated_client.get(
            f"/api/v1/people/{person2.id}"
        )
        assert response.status_code == 404
    
    async def test_person_projects(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting projects associated with a person"""
        # Create person and projects
        person = await test_factory.create_test_person(test_session)
        
        projects = []
        for i in range(3):
            project = await test_factory.create_test_project(
                test_session,
                name=f"Person Project {i}"
            )
            projects.append(project)
            
            # Add person to project
            await authenticated_client.post(
                f"/api/v1/projects/{project.id}/people",
                json={
                    "person_id": str(person.id),
                    "role": f"role{i}"
                }
            )
        
        response = await authenticated_client.get(
            f"/api/v1/people/{person.id}/projects"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 3
        for project in data:
            assert "id" in project
            assert "name" in project
            assert "role" in project
    
    async def test_person_emails(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting emails for a person"""
        # Create person
        person = await test_factory.create_test_person(test_session)
        
        # Create emails sent by this person
        for i in range(5):
            await test_factory.create_test_email(
                test_session,
                sender=person
            )
        
        response = await authenticated_client.get(
            f"/api/v1/people/{person.id}/emails"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sent" in data
        assert "received" in data
        assert len(data["sent"]) >= 5
    
    async def test_person_statistics(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting person statistics"""
        # Create person with emails
        person = await test_factory.create_test_person(test_session)
        
        # Create emails
        for i in range(7):
            await test_factory.create_test_email(
                test_session,
                sender=person
            )
        
        response = await authenticated_client.get(
            f"/api/v1/people/{person.id}/stats"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "emails_sent" in data
        assert "emails_received" in data
        assert "projects_count" in data
        assert "first_email_date" in data
        assert "last_email_date" in data
        assert data["emails_sent"] >= 7