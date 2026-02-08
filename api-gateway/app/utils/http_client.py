"""
API Gateway - HTTP Client Utility with Singleton Pattern
"""
import asyncio
import logging
import httpx
from typing import Optional
from app.config.settings import settings

# Initialize logger
logger = logging.getLogger(__name__)


class ServiceClient:
    """
    HTTP client for making requests to backend microservices.
    Implements singleton pattern to reuse the same client instance.
    """

    _instance: Optional['ServiceClient'] = None
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

        Configures:
        - Timeout from settings
        - Connection pool limits (100 max, 20 keepalive)
        - Async context support

        Returns:
            httpx.AsyncClient: Configured async HTTP client
        """
        if self._client is None:
            # Configure connection limits
            limits = httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )

            # Configure timeout
            timeout = httpx.Timeout(
                timeout=float(settings.request_timeout),
                connect=5.0,  # Connection timeout
                read=settings.request_timeout,  # Read timeout
                write=settings.request_timeout,  # Write timeout
                pool=5.0  # Pool timeout
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
        Should be called on application shutdown.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

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

        Retries only on:
        - TimeoutException
        - ConnectError

        Does NOT retry on:
        - HTTP responses (2xx, 4xx, 5xx)
        - Other RequestError types

        Args:
            service_url: Base URL of the service (e.g., "http://user-service:8000")
            method: HTTP method (GET, POST, PUT, DELETE)
            path: Endpoint path (e.g., "/api/v1/users/me")
            headers: Optional headers to forward
            body: Optional JSON body for POST/PUT requests
            query_params: Optional query parameters

        Returns:
            httpx.Response: Response from the backend service (on success)
            tuple[int, dict]: (status_code, error_dict) on error

        Example:
            response = await client.forward_request(
                service_url="http://user-service:8000",
                method="POST",
                path="/api/v1/users/register",
                headers={"Authorization": "Bearer token"},
                body={"email": "test@example.com"}
            )

            # Handle response
            if isinstance(response, tuple):
                status_code, error = response
                # Handle error
            else:
                # Handle success
                data = response.json()
        """
        max_retries = settings.max_retries

        # Retry loop
        for attempt in range(max_retries + 1):
            try:
                # Build full URL
                url = f"{service_url.rstrip('/')}{path}"

                # Get HTTP client
                client = await self.get_client()

                # Make request based on method
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=body,
                    params=query_params
                )

                # Success!
                if attempt > 0:
                    # Log success after retry
                    logger.info(
                        f"Request succeeded on attempt {attempt + 1}",
                        extra={
                            "method": method,
                            "service_url": service_url,
                            "path": path,
                            "attempt": attempt + 1
                        }
                    )

                return response

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                # These exceptions are retryable
                if attempt < max_retries:
                    # Calculate exponential backoff delay
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
                    # Max retries exhausted
                    logger.error(
                        f"Request failed after {max_retries + 1} attempts: {type(e).__name__}",
                        extra={
                            "method": method,
                            "service_url": service_url,
                            "path": path,
                            "error": str(e),
                            "total_attempts": max_retries + 1
                        }
                    )

                    # Return appropriate error
                    if isinstance(e, httpx.TimeoutException):
                        error_dict = self._build_error_dict("Request timeout", e, service_url)
                        return (504, error_dict)
                    else:  # ConnectError
                        error_dict = self._build_error_dict("Service unavailable", e, service_url)
                        return (503, error_dict)

            except httpx.RequestError as e:
                # Other request errors - do NOT retry
                logger.error(
                    f"Request failed: {type(e).__name__}",
                    extra={
                        "method": method,
                        "service_url": service_url,
                        "path": path,
                        "error": str(e)
                    }
                )
                error_dict = self._build_error_dict(
                    "Request failed",
                    e,
                    service_url
                )
                return (503, error_dict)

            except Exception as e:
                # Unexpected errors - do NOT retry
                logger.error(
                    f"Request failed: {type(e).__name__}",
                    extra={
                        "method": method,
                        "service_url": service_url,
                        "path": path,
                        "error": str(e)
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
