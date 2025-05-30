"""
Test script to verify the complete MCP server setup.
"""

import asyncio
import httpx
import os
import pytest
from typing import AsyncGenerator, Generator
import docker
from docker.models.containers import Container

# Test constants
TEST_TIMEOUT = 30  # seconds
HEALTH_CHECK_INTERVAL = 2  # seconds

@pytest.fixture(scope="session")
def docker_client() -> Generator[docker.DockerClient, None, None]:
    """Create a Docker client."""
    client = docker.from_env()
    yield client
    client.close()

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

async def wait_for_service(url: str, timeout: int = TEST_TIMEOUT) -> bool:
    """Wait for a service to become available."""
    start_time = asyncio.get_event_loop().time()
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return True
            except httpx.RequestError:
                pass
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)

@pytest.mark.asyncio
async def test_docker_services(docker_client: docker.DockerClient):
    """Test that all Docker services are running correctly."""
    # Check PostgreSQL
    postgres = docker_client.containers.list(
        filters={"name": "doc_assembler_web-postgres-1"}
    )
    assert len(postgres) == 1, "PostgreSQL container not found"
    assert postgres[0].status == "running"
    
    # Check Redis
    redis = docker_client.containers.list(
        filters={"name": "doc_assembler_web-redis-1"}
    )
    assert len(redis) == 1, "Redis container not found"
    assert redis[0].status == "running"
    
    # Check MCP server
    mcp = docker_client.containers.list(
        filters={"name": "doc_assembler_web-mcp_server-1"}
    )
    assert len(mcp) == 1, "MCP server container not found"
    assert mcp[0].status == "running"

@pytest.mark.asyncio
async def test_mcp_server_health():
    """Test that the MCP server is healthy."""
    url = "http://localhost:8000/health"
    is_healthy = await wait_for_service(url)
    assert is_healthy, "MCP server health check failed"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_system_status():
    """Test the system status endpoint."""
    url = "http://localhost:8000/status"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "database" in data["components"]
        assert "playwright" in data["components"]
        assert data["components"]["database"] == "healthy"
        assert data["components"]["playwright"] == "healthy"

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection through the MCP server."""
    from mcp_server.models.database import get_session
    
    async with get_session() as session:
        result = await session.execute("SELECT 1")
        assert result.scalar() == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

