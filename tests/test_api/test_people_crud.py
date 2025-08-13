"""
Tests for people CRUD operations
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.database
class TestPeopleCRUD:
    """Test people CRUD operations"""
    
    async def test_create_person(self, authenticated_client: AsyncClient, test_person_data):
        """Test creating a new person"""
        response = await authenticated_client.post(
            "/api/v1/people/",
            json=test_person_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == test_person_data["email"]
        assert data["first_name"] == test_person_data["first_name"]
        assert data["last_name"] == test_person_data["last_name"]
        assert data["organization"] == test_person_data["organization"]
        assert data["full_name"] == f"{test_person_data['first_name']} {test_person_data['last_name']}"
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_person_duplicate_email(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test creating person with duplicate email"""
        # Create first person
        await test_factory.create_test_person(
            test_session,
            email="duplicate@example.com"
        )
        
        # Try to create another with same email
        response = await authenticated_client.post(
            "/api/v1/people/",
            json={
                "email": "duplicate@example.com",
                "first_name": "Another",
                "last_name": "Person"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
    
    async def test_get_person(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting a person by ID"""
        # Create person
        person = await test_factory.create_test_person(test_session)
        
        response = await authenticated_client.get(f"/api/v1/people/{person.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(person.id)
        assert data["email"] == person.email
        assert data["first_name"] == person.first_name
        assert data["last_name"] == person.last_name
    
    async def test_get_person_by_email(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test getting a person by email address"""
        # Create person
        person = await test_factory.create_test_person(
            test_session,
            email="findme@example.com"
        )
        
        response = await authenticated_client.get(
            "/api/v1/people/by-email/findme@example.com"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(person.id)
        assert data["email"] == "findme@example.com"
    
    async def test_get_person_not_found(self, authenticated_client: AsyncClient):
        """Test getting non-existent person"""
        response = await authenticated_client.get(
            "/api/v1/people/00000000-0000-0000-0000-000000000000"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    async def test_list_people(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test listing all people"""
        # Create multiple people
        for i in range(5):
            await test_factory.create_test_person(
                test_session,
                email=f"person{i}@example.com",
                first_name=f"Person{i}"
            )
        
        response = await authenticated_client.get("/api/v1/people/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        
        assert len(data["items"]) >= 5
        assert data["total"] >= 5
    
    async def test_list_people_with_pagination(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test people listing with pagination"""
        # Create multiple people
        for i in range(12):
            await test_factory.create_test_person(
                test_session,
                email=f"page{i}@example.com"
            )
        
        # Get first page
        response = await authenticated_client.get(
            "/api/v1/people/?page=1&size=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) <= 5
        assert data["page"] == 1
        assert data["size"] == 5
    
    async def test_list_active_people(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test filtering people by active status"""
        # Create active and inactive people
        await test_factory.create_test_person(
            test_session,
            email="active@example.com",
            is_active=True
        )
        await test_factory.create_test_person(
            test_session,
            email="inactive@example.com",
            is_active=False
        )
        
        # Get only active people
        response = await authenticated_client.get(
            "/api/v1/people/?is_active=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for person in data["items"]:
            assert person["is_active"] == True
    
    async def test_list_external_people(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test filtering people by external status"""
        # Create internal and external people
        await test_factory.create_test_person(
            test_session,
            email="internal@company.com",
            is_external=False
        )
        await test_factory.create_test_person(
            test_session,
            email="external@other.com",
            is_external=True
        )
        
        # Get only external people
        response = await authenticated_client.get(
            "/api/v1/people/?is_external=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for person in data["items"]:
            assert person["is_external"] == True
    
    async def test_update_person(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test updating a person"""
        # Create person
        person = await test_factory.create_test_person(test_session)
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "organization": "New Org",
            "phone": "+1-555-9999"
        }
        
        response = await authenticated_client.put(
            f"/api/v1/people/{person.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["organization"] == update_data["organization"]
        assert data["phone"] == update_data["phone"]
        assert data["email"] == person.email  # Email unchanged
    
    async def test_patch_person(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test partial update of a person"""
        # Create person
        person = await test_factory.create_test_person(test_session)
        
        patch_data = {"phone": "+1-555-1234"}
        
        response = await authenticated_client.patch(
            f"/api/v1/people/{person.id}",
            json=patch_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["phone"] == patch_data["phone"]
        assert data["first_name"] == person.first_name  # Unchanged
        assert data["last_name"] == person.last_name  # Unchanged
    
    async def test_delete_person(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test deleting a person"""
        # Create person
        person = await test_factory.create_test_person(test_session)
        
        response = await authenticated_client.delete(
            f"/api/v1/people/{person.id}"
        )
        
        assert response.status_code == 204
        
        # Verify person is deleted
        response = await authenticated_client.get(
            f"/api/v1/people/{person.id}"
        )
        assert response.status_code == 404