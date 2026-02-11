"""
Tests for Health Check Route
"""
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.health import router, determine_overall_status, check_service_health
from app.utils.http_client import ServiceClient


# ==================== Fixtures ====================


@pytest.fixture
def app():
    """Create test FastAPI app"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


# ==================== Helper Functions ====================


def create_mock_response(status_code: int, json_data: dict = None):
    """Create mock httpx.Response"""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data or {"status": "ok"}
    return response


# ==================== Tests for determine_overall_status ====================


class TestDetermineOverallStatus:
    """Tests for status determination logic"""

    def test_all_services_up_returns_healthy(self):
        """Test: All services up → 'healthy'"""
        services = {
            "user-service": {"status": "up", "response_time_ms": 45.23},
            "product-service": {"status": "up", "response_time_ms": 30.12}
        }

        status = determine_overall_status(services)

        assert status == "healthy"

    def test_some_services_down_returns_degraded(self):
        """Test: Some services down → 'degraded'"""
        services = {
            "user-service": {"status": "up", "response_time_ms": 45.23},
            "product-service": {"status": "down", "error": "Connection refused"}
        }

        status = determine_overall_status(services)

        assert status == "degraded"

    def test_all_services_down_returns_unhealthy(self):
        """Test: All services down → 'unhealthy'"""
        services = {
            "user-service": {"status": "down", "error": "Timeout"},
            "product-service": {"status": "down", "error": "Connection refused"}
        }

        status = determine_overall_status(services)

        assert status == "unhealthy"

    def test_no_services_configured_returns_healthy(self):
        """Test: No services configured → 'healthy'"""
        services = {}

        status = determine_overall_status(services)

        assert status == "healthy"


# ==================== Tests for check_service_health ====================


class TestCheckServiceHealth:
    """Tests for individual service health checks"""

    @pytest.mark.asyncio
    async def test_service_up_returns_status_and_response_time(self):
        """Test: Service up → status 'up' with response time"""
        client = ServiceClient()
        mock_response = create_mock_response(200, {"status": "healthy"})

        with patch.object(client, 'forward_request', new_callable=AsyncMock) as mock_forward:
            mock_forward.return_value = mock_response

            result = await check_service_health(
                "user-service",
                "http://user-service:8000",
                client
            )

            assert result["status"] == "up"
            assert "response_time_ms" in result
            assert result["url"] == "http://user-service:8000/health"

    @pytest.mark.asyncio
    async def test_service_timeout_returns_down(self):
        """Test 4: Service timeout → marked as 'down' with error 'Timeout'"""
        client = ServiceClient()

        with patch.object(client, 'forward_request', new_callable=AsyncMock) as mock_forward:
            # Simulate timeout by raising TimeoutError after delay
            async def timeout_side_effect(*args, **kwargs):
                await asyncio.sleep(3)  # Longer than HEALTH_CHECK_TIMEOUT (2s)
                return create_mock_response(200)

            mock_forward.side_effect = timeout_side_effect

            result = await check_service_health(
                "user-service",
                "http://user-service:8000",
                client
            )

            assert result["status"] == "down"
            assert result["error"] == "Timeout"
            assert result["url"] == "http://user-service:8000/health"

    @pytest.mark.asyncio
    async def test_service_returns_500_marked_as_down(self):
        """Test 5: Service returns 500 → marked as 'down'"""
        client = ServiceClient()
        mock_response = create_mock_response(500, {"error": "Internal server error"})

        with patch.object(client, 'forward_request', new_callable=AsyncMock) as mock_forward:
            mock_forward.return_value = mock_response

            result = await check_service_health(
                "user-service",
                "http://user-service:8000",
                client
            )

            assert result["status"] == "down"
            assert result["error"] == "Service error"
            assert result["url"] == "http://user-service:8000/health"

    @pytest.mark.asyncio
    async def test_connection_refused_returns_down(self):
        """Test: Connection refused → marked as 'down'"""
        client = ServiceClient()

        with patch.object(client, 'forward_request', new_callable=AsyncMock) as mock_forward:
            mock_forward.side_effect = httpx.ConnectError("Connection refused")

            result = await check_service_health(
                "user-service",
                "http://user-service:8000",
                client
            )

            assert result["status"] == "down"
            assert result["error"] == "Connection refused"
            assert result["url"] == "http://user-service:8000/health"


# ==================== Tests for /health endpoint ====================


class TestHealthEndpoint:
    """Tests for GET /health endpoint"""

    @pytest.mark.asyncio
    async def test_all_services_up_returns_healthy(self, client):
        """Test 1: All services up → status 'healthy'"""
        mock_response = create_mock_response(200, {"status": "healthy"})

        with patch('app.routes.health.settings') as mock_settings:
            mock_settings.user_service_url = "http://user-service:8000"
            mock_settings.product_service_url = None
            mock_settings.order_service_url = None
            mock_settings.notification_service_url = None

            with patch.object(ServiceClient, 'forward_request', new_callable=AsyncMock) as mock_forward:
                mock_forward.return_value = mock_response

                response = client.get("/health")

                assert response.status_code == 200
                data = response.json()

                assert data["status"] == "healthy"
                assert data["gateway"]["status"] == "up"
                assert "timestamp" in data
                assert data["timestamp"].endswith("Z")
                assert "user-service" in data["services"]
                assert data["services"]["user-service"]["status"] == "up"

    @pytest.mark.asyncio
    async def test_some_services_down_returns_degraded(self, client):
        """Test 2: Some services down → status 'degraded'"""
        mock_response_up = create_mock_response(200, {"status": "healthy"})
        mock_response_down = (503, {"error": "Service unavailable", "detail": "Connection failed"})

        with patch('app.routes.health.settings') as mock_settings:
            mock_settings.user_service_url = "http://user-service:8000"
            mock_settings.product_service_url = "http://product-service:8001"
            mock_settings.order_service_url = None
            mock_settings.notification_service_url = None

            with patch.object(ServiceClient, 'forward_request', new_callable=AsyncMock) as mock_forward:
                # First call returns success, second returns error tuple
                mock_forward.side_effect = [mock_response_up, mock_response_down]

                response = client.get("/health")

                assert response.status_code == 200
                data = response.json()

                assert data["status"] == "degraded"
                assert data["gateway"]["status"] == "up"
                assert data["services"]["user-service"]["status"] == "up"
                assert data["services"]["product-service"]["status"] == "down"

    @pytest.mark.asyncio
    async def test_all_services_down_returns_unhealthy(self, client):
        """Test 3: All services down → status 'unhealthy'"""
        mock_response_down = (503, {"error": "Service unavailable", "detail": "Connection refused"})

        with patch('app.routes.health.settings') as mock_settings:
            mock_settings.user_service_url = "http://user-service:8000"
            mock_settings.product_service_url = "http://product-service:8001"
            mock_settings.order_service_url = None
            mock_settings.notification_service_url = None

            with patch.object(ServiceClient, 'forward_request', new_callable=AsyncMock) as mock_forward:
                mock_forward.return_value = mock_response_down

                response = client.get("/health")

                assert response.status_code == 200
                data = response.json()

                assert data["status"] == "unhealthy"
                assert data["gateway"]["status"] == "up"
                assert data["services"]["user-service"]["status"] == "down"
                assert data["services"]["product-service"]["status"] == "down"

    @pytest.mark.asyncio
    async def test_only_user_service_configured_works(self, client):
        """Test 6: Only user-service configured (others None) → works correctly"""
        mock_response = create_mock_response(200, {"status": "healthy"})

        with patch('app.routes.health.settings') as mock_settings:
            mock_settings.user_service_url = "http://user-service:8000"
            mock_settings.product_service_url = None
            mock_settings.order_service_url = None
            mock_settings.notification_service_url = None

            with patch.object(ServiceClient, 'forward_request', new_callable=AsyncMock) as mock_forward:
                mock_forward.return_value = mock_response

                response = client.get("/health")

                assert response.status_code == 200
                data = response.json()

                assert data["status"] == "healthy"
                assert len(data["services"]) == 1
                assert "user-service" in data["services"]
                assert "product-service" not in data["services"]
                assert "order-service" not in data["services"]
                assert "notification-service" not in data["services"]
