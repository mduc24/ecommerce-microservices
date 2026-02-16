"""
API Gateway - Notification Service Routes (Proxy)
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.utils.http_client import ServiceClient

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def _proxy_request(
    method: str,
    path: str,
    request: Request,
    body: dict | None = None,
    query_params: dict | None = None,
) -> JSONResponse:
    """Helper to proxy requests to notification-service."""
    service_client = ServiceClient()

    result = await service_client.forward_request(
        service_url=settings.notification_service_url,
        method=method,
        path=path,
        body=body,
        query_params=query_params,
    )

    if isinstance(result, tuple):
        status_code, error_dict = result
        return JSONResponse(status_code=status_code, content=error_dict)

    return JSONResponse(status_code=result.status_code, content=result.json())


@router.get("")
async def list_notifications(request: Request):
    """Proxy request to Notification Service - List notifications."""
    return await _proxy_request(
        "GET", "/api/v1/notifications", request,
        query_params=dict(request.query_params),
    )


@router.get("/{notification_id}")
async def get_notification(notification_id: int, request: Request):
    """Proxy request to Notification Service - Get single notification."""
    return await _proxy_request(
        "GET", f"/api/v1/notifications/{notification_id}", request,
    )


@router.post("/retry/{notification_id}")
async def retry_notification(notification_id: int, request: Request):
    """Proxy request to Notification Service - Retry failed notification."""
    return await _proxy_request(
        "POST", f"/api/v1/notifications/retry/{notification_id}", request,
    )
