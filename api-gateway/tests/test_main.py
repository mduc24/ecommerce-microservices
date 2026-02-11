"""
Tests for Main Application
"""
import logging
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import settings


# ==================== Fixtures ====================


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


# ==================== Tests for App Configuration ====================


class TestAppConfiguration:
    """Tests for FastAPI app configuration"""

    def test_app_has_correct_title_and_version(self):
        """Test 1: App has correct title/version"""
        assert app.title == "E-commerce API Gateway"
        assert app.version == settings.api_version
        assert app.description == "Single entry point for microservices"

    def test_app_has_docs_endpoints(self):
        """Test: App has Swagger UI and ReDoc endpoints"""
        # OpenAPI schema should be available
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200

        response = client.get("/redoc")
        assert response.status_code == 200

        response = client.get("/openapi.json")
        assert response.status_code == 200


# ==================== Tests for Root Endpoint ====================


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_endpoint_returns_gateway_info_with_timestamp(self, client):
        """Test 2: Root endpoint returns gateway info (with timestamp)"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "E-commerce API Gateway"
        assert data["version"] == settings.api_version
        assert data["status"] == "running"
        assert data["environment"] == settings.environment

        # Verify timestamp is ISO 8601 with UTC
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")


# ==================== Tests for Router Registration ====================


class TestRouterRegistration:
    """Tests for router registration"""

    def test_health_endpoint_accessible(self, client):
        """Test 3: Health endpoint accessible"""
        # Mock ServiceClient to avoid actual service calls
        with patch('app.routes.health.ServiceClient') as MockServiceClient:
            mock_instance = MockServiceClient.return_value
            mock_instance.forward_request = AsyncMock(return_value=(200, {"status": "ok"}))

            response = client.get("/health")

            # Should be accessible (may return 200 or other status based on services)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "gateway" in data

    def test_users_endpoints_accessible(self, client):
        """Test 4: Users endpoints accessible"""
        # Test register endpoint exists (will fail without body, but accessible)
        response = client.post("/users/register")
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

        # Test login endpoint exists
        response = client.post("/users/login")
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

        # Test /me endpoint exists (will fail without auth)
        response = client.get("/users/me")
        # Should return 401 (unauthorized), not 404 (not found)
        assert response.status_code == 401


# ==================== Tests for CORS ====================


class TestCORS:
    """Tests for CORS middleware"""

    def test_cors_headers_present(self, client):
        """Test 5: CORS headers present"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


# ==================== Tests for Exception Handler ====================


class TestGlobalExceptionHandler:
    """Tests for global exception handler"""

    def test_global_exception_handler_returns_500(self, client):
        """Test 6: Global exception handler returns 500"""
        # Create a route that raises an exception
        @app.get("/test-error")
        async def test_error():
            raise ValueError("Test exception")

        response = client.get("/test-error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal server error"
        # Should NOT leak exception details
        assert "ValueError" not in str(data)
        assert "Test exception" not in str(data)

        # Clean up
        app.routes = [r for r in app.routes if r.path != "/test-error"]

    def test_exception_logged_with_request_id(self, client, caplog):
        """Test 7: Exception logged with request_id"""
        # Create a route that raises an exception
        @app.get("/test-error-logging")
        async def test_error_logging():
            raise RuntimeError("Test logging exception")

        with caplog.at_level(logging.ERROR):
            response = client.get(
                "/test-error-logging",
                headers={"X-Request-ID": "test-request-123"}
            )

            assert response.status_code == 500

            # Check that exception was logged
            assert len(caplog.records) > 0

            # Find the error log record
            error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
            assert len(error_logs) > 0

            # Verify log contains exception info
            log_message = error_logs[0].message
            assert "Unhandled exception" in log_message
            assert "RuntimeError" in log_message

        # Clean up
        app.routes = [r for r in app.routes if r.path != "/test-error-logging"]


# ==================== Tests for Startup/Shutdown Events ====================


class TestStartupShutdown:
    """Tests for startup and shutdown events"""

    @pytest.mark.asyncio
    async def test_startup_event_logs_configuration(self, caplog):
        """Test: Startup event logs configuration"""
        from app.main import startup_event

        with caplog.at_level(logging.INFO):
            await startup_event()

            # Check startup logs
            log_messages = [r.message for r in caplog.records]

            assert any("API Gateway started" in msg for msg in log_messages)
            assert any(f"Version: {settings.api_version}" in msg for msg in log_messages)
            assert any(f"Environment: {settings.environment}" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_shutdown_event_closes_service_client(self, caplog):
        """Test: Shutdown event closes ServiceClient"""
        with patch('app.main.service_client') as mock_service_client:
            mock_service_client.close = AsyncMock()

            from app.main import shutdown_event

            with caplog.at_level(logging.INFO):
                await shutdown_event()

                # Verify ServiceClient.close() was called
                mock_service_client.close.assert_called_once()

                # Check shutdown logs
                log_messages = [r.message for r in caplog.records]
                assert any("API Gateway shutting down" in msg for msg in log_messages)
                assert any("ServiceClient closed successfully" in msg for msg in log_messages)
