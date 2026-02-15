"""
API Gateway - Order Service Routes (Proxy)
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.utils.http_client import ServiceClient

router = APIRouter(prefix="/orders", tags=["orders"])


async def _proxy_request(
    method: str,
    path: str,
    request: Request,
    body: dict | None = None,
    query_params: dict | None = None,
) -> JSONResponse:
    """Helper to proxy requests to order-service."""
    service_client = ServiceClient()

    result = await service_client.forward_request(
        service_url=settings.order_service_url,
        method=method,
        path=path,
        body=body,
        query_params=query_params,
    )

    if isinstance(result, tuple):
        status_code, error_dict = result
        return JSONResponse(status_code=status_code, content=error_dict)

    return JSONResponse(status_code=result.status_code, content=result.json())


# ==================== Routes (auth commented out for now) ====================


@router.post("")
async def create_order(
    request: Request,
    # user_id: str = Depends(get_current_user),  # TODO: Enable auth
):
    """Proxy request to Order Service - Create order."""
    body = await request.json()
    query_params = dict(request.query_params)

    return await _proxy_request(
        method="POST",
        path="/api/v1/orders",
        request=request,
        body=body,
        query_params=query_params,
    )


@router.get("")
async def list_orders(request: Request):
    """Proxy request to Order Service - List user orders."""
    query_params = dict(request.query_params)

    return await _proxy_request(
        method="GET",
        path="/api/v1/orders",
        request=request,
        query_params=query_params,
    )


@router.get("/{order_id}")
async def get_order(order_id: int, request: Request):
    """Proxy request to Order Service - Get single order."""
    query_params = dict(request.query_params)

    return await _proxy_request(
        method="GET",
        path=f"/api/v1/orders/{order_id}",
        request=request,
        query_params=query_params,
    )


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: Request,
    # user_id: str = Depends(get_current_user),  # TODO: Enable auth
):
    """Proxy request to Order Service - Update order status."""
    body = await request.json()

    return await _proxy_request(
        method="PATCH",
        path=f"/api/v1/orders/{order_id}/status",
        request=request,
        body=body,
    )
