"""
Tests for JWT Authentication Middleware
"""
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from jose import jwt
from app.middleware.auth import verify_jwt_token, get_current_user
from app.config.settings import settings


# ==================== Helper Functions ====================


def create_test_token(
    user_id: str = "user123",
    exp_delta: timedelta = timedelta(hours=1),
    secret_key: str = None,
    algorithm: str = None,
    include_sub: bool = True
) -> str:
    """Create JWT token for testing"""
    if secret_key is None:
        secret_key = settings.jwt_secret_key
    if algorithm is None:
        algorithm = settings.jwt_algorithm

    payload = {
        "exp": datetime.utcnow() + exp_delta
    }

    if include_sub:
        payload["sub"] = user_id

    return jwt.encode(payload, secret_key, algorithm=algorithm)


class MockRequest:
    """Mock FastAPI Request object"""
    def __init__(self, headers: dict = None):
        self.headers = headers or {}
        self.state = type('State', (), {})()


# ==================== Tests for verify_jwt_token ====================


class TestVerifyJWTToken:
    """Tests for verify_jwt_token function"""

    def test_valid_token_returns_user_id(self):
        """Test 1: Valid token returns user_id"""
        token = create_test_token(user_id="user123")

        user_id = verify_jwt_token(token)

        assert user_id == "user123"
        assert isinstance(user_id, str)

    def test_expired_token_raises_401(self):
        """Test 2: Expired token raises 401 'Token expired'"""
        # Create expired token (1 hour ago)
        token = create_test_token(exp_delta=timedelta(hours=-1))

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token expired"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    def test_invalid_signature_raises_401(self):
        """Test 3: Invalid signature raises 401 'Invalid token'"""
        # Create token with wrong secret key
        token = create_test_token(secret_key="wrong-secret-key")

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    def test_missing_sub_claim_raises_401(self):
        """Test 6: Token with missing 'sub' claim raises 401"""
        # Create token without 'sub' claim
        token = create_test_token(include_sub=False)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token payload"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    def test_wrong_algorithm_raises_401(self):
        """Test 7: Token with wrong algorithm raises 401"""
        # Create token with different algorithm
        token = create_test_token(algorithm="HS512")

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


# ==================== Tests for get_current_user ====================


class TestGetCurrentUser:
    """Tests for get_current_user dependency"""

    @pytest.mark.asyncio
    async def test_missing_authorization_header_raises_401(self):
        """Test 4: Missing Authorization header raises 401"""
        request = MockRequest(headers={})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authorization header missing"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_invalid_format_no_bearer_raises_401(self):
        """Test 5: Invalid format (no 'Bearer ') raises 401"""
        token = create_test_token()
        request = MockRequest(headers={"Authorization": token})  # Missing "Bearer "

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authorization format"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_valid_token_returns_user_id_and_stores_in_state(self):
        """Test: Valid token returns user_id and stores in request.state"""
        token = create_test_token(user_id="user456")
        request = MockRequest(headers={"Authorization": f"Bearer {token}"})

        user_id = await get_current_user(request)

        assert user_id == "user456"
        assert isinstance(user_id, str)
        assert request.state.user_id == "user456"
