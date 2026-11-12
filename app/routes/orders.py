from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import OrderCreate
from app.services import order_service
from app.core.security import get_current_user, require_admin

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("")
async def place_order(
    body: OrderCreate,
    current_user: dict = Depends(get_current_user),
):
    items = [{"product_id": i.product_id, "quantity": i.quantity} for i in body.items]
    order = order_service.place_order(
        user_id=current_user["sub"],
        items=items,
        shipping_address=body.shipping_address.model_dump(),
        payment_method=body.payment_method,
        payment_id=body.payment_id,
    )
    return {"success": True, "order": order}


@router.get("/my-orders")
async def my_orders(current_user: dict = Depends(get_current_user)):
    orders = order_service.get_user_orders(current_user["sub"])
    return {"orders": orders}


@router.get("/{order_id}")
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    user_id = None if current_user.get("role") == "admin" else current_user["sub"]
    order = order_service.get_order_by_id(order_id, user_id=user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    payload: dict = {},
    current_user: dict = Depends(get_current_user),
):
    reason = (payload or {}).get("reason", "Cancelled by customer")
    order = order_service.cancel_order(
        order_id=order_id,
        user_id=current_user["sub"],
        reason=reason,
    )
    return {"success": True, "message": "Order has been cancelled successfully.", "order": order}


@router.put("/{order_id}/status")
async def update_user_order_status(
    order_id: str,
    payload: dict,
    admin: dict = Depends(require_admin),
):
    new_status = payload.get("status")
    allowed = ["Order Placed", "Confirmed", "Processing", "Shipped", "Delivered"]
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status value. Must be one of {allowed}")
    
    if not order_service.get_order_by_id(order_id):
        raise HTTPException(status_code=404, detail="Order not found or permission denied.")
    
    updated = order_service.update_order_status(order_id, new_status)
    return {"success": True, "order": updated}
