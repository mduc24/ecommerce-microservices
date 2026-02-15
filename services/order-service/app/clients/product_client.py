"""
HTTP client for Product Service communication.
"""

import logging
from typing import Any

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


# ==================== Custom Exceptions ====================


class ProductServiceError(Exception):
    """Base exception for product service errors."""

    def __init__(self, message: str = "Product service error"):
        self.message = message
        super().__init__(self.message)


class ProductNotFoundError(ProductServiceError):
    """Raised when product is not found (404)."""

    def __init__(self, product_id: int):
        self.product_id = product_id
        super().__init__(f"Product {product_id} not found")


class ProductServiceUnavailableError(ProductServiceError):
    """Raised when product service is unreachable (503/connection error)."""

    def __init__(self, detail: str = "Product service unavailable"):
        super().__init__(detail)


class ProductServiceTimeoutError(ProductServiceError):
    """Raised when product service request times out."""

    def __init__(self, detail: str = "Product service request timed out"):
        super().__init__(detail)


# ==================== Product Client ====================


class ProductClient:
    """
    HTTP client for communicating with Product Service.

    Uses httpx.AsyncClient with configurable timeout.
    """

    def __init__(self):
        self._base_url = settings.product_service_url.rstrip("/")
        self._timeout = httpx.Timeout(
            timeout=float(settings.product_service_timeout)
        )

    async def get_product(self, product_id: int) -> dict[str, Any]:
        """
        Get product details from Product Service.

        Args:
            product_id: Product ID to fetch

        Returns:
            dict: Product data (id, name, price, stock_quantity, etc.)

        Raises:
            ProductNotFoundError: Product does not exist (404)
            ProductServiceTimeoutError: Request timed out
            ProductServiceUnavailableError: Service unreachable
            ProductServiceError: Other errors
        """
        url = f"{self._base_url}/api/v1/products/{product_id}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)

            if response.status_code == 200:
                return response.json()

            if response.status_code == 404:
                raise ProductNotFoundError(product_id)

            logger.error(
                f"Product service returned {response.status_code} for product {product_id}"
            )
            raise ProductServiceError(
                f"Unexpected response: {response.status_code}"
            )

        except ProductServiceError:
            raise

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching product {product_id}")
            raise ProductServiceTimeoutError()

        except httpx.ConnectError:
            logger.error(f"Cannot connect to product service: {self._base_url}")
            raise ProductServiceUnavailableError()

        except httpx.RequestError as e:
            logger.error(f"Request error fetching product {product_id}: {e}")
            raise ProductServiceUnavailableError(str(e))
