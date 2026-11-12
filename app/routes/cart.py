from fastapi import APIRouter, Depends, Body
from app.models.schemas import CartItemRequest
from app.services import cart_service
from app.core.security import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("")
async def get_cart(current_user: dict = Depends(get_current_user)):
    return cart_service.get_cart(current_user["sub"])


@router.post("")
async def add_to_cart(
    body: CartItemRequest,
    current_user: dict = Depends(get_current_user),
):
    return cart_service.add_to_cart(current_user["sub"], body.product_id, body.quantity)


@router.put("/{product_id}")
async def update_cart_item(
    product_id: str,
    quantity: int = Body(..., embed=True),
    current_user: dict = Depends(get_current_user),
):
    return cart_service.update_cart_item(current_user["sub"], product_id, quantity)


@router.delete("/{product_id}")
async def remove_from_cart(
    product_id: str,
    current_user: dict = Depends(get_current_user),
):
    return cart_service.remove_from_cart(current_user["sub"], product_id)


@router.post("/merge")
async def merge_guest_cart(
    guest_items: list = Body(...),
    current_user: dict = Depends(get_current_user),
):
    cart_service.merge_guest_cart(current_user["sub"], guest_items)
    return cart_service.get_cart(current_user["sub"])
