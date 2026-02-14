"""
Database models for product service.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Text, Numeric, CheckConstraint
)

from app.database import Base


class Product(Base):
    """Product model for catalog management."""

    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("price > 0", name="ck_products_price_positive"),
        CheckConstraint("stock_quantity >= 0", name="ck_products_stock_non_negative"),
    )

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Product info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps (UTC)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, sku={self.sku})>"
