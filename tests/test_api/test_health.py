"""
Tests for health check endpoints
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check and monitoring endpoints"""
    
    async def test_health_check(self, test_client: AsyncClient):
        """Test basic health check endpoint"""
        response = await test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    async def test_health_check_detailed(self, test_client: AsyncClient):
        """Test detailed health check with component status"""
        response = await test_client.get("/api/v1/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in data
        
        # Check component statuses
        components = data["components"]
        assert "database" in components
        assert "vector_db" in components
        assert "mcp_server" in components
        
        for component in components.values():
            assert "status" in component
            assert component["status"] in ["healthy", "degraded", "unhealthy"]
    
    async def test_readiness_check(self, test_client: AsyncClient):
        """Test readiness endpoint for Kubernetes"""
        response = await test_client.get("/api/v1/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] in [True, False]
        
        if not data["ready"]:
            assert "reason" in data
    
    async def test_liveness_check(self, test_client: AsyncClient):
        """Test liveness endpoint for Kubernetes"""
        response = await test_client.get("/api/v1/alive")
        
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] == True
    
    async def test_metrics_endpoint(self, test_client: AsyncClient):
        """Test metrics endpoint for monitoring"""
        response = await test_client.get("/api/v1/metrics")
        
        # May require authentication
        if response.status_code == 401:
            pytest.skip("Metrics endpoint requires authentication")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "requests" in data
        assert "errors" in data
        assert "latency" in data
        assert "database" in data
    
    async def test_version_endpoint(self, test_client: AsyncClient):
        """Test version information endpoint"""
        response = await test_client.get("/api/v1/version")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "version" in data
        assert "api_version" in data
        assert "build_date" in data
        assert "git_commit" in data
    
    async def test_ping_endpoint(self, test_client: AsyncClient):
        """Test simple ping endpoint"""
        response = await test_client.get("/api/v1/ping")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"
        assert "timestamp" in data


@pytest.mark.asyncio
class TestHealthEndpointsAuthenticated:
    """Test health endpoints that require authentication"""
    
    async def test_system_info_authenticated(self, authenticated_client: AsyncClient):
        """Test system info endpoint with authentication"""
        response = await authenticated_client.get("/api/v1/system/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "uptime" in data
    
    async def test_database_stats_authenticated(self, authenticated_client: AsyncClient):
        """Test database statistics endpoint"""
        response = await authenticated_client.get("/api/v1/system/database/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "connections" in data
        assert "active_queries" in data
        assert "table_sizes" in data
    
    async def test_cache_stats_authenticated(self, authenticated_client: AsyncClient):
        """Test cache statistics endpoint"""
        response = await authenticated_client.get("/api/v1/system/cache/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "hits" in data
        assert "misses" in data
        assert "size" in data
        assert "evictions" in data