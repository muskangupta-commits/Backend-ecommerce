from fastapi import APIRouter, Query
from typing import Optional
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("")
async def list_products(
    search: str = Query("", description="Search by name, category, or brand"),
    category: str = Query("", description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    sort_by: str = Query("newest", description="Sort: newest, price_asc, price_desc, rating"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return product_service.get_products(
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        page=page,
        limit=limit,
    )


@router.get("/categories")
async def get_categories():
    return {"categories": product_service.get_categories()}


@router.get("/{product_id}")
async def get_product(product_id: str):
    product = product_service.get_product_by_id(product_id)
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found.")

    related = product_service.get_related_products(product["category"], product_id)
    return {"product": product, "related": related}
