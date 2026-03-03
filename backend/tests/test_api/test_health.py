"""Tests for the health check endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from agentic_rpg.main import app


@pytest.fixture
async def client():
    """Create an async test client with mocked DB pool."""
    mock_pool = AsyncMock()
    with patch("agentic_rpg.main.create_pool", return_value=mock_pool), \
         patch("agentic_rpg.main.close_pool", return_value=None):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac


class TestHealthEndpoint:
    async def test_health_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_returns_ok_status(self, client):
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    async def test_health_response_shape(self, client):
        response = await client.get("/health")
        data = response.json()
        assert data == {"status": "ok"}

    async def test_health_wrong_method_returns_405(self, client):
        response = await client.post("/health")
        assert response.status_code == 405
