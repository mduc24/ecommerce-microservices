"""
Business logic for order service.
"""

import logging
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.clients.product_client import (
    ProductClient,
    ProductNotFoundError,
    ProductServiceUnavailableError,
    ProductServiceTimeoutError,
)
from app.events.publisher import event_publisher
from app.events.schemas import OrderCreatedEvent, OrderStatusUpdatedEvent
from app.models import Order, OrderItem
from app.schemas import CreateOrderRequest, OrderStatus

logger = logging.getLogger(__name__)


async def create_order(
    db: AsyncSession,
    request: CreateOrderRequest,
    user_id: int,
) -> Order:
    """
    Create a new order with product validation.

    Flow:
        1. Validate products exist and have sufficient stock
        2. Create order with product snapshots
        3. Save to database in a single transaction

    Args:
        db: Database session
        request: Order creation request with items
        user_id: ID of the user placing the order

    Returns:
        Order: Created order with items eager loaded

    Raises:
        HTTPException: On validation, product service, or database errors
    """
    product_client = ProductClient()
    order_items = []
    total_amount = Decimal("0")

    # Step 1: Validate all products and build order items
    for item in request.items:
        try:
            product = await product_client.get_product(item.product_id)
        except ProductNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found",
            )
        except ProductServiceTimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Product service request timed out",
            )
        except ProductServiceUnavailableError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product service unavailable",
            )

        # Check stock
        stock = product.get("stock_quantity", 0)
        if stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {item.product_id}. Available: {stock}, requested: {item.quantity}",
            )

        # Build order item snapshot
        product_price = Decimal(str(product["price"]))
        subtotal = product_price * item.quantity
        total_amount += subtotal

        order_items.append(
            OrderItem(
                product_id=item.product_id,
                product_name=product["name"],
                product_price=product_price,
                quantity=item.quantity,
                subtotal=subtotal,
            )
        )

    # Step 2: Create order and save
    try:
        order = Order(
            user_id=user_id,
            status="pending",
            total_amount=total_amount,
        )
        order.items = order_items

        db.add(order)
        await db.commit()
        await db.refresh(order)

        # Publish OrderCreated event (don't fail if publishing fails)
        try:
            event = OrderCreatedEvent.from_order(order)
            await event_publisher.publish(event, "order.created")
        except Exception as e:
            logger.error(f"Failed to publish OrderCreated event: {e}")

        return order

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )


async def get_order_by_id(
    db: AsyncSession,
    order_id: int,
    user_id: int,
) -> Order | None:
    """
    Get a single order by ID, scoped to user.

    Args:
        db: Database session
        order_id: Order ID to fetch
        user_id: Owner user ID (authorization check)

    Returns:
        Order with items eager loaded, or None if not found
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_orders(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Order]:
    """
    Get all orders for a user with pagination.

    Args:
        db: Database session
        user_id: User ID to filter by
        skip: Number of records to skip
        limit: Max number of records to return

    Returns:
        List of orders with items eager loaded (newest first)
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_order_status(
    db: AsyncSession,
    order_id: int,
    new_status: OrderStatus,
) -> Order:
    """
    Update order status with transition validation.

    Args:
        db: Database session
        order_id: Order ID to update
        new_status: New status to set

    Returns:
        Updated order with items eager loaded

    Raises:
        HTTPException: If order not found or invalid status transition
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    if order.status in ("cancelled", "delivered"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update order in {order.status} status",
        )

    old_status = order.status
    order.status = new_status.value
    await db.commit()
    await db.refresh(order)

    # Publish OrderStatusUpdated event (don't fail if publishing fails)
    try:
        event = OrderStatusUpdatedEvent.from_status_change(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status.value,
        )
        await event_publisher.publish(event, "order.status.updated")
    except Exception as e:
        logger.error(f"Failed to publish OrderStatusUpdated event: {e}")

    return order
