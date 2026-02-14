"""
Manual test for ProductClient against running Product Service.
"""

import asyncio
from app.clients.product_client import (
    ProductClient,
    ProductNotFoundError,
    ProductServiceUnavailableError,
    ProductServiceTimeoutError,
)


async def main():
    client = ProductClient()

    # Test 1: Happy path - Get existing product
    print("--- Test 1: Get existing product (ID=1) ---")
    try:
        product = await client.get_product(1)
        pid = product.get("id")
        pname = product.get("name")
        pprice = product.get("price")
        pstock = product.get("stock_quantity")
        print(f"  id: {pid}")
        print(f"  name: {pname}")
        print(f"  price: {pprice}")
        print(f"  stock_quantity: {pstock}")
        assert pid == 1, f"Expected id=1, got {pid}"
        assert pname is not None, "name should not be None"
        assert pprice is not None, "price should not be None"
        print("  PASSED")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")

    # Test 2: Product not found
    print()
    print("--- Test 2: Product not found (ID=9999) ---")
    try:
        await client.get_product(9999)
        print("  FAILED: No exception raised")
    except ProductNotFoundError as e:
        assert e.product_id == 9999, f"Expected product_id=9999, got {e.product_id}"
        print(f"  Exception: {e}")
        print(f"  product_id: {e.product_id}")
        print("  PASSED")
    except Exception as e:
        print(f"  FAILED: Wrong exception: {type(e).__name__}: {e}")

    # Summary
    print()
    print("--- All tests completed ---")


if __name__ == "__main__":
    asyncio.run(main())
