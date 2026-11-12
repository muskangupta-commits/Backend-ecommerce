from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ProductCreate, ProductUpdate, OrderStatusUpdate
from app.services import product_service, order_service
from app.core.security import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def dashboard(admin: dict = Depends(require_admin)):
    return order_service.get_dashboard_stats()


@router.post("/products")
async def create_product(body: ProductCreate, admin: dict = Depends(require_admin)):
    product = product_service.create_product(body.model_dump())
    return {"success": True, "product": product}


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    body: ProductUpdate,
    admin: dict = Depends(require_admin),
):
    product = product_service.update_product(product_id, body.model_dump(exclude_none=True))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return {"success": True, "product": product}


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, admin: dict = Depends(require_admin)):
    deleted = product_service.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found.")
    return {"success": True, "message": "Product deleted."}


@router.get("/orders")
async def list_all_orders(
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(require_admin),
):
    return order_service.get_all_orders(page=page, limit=limit)


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: OrderStatusUpdate,
    admin: dict = Depends(require_admin),
):
    order = order_service.update_order_status(order_id, body.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return {"success": True, "order": order}
