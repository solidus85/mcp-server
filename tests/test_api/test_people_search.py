"""
Tests for people search functionality
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.database
class TestPeopleSearch:
    """Test people search functionality"""
    
    async def test_search_people_by_name(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test searching people by name"""
        # Create people with different names
        await test_factory.create_test_person(
            test_session,
            email="john.smith@example.com",
            first_name="John",
            last_name="Smith"
        )
        await test_factory.create_test_person(
            test_session,
            email="jane.smith@example.com",
            first_name="Jane",
            last_name="Smith"
        )
        await test_factory.create_test_person(
            test_session,
            email="bob.jones@example.com",
            first_name="Bob",
            last_name="Jones"
        )
        
        response = await authenticated_client.get(
            "/api/v1/people/search?q=Smith"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        for person in data:
            assert "Smith" in person["full_name"]
    
    async def test_search_people_by_organization(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test searching people by organization"""
        # Create people with different organizations
        await test_factory.create_test_person(
            test_session,
            email="emp1@example.com",
            organization="Tech Corp"
        )
        await test_factory.create_test_person(
            test_session,
            email="emp2@example.com",
            organization="Tech Corp"
        )
        await test_factory.create_test_person(
            test_session,
            email="emp3@example.com",
            organization="Other Inc"
        )
        
        response = await authenticated_client.get(
            "/api/v1/people/search?organization=Tech Corp"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        for person in data:
            assert person["organization"] == "Tech Corp"
    
    async def test_search_people_by_email_domain(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test searching people by email domain"""
        # Create people with different email domains
        await test_factory.create_test_person(
            test_session,
            email="user1@company.com"
        )
        await test_factory.create_test_person(
            test_session,
            email="user2@company.com"
        )
        await test_factory.create_test_person(
            test_session,
            email="user3@other.org"
        )
        
        response = await authenticated_client.get(
            "/api/v1/people/search?domain=company.com"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        for person in data:
            assert person["email"].endswith("@company.com")
    
    async def test_autocomplete_people(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_factory
    ):
        """Test people autocomplete for UI"""
        # Create people
        await test_factory.create_test_person(
            test_session,
            email="alice@example.com",
            first_name="Alice"
        )
        await test_factory.create_test_person(
            test_session,
            email="albert@example.com",
            first_name="Albert"
        )
        
        response = await authenticated_client.get(
            "/api/v1/people/autocomplete?prefix=Al"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        for person in data:
            assert person["first_name"].startswith("Al")
            assert "id" in person
            assert "email" in person
            assert "display_name" in person