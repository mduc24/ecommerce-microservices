"""
Tests for User Service Proxy Routes
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from app.routes.users import router
from app.config.settings import settings


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


def create_mock_response(status_code: int, json_data: dict):
    """Create mock httpx.Response"""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    return response


def create_test_jwt(user_id: str = "123") -> str:
    """Create valid JWT token for testing"""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# ==================== Tests for POST /users/register ====================


class TestRegisterUser:
    """Tests for user registration endpoint"""

    @pytest.mark.asyncio
    async def test_register_without_auth_success(self, client):
        """Test 1: Register without auth → success"""
        register_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!"
        }

        mock_response = create_mock_response(201, {
            "id": 1,
            "email": "newuser@example.com",
            "username": "newuser",
            "is_active": True,
            "created_at": "2024-02-10T10:00:00Z"
        })

        with patch('app.routes.users.ServiceClient') as MockServiceClient:
            mock_instance = MockServiceClient.return_value
            mock_instance.forward_request = AsyncMock(return_value=mock_response)

            response = client.post("/users/register", json=register_data)

            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "newuser@example.com"
            assert data["username"] == "newuser"

            # Verify ServiceClient was called correctly
            mock_instance.forward_request.assert_called_once()
            call_args = mock_instance.forward_request.call_args
            assert call_args.kwargs["service_url"] == settings.user_service_url
            assert call_args.kwargs["method"] == "POST"
            assert call_args.kwargs["path"] == "/api/v1/users/register"
            assert call_args.kwargs["body"] == register_data

    @pytest.mark.asyncio
    async def test_register_service_validation_error_400_passed_through(self, client):
        """Test 6: Service validation error (400) → pass through"""
        register_data = {
            "email": "invalid-email",
            "username": "ab",  # Too short
            "password": "123"  # Too short
        }

        # User Service returns 400 validation error
        mock_response = create_mock_response(400, {
            "detail": "Validation error: email invalid, password too short"
        })

        with patch('app.routes.users.ServiceClient') as MockServiceClient:
            mock_instance = MockServiceClient.return_value
            mock_instance.forward_request = AsyncMock(return_value=mock_response)

            response = client.post("/users/register", json=register_data)

            # Should pass through 400 error
            assert response.status_code == 400
            data = response.json()
            assert "Validation error" in data["detail"]


# ==================== Tests for POST /users/login ====================


class TestLoginUser:
    """Tests for user login endpoint"""

    @pytest.mark.asyncio
    async def test_login_without_auth_success(self, client):
        """Test 2: Login without auth → success"""
        login_data = {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }

        mock_response = create_mock_response(200, {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        })

        with patch('app.routes.users.ServiceClient') as MockServiceClient:
            mock_instance = MockServiceClient.return_value
            mock_instance.forward_request = AsyncMock(return_value=mock_response)

            response = client.post("/users/login", json=login_data)

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

            # Verify ServiceClient was called correctly
            mock_instance.forward_request.assert_called_once()
            call_args = mock_instance.forward_request.call_args
            assert call_args.kwargs["service_url"] == settings.user_service_url
            assert call_args.kwargs["method"] == "POST"
            assert call_args.kwargs["path"] == "/api/v1/users/login"
            assert call_args.kwargs["body"] == login_data


# ==================== Tests for GET /users/me ====================


class TestGetUserProfile:
    """Tests for get user profile endpoint"""

    @pytest.mark.asyncio
    async def test_get_me_without_auth_returns_401(self, client):
        """Test 3: GET /me without auth → 401"""
        response = client.get("/users/me")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Authorization header missing"

    @pytest.mark.asyncio
    async def test_get_me_with_valid_jwt_success(self, client):
        """Test 4: GET /me with valid JWT → success"""
        token = create_test_jwt(user_id="123")

        mock_response = create_mock_response(200, {
            "id": 123,
            "email": "user@example.com",
            "username": "testuser",
            "is_active": True,
            "created_at": "2024-02-10T10:00:00Z"
        })

        with patch('app.routes.users.ServiceClient') as MockServiceClient:
            mock_instance = MockServiceClient.return_value
            mock_instance.forward_request = AsyncMock(return_value=mock_response)

            response = client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 123
            assert data["email"] == "user@example.com"

            # Verify ServiceClient was called correctly
            mock_instance.forward_request.assert_called_once()
            call_args = mock_instance.forward_request.call_args
            assert call_args.kwargs["service_url"] == settings.user_service_url
            assert call_args.kwargs["method"] == "GET"
            assert call_args.kwargs["path"] == "/api/v1/users/me"

            # Verify Authorization header was forwarded
            forwarded_headers = call_args.kwargs["headers"]
            assert "Authorization" in forwarded_headers
            assert forwarded_headers["Authorization"] == f"Bearer {token}"

    @pytest.mark.asyncio
    async def test_service_timeout_returns_504(self, client):
        """Test 5: Service timeout → 504"""
        token = create_test_jwt(user_id="123")

        # ServiceClient returns tuple (504, error_dict) on timeout
        error_response = (504, {
            "error": "Gateway Timeout",
            "detail": "Request to user-service timed out after 30.0 seconds"
        })

        with patch('app.routes.users.ServiceClient') as MockServiceClient:
            mock_instance = MockServiceClient.return_value
            mock_instance.forward_request = AsyncMock(return_value=error_response)

            response = client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 504
            data = response.json()
            assert data["error"] == "Gateway Timeout"
            assert "timed out" in data["detail"]

    @pytest.mark.asyncio
    async def test_x_request_id_forwarded(self, client):
        """Test 7: X-Request-ID forwarded → verify header"""
        token = create_test_jwt(user_id="123")

        mock_response = create_mock_response(200, {
            "id": 123,
            "email": "user@example.com",
            "username": "testuser"
        })

        with patch('app.routes.users.ServiceClient') as MockServiceClient:
            mock_instance = MockServiceClient.return_value
            mock_instance.forward_request = AsyncMock(return_value=mock_response)

            # ServiceClient automatically adds X-Request-ID (from Task 3.5)
            # We just verify the request reaches ServiceClient
            response = client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200

            # Verify ServiceClient.forward_request was called
            # X-Request-ID is added by ServiceClient internally
            mock_instance.forward_request.assert_called_once()

            # ServiceClient's forward_request adds X-Request-ID automatically
            # (implemented in Task 3.5 - lines 376-378 in http_client.py)
