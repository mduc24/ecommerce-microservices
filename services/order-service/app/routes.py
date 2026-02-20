"""
API routes for order service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.config.settings import settings
from app.database import get_db
from app.schemas import (
    CreateOrderRequest,
    OrderResponse,
    UpdateOrderStatusRequest,
)
from app.services import create_order, get_order_by_id, get_user_orders, update_order_status

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


class CurrentUser:
    def __init__(self, user_id: int, email: str):
        self.user_id = user_id
        self.email = email


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """Extract user_id and email from JWT Bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id_str: str = payload.get("sub")
        email: str = payload.get("email", "")
        if user_id_str is None:
            raise credentials_exception
        return CurrentUser(user_id=int(user_id_str), email=email)
    except (JWTError, ValueError):
        raise credentials_exception


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
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new order with product validation."""
    order = await create_order(db, request, current_user.user_id, current_user.email)
    return order


@router.get(
    "",
    response_model=list[OrderResponse],
)
async def list_orders_endpoint(
    current_user: CurrentUser = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get all orders for the authenticated user with pagination."""
    orders = await get_user_orders(db, current_user.user_id, skip, limit)
    return orders


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order_endpoint(
    order_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single order by ID."""
    order = await get_order_by_id(db, order_id, current_user.user_id)
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
