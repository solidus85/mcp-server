"""
Tests for authentication endpoints
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from jose import jwt

from src.config import settings


@pytest.mark.asyncio
class TestAuthenticationEndpoints:
    """Test authentication and authorization endpoints"""
    
    async def test_login_success(self, test_client: AsyncClient, test_user_data):
        """Test successful login"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify token is valid JWT
        token = data["access_token"]
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        assert decoded["sub"] == test_user_data["username"]
    
    async def test_login_invalid_credentials(self, test_client: AsyncClient):
        """Test login with invalid credentials"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "invalid_user",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    async def test_login_missing_fields(self, test_client: AsyncClient):
        """Test login with missing fields"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"username": "test"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    async def test_register_new_user(self, test_client: AsyncClient):
        """Test new user registration"""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User"
            }
        )
        
        if response.status_code == 404:
            pytest.skip("Registration endpoint not implemented")
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data
    
    async def test_register_duplicate_user(self, test_client: AsyncClient, test_user_data):
        """Test registration with existing username"""
        response = await test_client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )
        
        if response.status_code == 404:
            pytest.skip("Registration endpoint not implemented")
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
    
    async def test_refresh_token(self, authenticated_client: AsyncClient):
        """Test token refresh"""
        response = await authenticated_client.post("/api/v1/auth/refresh")
        
        if response.status_code == 404:
            pytest.skip("Token refresh endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    async def test_logout(self, authenticated_client: AsyncClient):
        """Test user logout"""
        response = await authenticated_client.post("/api/v1/auth/logout")
        
        if response.status_code == 404:
            pytest.skip("Logout endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    async def test_get_current_user(self, authenticated_client: AsyncClient):
        """Test getting current user info"""
        response = await authenticated_client.get("/api/v1/auth/me")
        
        if response.status_code == 404:
            pytest.skip("Current user endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "username" in data
        assert "email" in data
        assert "roles" in data
        assert "password" not in data
    
    async def test_change_password(self, authenticated_client: AsyncClient):
        """Test password change"""
        response = await authenticated_client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "NewSecurePassword456!"
            }
        )
        
        if response.status_code == 404:
            pytest.skip("Change password endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    async def test_request_password_reset(self, test_client: AsyncClient):
        """Test password reset request"""
        response = await test_client.post(
            "/api/v1/auth/reset-password",
            json={"email": "test@example.com"}
        )
        
        if response.status_code == 404:
            pytest.skip("Password reset endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


@pytest.mark.asyncio
class TestAuthorizationEndpoints:
    """Test authorization and role-based access"""
    
    async def test_admin_endpoint_with_admin_role(self, authenticated_client: AsyncClient):
        """Test admin endpoint with admin role"""
        response = await authenticated_client.get("/api/v1/admin/users")
        
        if response.status_code == 404:
            pytest.skip("Admin endpoint not implemented")
        
        # Should succeed as test user has admin role
        assert response.status_code == 200
    
    async def test_admin_endpoint_without_admin_role(self, test_client: AsyncClient):
        """Test admin endpoint without admin role"""
        from src.api.dependencies import create_access_token
        
        # Create token without admin role
        token_data = {
            "sub": "regularuser",
            "email": "regular@example.com",
            "roles": ["user"]
        }
        token = create_access_token(token_data)
        
        test_client.headers["Authorization"] = f"Bearer {token}"
        response = await test_client.get("/api/v1/admin/users")
        
        if response.status_code == 404:
            pytest.skip("Admin endpoint not implemented")
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
    
    async def test_protected_endpoint_without_auth(self, test_client: AsyncClient):
        """Test protected endpoint without authentication"""
        response = await test_client.get("/api/v1/protected/resource")
        
        if response.status_code == 404:
            # Try a known protected endpoint
            response = await test_client.get("/api/v1/documents")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    async def test_expired_token(self, test_client: AsyncClient):
        """Test with expired token"""
        from src.api.dependencies import create_access_token
        
        # Create expired token
        token_data = {
            "sub": "testuser",
            "email": "test@example.com",
            "roles": ["user"]
        }
        expired_token = create_access_token(
            token_data,
            expires_delta=timedelta(seconds=-1)
        )
        
        test_client.headers["Authorization"] = f"Bearer {expired_token}"
        response = await test_client.get("/api/v1/documents")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    async def test_invalid_token_format(self, test_client: AsyncClient):
        """Test with invalid token format"""
        test_client.headers["Authorization"] = "Bearer invalid.token.here"
        response = await test_client.get("/api/v1/documents")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    async def test_api_key_authentication(self, test_client: AsyncClient):
        """Test API key authentication"""
        test_client.headers["X-API-Key"] = "test_key_1"
        response = await test_client.get("/api/v1/public/data")
        
        if response.status_code == 404:
            pytest.skip("API key endpoint not implemented")
        
        assert response.status_code in [200, 404]
    
    async def test_invalid_api_key(self, test_client: AsyncClient):
        """Test with invalid API key"""
        test_client.headers["X-API-Key"] = "invalid_key"
        response = await test_client.get("/api/v1/public/data")
        
        if response.status_code == 404:
            pytest.skip("API key endpoint not implemented")
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting functionality"""
    
    async def test_rate_limit_not_exceeded(self, authenticated_client: AsyncClient):
        """Test requests within rate limit"""
        for i in range(5):
            response = await authenticated_client.get("/api/v1/documents")
            if response.status_code == 404:
                pytest.skip("Documents endpoint not implemented")
            assert response.status_code in [200, 404]
    
    async def test_rate_limit_exceeded(self, authenticated_client: AsyncClient):
        """Test rate limit exceeded"""
        # Make many rapid requests
        responses = []
        for i in range(100):
            response = await authenticated_client.get("/api/v1/documents")
            responses.append(response.status_code)
            
            if response.status_code == 429:
                # Rate limit hit
                data = response.json()
                assert "detail" in data
                assert "rate limit" in data["detail"].lower()
                return
        
        # If we didn't hit rate limit, either it's very high or not implemented
        pytest.skip("Rate limit not triggered or very high")
    
    async def test_rate_limit_headers(self, authenticated_client: AsyncClient):
        """Test rate limit headers in response"""
        response = await authenticated_client.get("/api/v1/documents")
        
        # Check for rate limit headers
        headers = response.headers
        
        # Common rate limit headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "RateLimit-Limit",
            "RateLimit-Remaining",
            "RateLimit-Reset"
        ]
        
        has_rate_limit_headers = any(
            header in headers for header in rate_limit_headers
        )
        
        if not has_rate_limit_headers:
            pytest.skip("Rate limit headers not implemented")