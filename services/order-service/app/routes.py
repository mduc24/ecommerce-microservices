"""
API routes for order service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.database import get_db
from app.schemas import (
    CreateOrderRequest,
    OrderResponse,
    UpdateOrderStatusRequest,
)
from app.services import create_order, get_order_by_id, get_user_orders, update_order_status

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order_endpoint(
    request: CreateOrderRequest,
    user_id: int = Query(..., description="User ID"),  # TODO: user_id from JWT token
    db: AsyncSession = Depends(get_db),
):
    """Create a new order with product validation."""
    order = await create_order(db, request, user_id)
    return order


@router.get(
    "",
    response_model=list[OrderResponse],
)
async def list_orders_endpoint(
    user_id: int = Query(..., description="User ID"),  # TODO: user_id from JWT token
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get all orders for a user with pagination."""
    orders = await get_user_orders(db, user_id, skip, limit)
    return orders


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order_endpoint(
    order_id: int,
    user_id: int = Query(..., description="User ID"),  # TODO: user_id from JWT token
    db: AsyncSession = Depends(get_db),
):
    """Get a single order by ID."""
    order = await get_order_by_id(db, order_id, user_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
async def update_order_status_endpoint(
    order_id: int,
    request: UpdateOrderStatusRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update order status."""
    order = await update_order_status(db, order_id, request.status)
    return order
