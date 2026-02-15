"""
Event schemas for order service messaging.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderItemData(BaseModel):
    """Order item data embedded in events."""

    product_id: int
    product_name: str
    quantity: int
    price: float


class OrderCreatedData(BaseModel):
    """Data payload for order.created event."""

    order_id: int
    user_id: int
    total_amount: float
    items: list[OrderItemData]
    status: str


class OrderCreatedEvent(BaseModel):
    """Event emitted when a new order is created."""

    model_config = ConfigDict(from_attributes=True)

    event_type: str = "order.created"
    timestamp: str
    data: OrderCreatedData

    @classmethod
    def from_order(cls, order) -> "OrderCreatedEvent":
        """Build event from an Order model instance."""
        return cls(
            timestamp=datetime.utcnow().isoformat() + "Z",
            data=OrderCreatedData(
                order_id=order.id,
                user_id=order.user_id,
                total_amount=float(order.total_amount),
                items=[
                    OrderItemData(
                        product_id=item.product_id,
                        product_name=item.product_name,
                        quantity=item.quantity,
                        price=float(item.product_price),
                    )
                    for item in order.items
                ],
                status=order.status,
            ),
        )


class OrderStatusUpdatedData(BaseModel):
    """Data payload for order.status.updated event."""

    order_id: int
    old_status: str
    new_status: str
    updated_by: str


class OrderStatusUpdatedEvent(BaseModel):
    """Event emitted when an order status changes."""

    model_config = ConfigDict(from_attributes=True)

    event_type: str = "order.status.updated"
    timestamp: str
    data: OrderStatusUpdatedData

    @classmethod
    def from_status_change(
        cls, order_id: int, old_status: str, new_status: str, updated_by: str = "system"
    ) -> "OrderStatusUpdatedEvent":
        """Build event from status change parameters."""
        return cls(
            timestamp=datetime.utcnow().isoformat() + "Z",
            data=OrderStatusUpdatedData(
                order_id=order_id,
                old_status=old_status,
                new_status=new_status,
                updated_by=updated_by,
            ),
        )
