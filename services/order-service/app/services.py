"""
Business logic for order service.
"""

import logging
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.product_client import (
    ProductClient,
    ProductNotFoundError,
    ProductServiceUnavailableError,
    ProductServiceTimeoutError,
)
from app.models import Order, OrderItem
from app.schemas import CreateOrderRequest

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

        return order

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )
