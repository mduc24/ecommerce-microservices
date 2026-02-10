"""
API Gateway - Health Check Routes
"""
import asyncio
import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter

from app.config.settings import settings
from app.utils.http_client import ServiceClient

router = APIRouter(tags=["health"])

# Health check timeout per service (2 seconds)
HEALTH_CHECK_TIMEOUT = 2.0


async def check_service_health(
    service_name: str,
    service_url: str,
    client: ServiceClient
) -> dict[str, Any]:
    """
    Check health of a single service.

    Args:
        service_name: Name of the service (e.g., "user-service")
        service_url: Base URL of the service
        client: ServiceClient instance

    Returns:
        dict with status, response_time_ms, url, and optional error
    """
    start_time = time.perf_counter()

    try:
        # Make health check request with timeout
        response = await asyncio.wait_for(
            client.forward_request(
                service_url=service_url,
                method="GET",
                path="/health"
            ),
            timeout=HEALTH_CHECK_TIMEOUT
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Check if response is a tuple (error response from client)
        if isinstance(response, tuple):
            status_code, error_data = response
            return {
                "status": "down",
                "error": error_data.get("detail", "Service error"),
                "url": f"{service_url}/health"
            }

        # Check if response is httpx.Response
        if isinstance(response, httpx.Response):
            if response.status_code >= 500:
                return {
                    "status": "down",
                    "error": "Service error",
                    "url": f"{service_url}/health"
                }

            return {
                "status": "up",
                "response_time_ms": round(elapsed_ms, 2),
                "url": f"{service_url}/health"
            }

        # Unknown response type
        return {
            "status": "down",
            "error": "Unknown error",
            "url": f"{service_url}/health"
        }

    except asyncio.TimeoutError:
        return {
            "status": "down",
            "error": "Timeout",
            "url": f"{service_url}/health"
        }
    except httpx.ConnectError:
        return {
            "status": "down",
            "error": "Connection refused",
            "url": f"{service_url}/health"
        }
    except Exception as e:
        return {
            "status": "down",
            "error": "Unknown error",
            "url": f"{service_url}/health"
        }


def determine_overall_status(services: dict[str, dict[str, Any]]) -> str:
    """
    Determine overall gateway status based on service health.

    Rules:
        - "healthy": All configured services are up
        - "degraded": Some services are down (1+ down, not all)
        - "unhealthy": All configured services are down

    Args:
        services: Dictionary of service health check results

    Returns:
        str: "healthy", "degraded", or "unhealthy"
    """
    if not services:
        # No services configured, gateway is healthy
        return "healthy"

    service_statuses = [svc["status"] for svc in services.values()]
    up_count = service_statuses.count("up")
    total_count = len(service_statuses)

    if up_count == total_count:
        return "healthy"
    elif up_count == 0:
        return "unhealthy"
    else:
        return "degraded"


@router.get("/health")
async def health_check():
    """
    Gateway health check endpoint with aggregated service status.

    Returns HTTP 200 always, even if backend services are down.

    Response:
        - status: "healthy", "degraded", or "unhealthy"
        - timestamp: ISO 8601 UTC timestamp
        - gateway: Gateway status (always "up")
        - services: Health status of all configured backend services
    """
    # Build list of configured services (dynamic discovery)
    configured_services = {}

    if settings.user_service_url:
        configured_services["user-service"] = settings.user_service_url

    if settings.product_service_url:
        configured_services["product-service"] = settings.product_service_url

    if settings.order_service_url:
        configured_services["order-service"] = settings.order_service_url

    if settings.notification_service_url:
        configured_services["notification-service"] = settings.notification_service_url

    # Create service client
    client = ServiceClient()

    # Check all services in parallel
    tasks = [
        check_service_health(name, url, client)
        for name, url in configured_services.items()
    ]

    # Gather results with return_exceptions=True (continue on errors)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build services dict with results
    services = {}
    for (name, url), result in zip(configured_services.items(), results):
        if isinstance(result, Exception):
            # Handle unexpected exceptions from gather
            services[name] = {
                "status": "down",
                "error": "Unknown error",
                "url": f"{url}/health"
            }
        else:
            services[name] = result

    # Determine overall status
    overall_status = determine_overall_status(services)

    # Build response
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "gateway": {
            "status": "up"
        },
        "services": services
    }
