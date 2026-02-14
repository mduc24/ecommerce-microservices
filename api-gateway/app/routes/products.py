"""
API Gateway - Product Service Routes (Proxy)
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.utils.http_client import ServiceClient

router = APIRouter(prefix="/products", tags=["products"])


async def _proxy_request(
    method: str,
    path: str,
    request: Request,
    body: dict | None = None,
    query_params: dict | None = None,
) -> JSONResponse:
    """Helper to proxy requests to product-service."""
    service_client = ServiceClient()

    result = await service_client.forward_request(
        service_url=settings.product_service_url,
        method=method,
        path=path,
        body=body,
        query_params=query_params,
    )

    if isinstance(result, tuple):
        status_code, error_dict = result
        return JSONResponse(status_code=status_code, content=error_dict)

    # DELETE 204 returns no body
    if result.status_code == 204:
        return JSONResponse(status_code=204, content=None)

    return JSONResponse(status_code=result.status_code, content=result.json())


# ==================== Public Routes ====================


@router.get("")
async def list_products(request: Request):
    """
    Proxy request to Product Service - List products with pagination.

    Public endpoint (no authentication required).

    Query params: limit, offset, category, is_active, name, sort_by
    """
    query_params = dict(request.query_params)

    return await _proxy_request(
        method="GET",
        path="/api/v1/products",
        request=request,
        query_params=query_params,
    )


@router.get("/{product_id}")
async def get_product(product_id: int, request: Request):
    """
    Proxy request to Product Service - Get single product.

    Public endpoint (no authentication required).
    """
    return await _proxy_request(
        method="GET",
        path=f"/api/v1/products/{product_id}",
        request=request,
    )


# ==================== Protected Routes (auth commented out for now) ====================


@router.post("")
async def create_product(
    request: Request,
    # user_id: str = Depends(get_current_user),  # TODO: Enable auth
):
    """
    Proxy request to Product Service - Create product.

    Protected endpoint (requires authentication - TODO).
    """
    body = await request.json()

    return await _proxy_request(
        method="POST",
        path="/api/v1/products",
        request=request,
        body=body,
    )


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    request: Request,
    # user_id: str = Depends(get_current_user),  # TODO: Enable auth
):
    """
    Proxy request to Product Service - Full update product.

    Protected endpoint (requires authentication - TODO).
    """
    body = await request.json()

    return await _proxy_request(
        method="PUT",
        path=f"/api/v1/products/{product_id}",
        request=request,
        body=body,
    )


@router.patch("/{product_id}")
async def partial_update_product(
    product_id: int,
    request: Request,
    # user_id: str = Depends(get_current_user),  # TODO: Enable auth
):
    """
    Proxy request to Product Service - Partial update product.

    Protected endpoint (requires authentication - TODO).
    """
    body = await request.json()

    return await _proxy_request(
        method="PATCH",
        path=f"/api/v1/products/{product_id}",
        request=request,
        body=body,
    )


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    request: Request,
    # user_id: str = Depends(get_current_user),  # TODO: Enable auth
):
    """
    Proxy request to Product Service - Soft delete product.

    Protected endpoint (requires authentication - TODO).
    Returns 204 No Content.
    """
    return await _proxy_request(
        method="DELETE",
        path=f"/api/v1/products/{product_id}",
        request=request,
    )


@router.patch("/{product_id}/stock")
async def update_stock(
    product_id: int,
    request: Request,
    # user_id: str = Depends(get_current_user),  # TODO: Enable auth
):
    """
    Proxy request to Product Service - Update product stock.

    Protected endpoint (requires authentication - TODO).
    """
    body = await request.json()

    return await _proxy_request(
        method="PATCH",
        path=f"/api/v1/products/{product_id}/stock",
        request=request,
        body=body,
    )
