"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


# ==================== Enums ====================


class OrderStatus(str, Enum):
    """Valid order statuses."""

    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


# ==================== Request Schemas ====================


class OrderItemRequest(BaseModel):
    """Schema for a single order item in create request."""

    product_id: int = Field(
        ...,
        example=1,
        description="Product ID to order"
    )
    quantity: int = Field(
        ...,
        gt=0,
        example=2,
        description="Quantity to order (must be > 0)"
    )


class CreateOrderRequest(BaseModel):
    """Schema for creating a new order."""

    items: list[OrderItemRequest] = Field(
        ...,
        min_length=1,
        example=[{"product_id": 1, "quantity": 2}],
        description="List of items to order (min 1)"
    )


class UpdateOrderStatusRequest(BaseModel):
    """Schema for updating order status."""

    status: OrderStatus = Field(
        ...,
        example="confirmed",
        description="New order status"
    )


# ==================== Response Schemas ====================


class OrderItemResponse(BaseModel):
    """Schema for order item in response."""

    id: int = Field(..., example=1)
    order_id: int = Field(..., example=1)
    product_id: int = Field(..., example=1)
    product_name: str = Field(..., example="Wireless Bluetooth Headphones")
    product_price: Decimal = Field(..., example=29.99)
    quantity: int = Field(..., example=2)
    subtotal: Decimal = Field(..., example=59.98)
    created_at: datetime = Field(..., example="2024-01-01T00:00:00")

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Schema for order response."""

    id: int = Field(..., example=1)
    user_id: int = Field(..., example=1)
    status: OrderStatus = Field(..., example="pending")
    total_amount: Decimal = Field(..., example=59.98)
    created_at: datetime = Field(..., example="2024-01-01T00:00:00")
    updated_at: datetime = Field(..., example="2024-01-01T00:00:00")
    items: list[OrderItemResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
