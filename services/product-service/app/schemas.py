"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ProductBase(BaseModel):
    """Base schema with shared product fields."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        example="Wireless Bluetooth Headphones",
        description="Product name"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        example="High-quality wireless headphones with noise cancellation",
        description="Product description"
    )
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        example=29.99,
        description="Product price (must be > 0)"
    )
    stock_quantity: int = Field(
        ...,
        ge=0,
        example=100,
        description="Available stock (must be >= 0)"
    )
    sku: str = Field(
        ...,
        min_length=3,
        max_length=50,
        example="WBH-001",
        description="Unique stock keeping unit"
    )
    category: Optional[str] = Field(
        None,
        max_length=100,
        example="Electronics",
        description="Product category"
    )


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    is_active: bool = Field(
        default=True,
        example=True,
        description="Product active status"
    )

    @field_validator('sku')
    @classmethod
    def normalize_sku(cls, v: str) -> str:
        """Normalize SKU to uppercase."""
        return v.upper().strip()


class ProductUpdate(BaseModel):
    """Schema for updating a product. All fields optional."""

    name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=200,
        example="Updated Product Name"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        example="Updated description"
    )
    price: Optional[Decimal] = Field(
        None,
        gt=0,
        decimal_places=2,
        example=39.99
    )
    stock_quantity: Optional[int] = Field(
        None,
        ge=0,
        example=50
    )
    sku: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        example="WBH-002"
    )
    category: Optional[str] = Field(
        None,
        max_length=100,
        example="Electronics"
    )
    is_active: Optional[bool] = Field(
        None,
        example=True
    )

    @field_validator('sku')
    @classmethod
    def normalize_sku(cls, v: Optional[str]) -> Optional[str]:
        """Normalize SKU to uppercase when provided."""
        if v is not None:
            return v.upper().strip()
        return v


class ProductResponse(ProductBase):
    """Schema for product response."""

    id: int = Field(..., example=1)
    is_active: bool = Field(..., example=True)
    created_at: datetime = Field(..., example="2024-01-01T00:00:00")
    updated_at: datetime = Field(..., example="2024-01-01T00:00:00")

    class Config:
        from_attributes = True


class ProductInDB(ProductResponse):
    """
    Internal schema representing full database record.
    Currently same as ProductResponse - extend when needed.
    """

    pass


class StockUpdate(BaseModel):
    """Schema for updating product stock."""

    stock_quantity: int = Field(
        ...,
        ge=0,
        example=50,
        description="New stock quantity (must be >= 0)"
    )


class ProductListResponse(BaseModel):
    """Paginated product list response."""

    items: list[ProductResponse]
    total: int = Field(..., example=100)
    limit: int = Field(..., example=20)
    offset: int = Field(..., example=0)
