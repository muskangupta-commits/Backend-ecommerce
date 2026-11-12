from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from app.database.connection import get_db
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


def _get_cart(user_id: str) -> dict:
    db = get_db()
    cart = db.carts.find_one({"user_id": user_id})
    if not cart:
        return {"user_id": user_id, "items": [], "updated_at": datetime.utcnow()}
    return cart


def get_cart(user_id: str) -> dict:
    db = get_db()
    cart = _get_cart(user_id)
    items = cart.get("items", [])
    enriched = []
    subtotal = 0.0

    for item in items:
        try:
            product = db.products.find_one({"_id": ObjectId(item["product_id"])})
        except InvalidId:
            continue
        if not product:
            continue
        product_data = {
            "id": str(product["_id"]),
            "name": product["name"],
            "price": product["price"],
            "original_price": product.get("original_price"),
            "image": product.get("image", ""),
            "category": product.get("category", ""),
            "stock": product.get("stock", 0),
        }
        line_total = product["price"] * item["quantity"]
        subtotal += line_total
        enriched.append({
            "product_id": item["product_id"],
            "product": product_data,
            "quantity": item["quantity"],
            "line_total": line_total,
        })

    delivery_charge = 0.0 if subtotal >= 500 else 40.0
    return {
        "items": enriched,
        "subtotal": round(subtotal, 2),
        "delivery_charge": delivery_charge,
        "total": round(subtotal + delivery_charge, 2),
        "item_count": sum(i["quantity"] for i in items),
    }


def add_to_cart(user_id: str, product_id: str, quantity: int) -> dict:
    db = get_db()
    try:
        product = db.products.find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid product ID.")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    if product.get("stock", 0) < 1:
        raise HTTPException(status_code=400, detail="Product is out of stock.")

    cart = _get_cart(user_id)
    items = cart.get("items", [])

    # Find existing item
    for item in items:
        if item["product_id"] == product_id:
            new_qty = item["quantity"] + quantity
            if new_qty > product["stock"]:
                raise HTTPException(status_code=400, detail=f"Only {product['stock']} units available.")
            item["quantity"] = new_qty
            break
    else:
        if quantity > product["stock"]:
            raise HTTPException(status_code=400, detail=f"Only {product['stock']} units available.")
        items.append({"product_id": product_id, "quantity": quantity})

    db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": items, "updated_at": datetime.utcnow(), "user_id": user_id}},
        upsert=True,
    )
    return get_cart(user_id)


def update_cart_item(user_id: str, product_id: str, quantity: int) -> dict:
    db = get_db()
    if quantity < 1:
        return remove_from_cart(user_id, product_id)

    try:
        product = db.products.find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid product ID.")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    if quantity > product["stock"]:
        raise HTTPException(status_code=400, detail=f"Only {product['stock']} units available.")

    cart = _get_cart(user_id)
    items = cart.get("items", [])

    found = False
    for item in items:
        if item["product_id"] == product_id:
            item["quantity"] = quantity
            found = True
            break

    if not found:
        items.append({"product_id": product_id, "quantity": quantity})

    db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": items, "updated_at": datetime.utcnow()}},
        upsert=True,
    )
    return get_cart(user_id)


def remove_from_cart(user_id: str, product_id: str) -> dict:
    db = get_db()
    cart = _get_cart(user_id)
    items = [i for i in cart.get("items", []) if i["product_id"] != product_id]
    db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": items, "updated_at": datetime.utcnow()}},
        upsert=True,
    )
    return get_cart(user_id)


def clear_cart(user_id: str):
    db = get_db()
    db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "updated_at": datetime.utcnow()}},
        upsert=True,
    )


def merge_guest_cart(user_id: str, guest_items: list):
    for item in guest_items:
        try:
            add_to_cart(user_id, item["product_id"], item["quantity"])
        except Exception:
            pass
