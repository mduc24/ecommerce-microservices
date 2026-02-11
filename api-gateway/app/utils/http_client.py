"""
HTTP Client wrapper for inter-service communication.

Handles timeouts, retries, logging, and error responses.
Singleton pattern ensures connection pool reuse.

Features:
- Automatic retry with exponential backoff
- Request/Response logging with header redaction
- Connection pooling (100 max, 20 keepalive)
- Request ID tracking (X-Request-ID)
- Duration tracking for observability
- Async context manager support

Example:
    async with ServiceClient() as client:
        response = await client.forward_request(
            service_url="http://user-service:8000",
            method="GET",
            path="/api/v1/users/me",
            headers={"Authorization": "Bearer token"}
        )
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Optional

import httpx

from app.config.settings import settings

# Initialize logger
logger = logging.getLogger(__name__)

# ==================== Constants ====================

# Connection pool settings
MAX_CONNECTIONS = 100
MAX_KEEPALIVE_CONNECTIONS = 20
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_POOL_TIMEOUT = 5.0

# Security: Sensitive headers to redact in logs (only affects logging, not actual requests)
SENSITIVE_HEADERS = ["authorization", "cookie", "x-api-key", "proxy-authorization"]


class ServiceClient:
    """
    Singleton HTTP client for making requests to backend microservices.

    This class implements a singleton pattern to ensure connection pool reuse
    across the application. It handles retries, timeouts, logging, and error
    responses automatically.

    Connection Pool Settings:
        - Max connections: 100
        - Max keepalive connections: 20
        - Connection timeout: 5s
        - Request timeout: From settings (default 30s)

    Thread Safety:
        The singleton pattern is thread-safe. The same instance is returned
        across all calls to ServiceClient().

    Features:
        - Automatic retry on timeout/connection errors (exponential backoff)
        - Request/Response logging with sensitive header redaction
        - Request ID tracking (X-Request-ID)
        - Duration tracking in milliseconds
        - Async context manager support

    Example:
        Basic usage:
            client = ServiceClient()
            response = await client.forward_request(
                service_url="http://user-service:8000",
                method="POST",
                path="/api/v1/users/register",
                body={"email": "user@example.com", "password": "secure123"}
            )

        With context manager (automatic cleanup):
            async with ServiceClient() as client:
                response = await client.forward_request(
                    service_url="http://user-service:8000",
                    method="GET",
                    path="/api/v1/users/me",
                    headers={"Authorization": "Bearer token"}
                )

        Error handling:
            result = await client.forward_request(...)
            if isinstance(result, tuple):
                status_code, error_dict = result
                # Handle error
            else:
                # Success - result is httpx.Response
                data = result.json()
    """

    _instance: Optional[ServiceClient] = None
    _client: Optional[httpx.AsyncClient] = None

    def __new__(cls) -> 'ServiceClient':
        """
        Singleton pattern implementation.
        Ensures only one instance of ServiceClient exists.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_client(self) -> httpx.AsyncClient:
        """
        Get or create the httpx.AsyncClient instance.

        Creates a configured HTTP client with connection pooling and timeouts.
        The client is created once and reused for all subsequent requests
        (singleton pattern).

        Configuration:
            - Max connections: 100
            - Max keepalive connections: 20
            - Request timeout: From settings (default 30s)
            - Connection timeout: 5s
            - Pool timeout: 5s
            - Follow redirects: Enabled

        Returns:
            httpx.AsyncClient: Configured async HTTP client instance

        Note:
            This method is idempotent - calling it multiple times returns
            the same client instance.
        """
        if self._client is None:
            # Configure connection limits using module constants
            limits = httpx.Limits(
                max_connections=MAX_CONNECTIONS,
                max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS
            )

            # Configure timeout
            timeout = httpx.Timeout(
                timeout=float(settings.request_timeout),
                connect=DEFAULT_CONNECT_TIMEOUT,
                read=settings.request_timeout,
                write=settings.request_timeout,
                pool=DEFAULT_POOL_TIMEOUT
            )

            # Create async client
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                follow_redirects=True
            )

        return self._client

    async def close(self) -> None:
        """
        Close the HTTP client and cleanup resources.

        This method is idempotent - it's safe to call multiple times.
        Subsequent calls after the first close will be no-ops.

        Should be called on application shutdown or when using context manager.

        Example:
            client = ServiceClient()
            await client.close()  # First call - closes client
            await client.close()  # Second call - no-op (safe)
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> ServiceClient:
        """
        Enter async context manager.

        Returns:
            ServiceClient: This instance for use in the context

        Example:
            async with ServiceClient() as client:
                response = await client.forward_request(...)
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any
    ) -> bool:
        """
        Exit async context manager and cleanup resources.

        Ensures the HTTP client is properly closed even if an exception
        occurred within the context.

        Args:
            exc_type: Exception type if an exception occurred, None otherwise
            exc_val: Exception value if an exception occurred, None otherwise
            exc_tb: Exception traceback if an exception occurred, None otherwise

        Returns:
            bool: False to propagate any exception that occurred in the context

        Note:
            Returning False ensures that exceptions are not suppressed.
        """
        await self.close()
        return False  # Propagate exceptions

    def _build_error_dict(
        self,
        error_msg: str,
        exception: Exception,
        service_url: str
    ) -> dict:
        """
        Build error dictionary for error responses.

        Args:
            error_msg: Short error message
            exception: The exception that occurred
            service_url: The service URL that was called

        Returns:
            dict: Error dictionary with 'error' and 'detail' keys
        """
        error_dict = {"error": error_msg}

        # Include full details in debug mode, generic message otherwise
        if settings.debug_mode:
            error_dict["detail"] = f"{str(exception)} | service: {service_url}"
        else:
            error_dict["detail"] = f"Service: {service_url}"

        return error_dict

    def _redact_headers(self, headers: dict | None) -> dict:
        """
        Redact sensitive headers for secure logging.

        CRITICAL: This only affects logging - actual request headers are NOT modified.

        Redacted Headers:
            - Authorization
            - Cookie
            - X-API-Key
            - Proxy-Authorization
            - Any header containing "token" (case-insensitive)

        Args:
            headers: Original headers dictionary (can be None)

        Returns:
            dict: New dictionary with sensitive values replaced with '***REDACTED***'.
                  Non-sensitive headers are preserved as-is.

        Example:
            >>> headers = {"Authorization": "Bearer secret", "X-Custom": "value"}
            >>> client._redact_headers(headers)
            {"Authorization": "***REDACTED***", "X-Custom": "value"}

        Note:
            The original headers dict is never modified. A new dict is created
            and returned with redacted values only for logging purposes.
        """
        if not headers:
            return {}

        # Create a copy to avoid modifying original
        redacted = headers.copy()

        # Redact sensitive headers
        for key in list(redacted.keys()):
            key_lower = key.lower()
            # Check if key is in sensitive list or contains "token"
            if key_lower in SENSITIVE_HEADERS or 'token' in key_lower:
                redacted[key] = '***REDACTED***'

        return redacted

    async def forward_request(
        self,
        service_url: str,
        method: str,
        path: str,
        headers: dict | None = None,
        body: dict | None = None,
        query_params: dict | None = None
    ) -> httpx.Response | tuple[int, dict]:
        """
        Forward HTTP request to a backend microservice with retry logic and error handling.

        Features:
            - Automatic retry with exponential backoff (1s, 2s, 4s, ...)
            - Request/Response logging with header redaction
            - Request ID tracking (X-Request-ID)
            - Duration tracking in milliseconds
            - Structured error responses

        Retry Behavior:
            Retries only on:
                - TimeoutException (network timeout)
                - ConnectError (connection refused/failed)

            Does NOT retry on:
                - HTTP responses (2xx, 4xx, 5xx) - these are valid responses
                - Other RequestError types

        Args:
            service_url: Base URL of the backend service.
                Example: "http://user-service:8000"
            method: HTTP method to use.
                Supported: GET, POST, PUT, DELETE, PATCH, etc.
            path: Endpoint path starting with /.
                Example: "/api/v1/users/me"
            headers: Optional request headers to forward.
                X-Request-ID will be added/preserved automatically.
                X-Forwarded-For will be preserved if present.
            body: Optional JSON request body for POST/PUT/PATCH requests.
                Will be serialized to JSON automatically.
            query_params: Optional query parameters as dict.
                Example: {"page": "1", "limit": "10"}

        Returns:
            httpx.Response: On successful request (any HTTP status code).
                The response object from the backend service unchanged.

            tuple[int, dict]: On request failure (timeout, connection error, etc.).
                - int: HTTP-like status code (504 for timeout, 503 for unavailable, etc.)
                - dict: Error dictionary with 'error' and 'detail' keys

        Raises:
            None: All errors are returned as tuples, not raised as exceptions.

        Example:
            Basic request:
                response = await client.forward_request(
                    service_url="http://user-service:8000",
                    method="GET",
                    path="/api/v1/users/me",
                    headers={"Authorization": "Bearer token123"}
                )

            With body and query params:
                response = await client.forward_request(
                    service_url="http://user-service:8000",
                    method="POST",
                    path="/api/v1/users",
                    body={"email": "user@example.com", "password": "secure123"},
                    query_params={"send_email": "true"}
                )

            Error handling:
                result = await client.forward_request(...)
                if isinstance(result, tuple):
                    status_code, error_dict = result
                    logger.error(f"Request failed: {error_dict['error']}")
                else:
                    # Success - result is httpx.Response
                    data = result.json()

        Note:
            - Request bodies and response bodies are never logged for security
            - Sensitive headers (Authorization, Cookie, etc.) are redacted in logs
            - Each request is tracked with a unique X-Request-ID for tracing
        """
        max_retries = settings.max_retries

        # Extract or generate request ID
        request_id = headers.get('X-Request-ID') if headers else None
        if not request_id:
            request_id = uuid.uuid4().hex  # UUID without dashes

        # Prepare request headers (ensure X-Request-ID is included)
        request_headers = headers.copy() if headers else {}
        request_headers['X-Request-ID'] = request_id

        # Start duration tracking
        start_time = time.perf_counter()

        # Log request (DEBUG level, only if debug_mode enabled)
        if settings.debug_mode:
            logger.debug(
                f"Request: {method} {service_url}{path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "service_url": service_url,
                    "path": path,
                    "headers": self._redact_headers(headers),
                    "has_body": body is not None,
                    "has_query_params": query_params is not None
                }
            )

        # Retry loop: range(max_retries + 1) gives us (max_retries + 1) attempts total
        # Example: max_retries=3 → range(4) → attempts [0, 1, 2, 3] = 4 total attempts
        for attempt in range(max_retries + 1):
            try:
                # Build full URL
                url = f"{service_url.rstrip('/')}{path}"

                # Get HTTP client
                client = await self.get_client()

                # Make request based on method
                # NOTE: Using request_headers (with X-Request-ID), not original headers
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=request_headers,
                    json=body,
                    params=query_params
                )

                # Calculate duration
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log response (DEBUG level, only if debug_mode enabled)
                if settings.debug_mode:
                    logger.debug(
                        f"Response: {response.status_code}",
                        extra={
                            "request_id": request_id,
                            "status_code": response.status_code,
                            "duration_ms": round(duration_ms, 2),
                            "attempt": attempt + 1 if attempt > 0 else 1
                        }
                    )

                # Success! If we got here, the request completed (any HTTP status is success)
                # Only log retry success at INFO level (attempt > 0 means we retried)
                # First attempt success (attempt == 0) already logged at DEBUG level above
                if attempt > 0:
                    # Log success after retry (INFO level)
                    logger.info(
                        f"Request succeeded on attempt {attempt + 1}",
                        extra={
                            "request_id": request_id,
                            "method": method,
                            "service_url": service_url,
                            "path": path,
                            "attempt": attempt + 1,
                            "duration_ms": round(duration_ms, 2)
                        }
                    )

                return response

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                # These exceptions are retryable (network-level failures, not HTTP errors)
                # TimeoutException: Request took too long (network timeout)
                # ConnectError: Cannot establish connection (service down, DNS failure, etc.)
                if attempt < max_retries:
                    # Calculate exponential backoff delay: 2^0=1s, 2^1=2s, 2^2=4s, 2^3=8s
                    # This gives the downstream service time to recover
                    delay = 1 * (2 ** attempt)  # 1s, 2s, 4s, ...

                    # Log retry attempt
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_retries} after {type(e).__name__} - {service_url}{path}",
                        extra={
                            "method": method,
                            "service_url": service_url,
                            "path": path,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "delay": delay,
                            "exception_type": type(e).__name__
                        }
                    )

                    # Wait before retry
                    await asyncio.sleep(delay)
                    continue  # Next attempt

                else:
                    # Max retries exhausted - all retry attempts failed
                    # We've tried (max_retries + 1) times total
                    duration_ms = (time.perf_counter() - start_time) * 1000

                    logger.error(
                        f"Request failed after {max_retries + 1} attempts: {type(e).__name__}",
                        extra={
                            "request_id": request_id,
                            "method": method,
                            "service_url": service_url,
                            "path": path,
                            "error": str(e),
                            "total_attempts": max_retries + 1,
                            "duration_ms": round(duration_ms, 2)
                        }
                    )

                    # Return appropriate HTTP-like error code
                    if isinstance(e, httpx.TimeoutException):
                        # 504 Gateway Timeout - upstream service didn't respond in time
                        error_dict = self._build_error_dict("Request timeout", e, service_url)
                        return (504, error_dict)
                    else:  # ConnectError
                        # 503 Service Unavailable - cannot establish connection
                        error_dict = self._build_error_dict("Service unavailable", e, service_url)
                        return (503, error_dict)

            except httpx.RequestError as e:
                # Other request errors - do NOT retry (not network-level failures)
                # Examples: Invalid URL, unsupported protocol, read errors, etc.
                # These are typically non-transient and retrying won't help
                duration_ms = (time.perf_counter() - start_time) * 1000

                logger.error(
                    f"Request failed: {type(e).__name__}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "service_url": service_url,
                        "path": path,
                        "error": str(e),
                        "duration_ms": round(duration_ms, 2)
                    }
                )
                error_dict = self._build_error_dict(
                    "Request failed",
                    e,
                    service_url
                )
                return (503, error_dict)

            except Exception as e:
                # Unexpected errors - do NOT retry (could be programming errors)
                # Catch-all for any unexpected exceptions (JSON encoding errors, etc.)
                # These should be investigated and fixed, not retried
                duration_ms = (time.perf_counter() - start_time) * 1000

                logger.error(
                    f"Request failed: {type(e).__name__}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "service_url": service_url,
                        "path": path,
                        "error": str(e),
                        "duration_ms": round(duration_ms, 2)
                    }
                )
                error_dict = self._build_error_dict(
                    "Internal server error",
                    e,
                    service_url
                )
                return (500, error_dict)


# Singleton instance
service_client = ServiceClient()
