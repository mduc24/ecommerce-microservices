"""
API routes for product catalog management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database import get_db
from app.models import Product
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    StockUpdate,
)

router = APIRouter(prefix="/api/v1/products", tags=["products"])

ALLOWED_SORT_FIELDS = {
    "price": Product.price.asc(),
    "-price": Product.price.desc(),
    "created_at": Product.created_at.asc(),
    "-created_at": Product.created_at.desc(),
    "name": Product.name.asc(),
    "-name": Product.name.desc(),
}


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new product."""
    # Check SKU uniqueness
    result = await db.execute(
        select(Product).where(Product.sku == product_data.sku)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SKU already exists",
        )

    new_product = Product(**product_data.model_dump())

    try:
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SKU already exists",
        )

    return new_product


@router.get("", response_model=ProductListResponse)
async def list_products(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of products per page",
    ),
    offset: int = Query(default=0, ge=0, description="Number of products to skip"),
    category: str | None = Query(default=None, description="Filter by category"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    name: str | None = Query(default=None, description="Search by name (case-insensitive)"),
    sort_by: str = Query(
        default="-created_at",
        description="Sort field: price, -price, created_at, -created_at, name, -name",
    ),
):
    """List products with pagination, filtering, and sorting."""
    # Base query
    query = select(Product)
    count_query = select(func.count(Product.id))

    # Filters
    if category is not None:
        query = query.where(Product.category == category)
        count_query = count_query.where(Product.category == category)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
        count_query = count_query.where(Product.is_active == is_active)
    if name is not None:
        query = query.where(Product.name.ilike(f"%{name}%"))
        count_query = count_query.where(Product.name.ilike(f"%{name}%"))

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Sorting
    order_clause = ALLOWED_SORT_FIELDS.get(sort_by)
    if order_clause is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by. Allowed: {', '.join(ALLOWED_SORT_FIELDS.keys())}",
        )
    query = query.order_by(order_clause)

    # Pagination
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()

    return ProductListResponse(
        items=products,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single product by ID."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Full update of a product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Check SKU uniqueness if changed
    if product_data.sku != product.sku:
        sku_result = await db.execute(
            select(Product).where(Product.sku == product_data.sku)
        )
        if sku_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SKU already exists",
            )

    for field, value in product_data.model_dump().items():
        setattr(product, field, value)

    try:
        await db.commit()
        await db.refresh(product)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SKU already exists",
        )

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def partial_update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Partial update of a product. Only provided fields are updated."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = product_data.model_dump(exclude_unset=True)

    # Check SKU uniqueness if changed
    if "sku" in update_data and update_data["sku"] != product.sku:
        sku_result = await db.execute(
            select(Product).where(Product.sku == update_data["sku"])
        )
        if sku_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SKU already exists",
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        await db.commit()
        await db.refresh(product)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SKU already exists",
        )

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a product (sets is_active to False)."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product.is_active = False
    await db.commit()


@router.patch("/{product_id}/stock", response_model=ProductResponse)
async def update_stock(
    product_id: int,
    stock_data: StockUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update product stock quantity (absolute value)."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product.stock_quantity = stock_data.stock_quantity
    await db.commit()
    await db.refresh(product)

    return product
