"""
Database models for order service.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime,
    Numeric, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class Order(Base):
    """Order model for order processing."""

    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_orders_total_non_negative"),
    )

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # User reference (no FK - microservices principle)
    user_id = Column(Integer, nullable=False, index=True)

    # Order info
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Timestamps (UTC)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"


class OrderItem(Base):
    """Order item model - product snapshot at order time."""

    __tablename__ = "order_items"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("product_price > 0", name="ck_order_items_price_positive"),
        CheckConstraint("subtotal > 0", name="ck_order_items_subtotal_positive"),
    )

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Order reference (FK with cascade)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Product snapshot (no FK - microservices principle)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(255), nullable=False)
    product_price = Column(Numeric(10, 2), nullable=False)

    # Quantity and calculated subtotal
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    # Timestamps (UTC)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, product_name={self.product_name}, qty={self.quantity})>"
