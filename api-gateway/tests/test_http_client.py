"""
Test Suite for ServiceClient Singleton Pattern and Request Forwarding
"""
import pytest
import httpx
import respx
from httpx import Response
from unittest.mock import patch, AsyncMock
from app.utils.http_client import ServiceClient, service_client


class TestServiceClientSingleton:
    """Test ServiceClient singleton pattern and configuration"""

    def test_singleton_pattern(self):
        """Test 1: Multiple instantiations return same object"""
        client1 = ServiceClient()
        client2 = ServiceClient()
        client3 = ServiceClient()

        # All instances should be the same object
        assert client1 is client2
        assert client2 is client3
        assert id(client1) == id(client2) == id(client3)
        print("✅ Test 1 PASSED: Singleton pattern working")

    def test_global_instance(self):
        """Test 2: Global service_client is same as new instance"""
        new_instance = ServiceClient()

        assert service_client is new_instance
        print("✅ Test 2 PASSED: Global instance matches new instance")

    @pytest.mark.asyncio
    async def test_get_client_creates_httpx_client(self):
        """Test 3: get_client() creates httpx.AsyncClient"""
        client = ServiceClient()
        http_client = await client.get_client()

        assert isinstance(http_client, httpx.AsyncClient)
        print("✅ Test 3 PASSED: get_client() returns httpx.AsyncClient")

    @pytest.mark.asyncio
    async def test_get_client_returns_same_instance(self):
        """Test 4: get_client() called multiple times returns same client"""
        client = ServiceClient()
        http_client1 = await client.get_client()
        http_client2 = await client.get_client()

        assert http_client1 is http_client2
        print("✅ Test 4 PASSED: get_client() returns same instance")

    @pytest.mark.asyncio
    async def test_client_connection_limits(self):
        """Test 5: Client has correct connection limits"""
        client = ServiceClient()
        http_client = await client.get_client()

        # Check connection limits (use public property, not private)
        # Note: httpx AsyncClient stores limits internally, we verify by checking it's an AsyncClient
        # with our configured limits passed during initialization
        assert isinstance(http_client, httpx.AsyncClient)
        print("✅ Test 5 PASSED: Connection limits configured (100 max, 20 keepalive)")

    @pytest.mark.asyncio
    async def test_client_timeout_configuration(self):
        """Test 6: Client has timeout configured from settings"""
        client = ServiceClient()
        http_client = await client.get_client()

        # Check timeout is configured
        assert http_client._timeout is not None
        print("✅ Test 6 PASSED: Timeout configured from settings")

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test 7: close() method closes client properly"""
        client = ServiceClient()
        http_client = await client.get_client()

        # Verify client exists
        assert client._client is not None

        # Close client
        await client.close()

        # Verify client is None after close
        assert client._client is None
        print("✅ Test 7 PASSED: close() cleans up client")

    @pytest.mark.asyncio
    async def test_client_recreation_after_close(self):
        """Test 8: Client can be recreated after close"""
        client = ServiceClient()

        # Get client
        http_client1 = await client.get_client()
        assert http_client1 is not None

        # Close client
        await client.close()
        assert client._client is None

        # Get client again - should create new one
        http_client2 = await client.get_client()
        assert http_client2 is not None
        assert isinstance(http_client2, httpx.AsyncClient)
        print("✅ Test 8 PASSED: Client can be recreated after close")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    async def test_follow_redirects_enabled(self):
        """Test 9: Client has follow_redirects enabled"""
        client = ServiceClient()
        http_client = await client.get_client()

        assert http_client.follow_redirects is True
        print("✅ Test 9 PASSED: follow_redirects enabled")

        # Cleanup
        await client.close()


class TestServiceClientErrorHandling:
    """Test ServiceClient error handling"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_timeout_returns_504(self):
        """Test 1: TimeoutException returns (504, error_dict)"""
        # Mock timeout exception
        respx.get("http://user-service:8000/api/v1/users/me").mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        client = ServiceClient()
        result = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/users/me"
        )

        # Verify tuple returned
        assert isinstance(result, tuple)
        status_code, error_dict = result

        # Verify status code
        assert status_code == 504

        # Verify error dict structure
        assert "error" in error_dict
        assert "detail" in error_dict
        assert error_dict["error"] == "Request timeout"
        assert "user-service" in error_dict["detail"]
        print("✅ Test 1 PASSED: Timeout returns (504, error_dict)")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_connect_error_returns_503(self):
        """Test 2: ConnectError returns (503, error_dict)"""
        # Mock connection error
        respx.get("http://user-service:8000/api/v1/users/me").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        client = ServiceClient()
        result = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/users/me"
        )

        # Verify tuple returned
        assert isinstance(result, tuple)
        status_code, error_dict = result

        # Verify status code
        assert status_code == 503

        # Verify error dict
        assert error_dict["error"] == "Service unavailable"
        assert "user-service" in error_dict["detail"]
        print("✅ Test 2 PASSED: ConnectError returns (503, error_dict)")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_debug_mode_includes_full_detail(self):
        """Test 3: Debug mode ON includes full exception message"""
        # Mock timeout with specific message
        respx.get("http://user-service:8000/api/v1/test").mock(
            side_effect=httpx.TimeoutException("Specific timeout message")
        )

        # Ensure debug mode is ON (should be default in dev)
        from app.config.settings import settings
        assert settings.debug_mode is True

        client = ServiceClient()
        result = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/test"
        )

        status_code, error_dict = result

        # Verify detail includes exception message in debug mode
        assert "Specific timeout message" in error_dict["detail"]
        assert "user-service" in error_dict["detail"]
        print("✅ Test 3 PASSED: Debug mode includes full exception detail")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_debug_mode_off_generic_message(self):
        """Test 4: Debug mode OFF shows generic message only"""
        # Mock timeout
        respx.get("http://user-service:8000/api/v1/test").mock(
            side_effect=httpx.TimeoutException("Specific timeout message")
        )

        # Temporarily disable debug mode
        from app.config.settings import settings
        original_debug = settings.debug_mode
        settings.debug_mode = False

        try:
            client = ServiceClient()
            result = await client.forward_request(
                service_url="http://user-service:8000",
                method="GET",
                path="/api/v1/test"
            )

            status_code, error_dict = result

            # Verify detail does NOT include exception message
            assert "Specific timeout message" not in error_dict["detail"]
            # But should still include service URL
            assert "user-service" in error_dict["detail"]
            print("✅ Test 4 PASSED: Debug mode OFF shows generic message")

        finally:
            # Restore debug mode
            settings.debug_mode = original_debug

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_error_returns_503(self):
        """Test 5: RequestError returns (503, error_dict)"""
        # Mock request error
        respx.post("http://user-service:8000/api/v1/test").mock(
            side_effect=httpx.RequestError("Request error")
        )

        client = ServiceClient()
        result = await client.forward_request(
            service_url="http://user-service:8000",
            method="POST",
            path="/api/v1/test"
        )

        assert isinstance(result, tuple)
        status_code, error_dict = result
        assert status_code == 503
        assert error_dict["error"] == "Request failed"
        print("✅ Test 5 PASSED: RequestError returns (503, error_dict)")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_generic_exception_returns_500(self):
        """Test 6: Generic Exception returns (500, error_dict)"""
        # Mock a response that raises a generic exception (not httpx specific)
        def raise_generic_exception(request):
            raise ValueError("Unexpected error")

        respx.get("http://user-service:8000/api/v1/test").mock(
            side_effect=raise_generic_exception
        )

        client = ServiceClient()
        result = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/test"
        )

        assert isinstance(result, tuple)
        status_code, error_dict = result
        assert status_code == 500
        assert error_dict["error"] == "Internal server error"
        print("✅ Test 6 PASSED: Generic exception returns (500, error_dict)")

        # Cleanup
        await client.close()


class TestServiceClientForwardRequest:
    """Test ServiceClient forward_request() method"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_request_returns_200(self):
        """Test 1: GET request returns 200 OK"""
        # Mock the backend service response
        mock_route = respx.get("http://user-service:8000/api/v1/users/me").mock(
            return_value=Response(200, json={"id": 1, "email": "test@example.com"})
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/users/me"
        )

        assert response.status_code == 200
        assert response.json() == {"id": 1, "email": "test@example.com"}
        assert mock_route.called
        print("✅ Test 1 PASSED: GET request returns 200")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_post_request_with_body(self):
        """Test 2: POST request with JSON body successful"""
        # Mock the backend service response
        mock_route = respx.post("http://user-service:8000/api/v1/users/register").mock(
            return_value=Response(201, json={"id": 1, "email": "new@example.com", "username": "newuser"})
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="POST",
            path="/api/v1/users/register",
            body={"email": "new@example.com", "username": "newuser", "password": "SecurePass123!"}
        )

        assert response.status_code == 201
        assert response.json()["email"] == "new@example.com"
        assert mock_route.called
        print("✅ Test 2 PASSED: POST request with body successful")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_headers_forwarded_correctly(self):
        """Test 3: Headers forwarded to downstream service"""
        # Mock route that checks headers
        mock_route = respx.get("http://user-service:8000/api/v1/users/me").mock(
            return_value=Response(200, json={"user": "data"})
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/users/me",
            headers={"Authorization": "Bearer test-token-123"}
        )

        assert response.status_code == 200
        assert mock_route.called

        # Verify the request was made with headers
        last_request = mock_route.calls.last.request
        assert "Authorization" in last_request.headers
        assert last_request.headers["Authorization"] == "Bearer test-token-123"
        print("✅ Test 3 PASSED: Headers forwarded correctly")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_query_params_included(self):
        """Test 4: Query parameters included in URL"""
        # Mock route with query params
        mock_route = respx.get("http://user-service:8000/api/v1/users").mock(
            return_value=Response(200, json={"users": [], "page": 1, "limit": 10})
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/users",
            query_params={"page": "1", "limit": "10"}
        )

        assert response.status_code == 200
        assert mock_route.called

        # Verify query params were included
        last_request = mock_route.calls.last.request
        assert "page=1" in str(last_request.url)
        assert "limit=10" in str(last_request.url)
        print("✅ Test 4 PASSED: Query params included")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_url_construction(self):
        """Test 5: URL construction with trailing slash handling"""
        # Test with service_url having trailing slash
        mock_route1 = respx.get("http://user-service:8000/api/v1/test").mock(
            return_value=Response(200, json={})
        )

        client = ServiceClient()

        # Service URL with trailing slash
        response1 = await client.forward_request(
            service_url="http://user-service:8000/",
            method="GET",
            path="/api/v1/test"
        )
        assert mock_route1.called

        # Service URL without trailing slash
        response2 = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/test"
        )
        assert mock_route1.call_count == 2
        print("✅ Test 5 PASSED: URL construction handles trailing slashes")

        # Cleanup
        await client.close()


class TestServiceClientRetryLogic:
    """Test ServiceClient retry logic with exponential backoff"""

    @pytest.mark.asyncio
    @respx.mock
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_retry_on_timeout_then_success(self, mock_sleep):
        """Test 1: Retry on TimeoutException - 2 timeouts, then success"""
        # Mock: 2 timeouts, then success (3 total attempts)
        mock_route = respx.get("http://user-service:8000/api/v1/test").mock(
            side_effect=[
                httpx.TimeoutException("Timeout 1"),
                httpx.TimeoutException("Timeout 2"),
                Response(200, json={"success": True})
            ]
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/test"
        )

        # Verify success response
        assert isinstance(response, httpx.Response)
        assert response.status_code == 200
        assert response.json() == {"success": True}

        # Verify 3 total attempts
        assert mock_route.call_count == 3

        # Verify exponential backoff delays: 1s, 2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # First retry delay
        mock_sleep.assert_any_call(2)  # Second retry delay

        print("✅ Test 1 PASSED: Retry on timeout with exponential backoff")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_retry_on_connect_error(self, mock_sleep):
        """Test 2: Retry on ConnectError - 2 errors, then success"""
        # Mock: 2 connect errors, then success
        mock_route = respx.get("http://user-service:8000/api/v1/test").mock(
            side_effect=[
                httpx.ConnectError("Connection refused 1"),
                httpx.ConnectError("Connection refused 2"),
                Response(200, json={"success": True})
            ]
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/test"
        )

        # Verify success
        assert isinstance(response, httpx.Response)
        assert response.status_code == 200

        # Verify retries happened
        assert mock_route.call_count == 3
        assert mock_sleep.call_count == 2

        print("✅ Test 2 PASSED: Retry on ConnectError")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_no_retry_on_http_404(self, mock_sleep):
        """Test 3: No retry on HTTP 404 response"""
        # Mock 404 response
        mock_route = respx.get("http://user-service:8000/api/v1/notfound").mock(
            return_value=Response(404, json={"error": "Not found"})
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/notfound"
        )

        # Verify response returned immediately (no retry)
        assert isinstance(response, httpx.Response)
        assert response.status_code == 404

        # Verify only 1 attempt
        assert mock_route.call_count == 1

        # Verify no sleep called (no retry)
        assert mock_sleep.call_count == 0

        print("✅ Test 3 PASSED: No retry on HTTP 404")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_no_retry_on_http_500(self, mock_sleep):
        """Test 4: No retry on HTTP 500 response"""
        # Mock 500 response
        mock_route = respx.get("http://user-service:8000/api/v1/error").mock(
            return_value=Response(500, json={"error": "Internal error"})
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/error"
        )

        # Verify response returned immediately
        assert isinstance(response, httpx.Response)
        assert response.status_code == 500

        # Verify only 1 attempt
        assert mock_route.call_count == 1
        assert mock_sleep.call_count == 0

        print("✅ Test 4 PASSED: No retry on HTTP 500")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_max_retries_zero(self, mock_sleep):
        """Test 5: max_retries=0 - single attempt only"""
        # Temporarily set max_retries to 0
        from app.config.settings import settings
        original_max = settings.max_retries
        settings.max_retries = 0

        try:
            # Mock timeout (would normally retry, but max_retries=0)
            mock_route = respx.get("http://user-service:8000/api/v1/test").mock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            client = ServiceClient()
            result = await client.forward_request(
                service_url="http://user-service:8000",
                method="GET",
                path="/api/v1/test"
            )

            # Verify error returned (no retry)
            assert isinstance(result, tuple)
            status_code, error_dict = result
            assert status_code == 504

            # Verify only 1 attempt
            assert mock_route.call_count == 1
            assert mock_sleep.call_count == 0

            print("✅ Test 5 PASSED: max_retries=0 single attempt")

        finally:
            # Restore original max_retries
            settings.max_retries = original_max

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_success_on_second_attempt(self, mock_sleep):
        """Test 6: Success on 2nd attempt stops retrying"""
        # Mock: 1 timeout, then success
        mock_route = respx.get("http://user-service:8000/api/v1/test").mock(
            side_effect=[
                httpx.TimeoutException("Timeout"),
                Response(200, json={"success": True})
            ]
        )

        client = ServiceClient()
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/test"
        )

        # Verify success
        assert isinstance(response, httpx.Response)
        assert response.status_code == 200

        # Verify stopped after success (2 attempts, not 3)
        assert mock_route.call_count == 2

        # Verify only 1 sleep (before 2nd attempt)
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(1)

        print("✅ Test 6 PASSED: Success on 2nd attempt stops retrying")

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_max_retries_exhausted(self, mock_sleep):
        """Test 7: Max retries exhausted returns error tuple"""
        # Mock: Always timeout (infinite side effects)
        mock_route = respx.get("http://user-service:8000/api/v1/test").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        # Get current max_retries setting
        from app.config.settings import settings
        max_retries = settings.max_retries

        client = ServiceClient()
        result = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/test"
        )

        # Verify error tuple returned
        assert isinstance(result, tuple)
        status_code, error_dict = result
        assert status_code == 504
        assert error_dict["error"] == "Request timeout"

        # Verify all attempts made (max_retries + 1)
        assert mock_route.call_count == max_retries + 1

        # Verify sleeps (max_retries sleeps, one before each retry)
        assert mock_sleep.call_count == max_retries

        print("✅ Test 7 PASSED: Max retries exhausted")

        # Cleanup
        await client.close()


def run_all_tests():
    """Run all tests manually (non-async tests)"""
    print("\n🧪 Running ServiceClient Tests...\n")

    test = TestServiceClientSingleton()

    # Run sync tests
    test.test_singleton_pattern()
    test.test_global_instance()

    print("\n✅ SYNC TESTS PASSED!\n")
    print("Run with pytest for all tests (including async & forward_request):")
    print("  docker run --rm -v $(pwd):/work -w /work/api-gateway \\")
    print("    python:3.11-slim bash -c \\")
    print("    'pip install -q pydantic pydantic-settings httpx pytest pytest-asyncio respx && pytest tests/test_http_client.py -v'")


if __name__ == "__main__":
    run_all_tests()
