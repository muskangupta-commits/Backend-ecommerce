from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, List
from app.database.connection import get_db
from app.core.config import settings
from app.services import cart_service
from fastapi import HTTPException
import stripe
import random
import string
import logging

logger = logging.getLogger(__name__)

ORDER_STATUSES = [
    "Order Placed", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"
]


def _serialize_order(order: dict) -> dict:
    if not order:
        return None
    order = dict(order)
    order["id"] = str(order.pop("_id"))
    return order


def _generate_order_id() -> str:
    suffix = ''.join(random.choices(string.digits, k=5))
    return f"ORD-{suffix}"


def place_order(user_id: str, items: list, shipping_address: dict, payment_method: str, payment_id: str = None) -> dict:
    db = get_db()

    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    # Fetch trusted prices from MongoDB
    order_items = []
    subtotal = 0.0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]

        try:
            product = db.products.find_one({"_id": ObjectId(product_id)})
        except InvalidId:
            raise HTTPException(status_code=400, detail=f"Invalid product ID: {product_id}")

        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")

        if product.get("stock", 0) < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product['name']}'. Available: {product.get('stock', 0)}"
            )

        line_total = product["price"] * quantity
        subtotal += line_total

        order_items.append({
            "product_id": product_id,
            "name": product["name"],
            "image": product.get("image", ""),
            "price": product["price"],
            "quantity": quantity,
            "line_total": line_total,
        })

    delivery_charge = 0.0 if subtotal >= 500 else 40.0
    total_amount = subtotal + delivery_charge

    # Generate unique order ID
    order_id = _generate_order_id()
    while db.orders.find_one({"order_id": order_id}):
        order_id = _generate_order_id()

    # Fetch user details to attach direct customer identifiers
    user = None
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        pass
    if not user:
        user = db.users.find_one({"_id": user_id})

    customer_phone = (shipping_address or {}).get("phone") or (user.get("phone") if user else None)
    customer_name = (shipping_address or {}).get("full_name") or (user.get("name") if user else None)
    customer_email = (user.get("email") if user else None) or (shipping_address or {}).get("email")

    online_payment_methods = {"Card", "Online", "Stripe", "UPI"}
    if payment_method in online_payment_methods:
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(status_code=503, detail="Online payments are not configured.")
        if not payment_id:
            raise HTTPException(status_code=400, detail="A successful Stripe payment is required.")

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            intent = stripe.PaymentIntent.retrieve(payment_id)
        except stripe.error.StripeError as e:
            logger.warning("Stripe could not verify order payment: %s", e)
            raise HTTPException(status_code=502, detail="Stripe could not verify the payment.") from e

        if (
            intent.status != "succeeded"
            or intent.amount != int(round(total_amount * 100))
            or intent.currency.lower() != "inr"
            or intent.metadata.get("user_id") != user_id
        ):
            raise HTTPException(status_code=400, detail="Payment does not match this order.")
        payment_status = "Paid"
    elif payment_method == "COD":
        payment_status = "Pending"
        payment_id = None
    else:
        raise HTTPException(status_code=400, detail="Unsupported payment method.")

    order_doc = {
        "order_id": order_id,
        "user_id": user_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email,
        "items": order_items,
        "shipping_address": shipping_address,
        "subtotal": round(subtotal, 2),
        "delivery_charge": delivery_charge,
        "total_amount": round(total_amount, 2),
        "payment_method": payment_method,
        "payment_status": payment_status,
        "payment_id": payment_id,
        "order_status": "Order Placed",
        "status_history": [
            {"status": "Order Placed", "timestamp": datetime.utcnow().isoformat()}
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = db.orders.insert_one(order_doc)

    # Persist address to user profile in Atlas so it is automatically remembered for future orders
    try:
        user_filter = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"_id": user_id}
        db.users.update_one(
            user_filter,
            {
                "$set": {
                    "saved_address": shipping_address,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    except Exception as e:
        logger.warning(f"Could not persist saved_address to user profile: {e}")

    # Deduct stock
    for item in order_items:
        try:
            db.products.update_one(
                {"_id": ObjectId(item["product_id"])},
                {"$inc": {"stock": -item["quantity"]}}
            )
        except Exception as e:
            logger.warning(f"Stock update failed for {item['product_id']}: {e}")

    # Clear cart
    cart_service.clear_cart(user_id)

    order = db.orders.find_one({"_id": result.inserted_id})
    return _serialize_order(order)


def get_user_orders(user_id: str) -> List[dict]:
    db = get_db()
    orders = list(db.orders.find({"user_id": user_id}).sort("created_at", -1))
    return [_serialize_order(o) for o in orders]


def get_order_by_id(order_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    db = get_db()
    query = {}

    try:
        # Try ObjectId lookup first
        query["_id"] = ObjectId(order_id)
    except InvalidId:
        # Fall back to order_id string lookup
        query["order_id"] = order_id

    order = db.orders.find_one(query)
    if not order:
        return None
    if user_id and order.get("user_id") != user_id:
        return None  # Not this user's order
    return _serialize_order(order)


def update_order_status(order_id: str, new_status: str) -> Optional[dict]:
    db = get_db()
    query = {}
    try:
        query["_id"] = ObjectId(order_id)
    except InvalidId:
        query["order_id"] = order_id

    history_entry = {"status": new_status, "timestamp": datetime.utcnow().isoformat()}
    update_doc = {
        "$set": {"order_status": new_status, "updated_at": datetime.utcnow()},
        "$push": {"status_history": history_entry},
    }

    # If the order reaches 'Delivered', mark COD payments as 'Paid'
    if new_status == "Delivered":
        update_doc["$set"]["payment_status"] = "Paid"

    db.orders.update_one(query, update_doc)
    order = db.orders.find_one(query)
    return _serialize_order(order)


def cancel_order(order_id: str, user_id: str, reason: str = "Cancelled by user") -> dict:
    db = get_db()
    query = {}
    try:
        query["_id"] = ObjectId(order_id)
    except InvalidId:
        query["order_id"] = order_id

    order = db.orders.find_one(query)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to cancel this order.")

    current_status = order.get("order_status", "Order Placed")
    if current_status in ["Delivered", "Cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Order cannot be cancelled because it is already '{current_status}'."
        )

    # Restock inventory in MongoDB
    for item in order.get("items", []):
        prod_id = item.get("product_id")
        qty = item.get("quantity", 1)
        if prod_id:
            try:
                prod_query = {"_id": ObjectId(prod_id)} if ObjectId.is_valid(prod_id) else {"_id": prod_id}
                db.products.update_one(prod_query, {"$inc": {"stock": qty}})
            except Exception as e:
                logger.warning(f"Could not restock product {prod_id}: {e}")

    # Determine refund details
    payment_status = order.get("payment_status", "Pending")
    is_paid = payment_status == "Paid"
    refund_status = "Refund Initiated (Stripe)" if is_paid else "No Refund Needed (COD)"

    history_entry = {
        "status": "Cancelled",
        "timestamp": datetime.utcnow().isoformat(),
        "reason": reason,
    }

    db.orders.update_one(
        query,
        {
            "$set": {
                "order_status": "Cancelled",
                "cancellation_reason": reason,
                "refund_status": refund_status,
                "updated_at": datetime.utcnow(),
            },
            "$push": {"status_history": history_entry},
        }
    )

    updated = db.orders.find_one(query)
    return _serialize_order(updated)


def get_all_orders(page: int = 1, limit: int = 20) -> dict:
    db = get_db()
    total = db.orders.count_documents({})
    skip = (page - 1) * limit
    orders = list(db.orders.find({}).sort("created_at", -1).skip(skip).limit(limit))
    return {
        "orders": [_serialize_order(o) for o in orders],
        "total": total,
        "page": page,
    }


def get_dashboard_stats() -> dict:
    db = get_db()
    total_products = db.products.count_documents({})
    total_orders = db.orders.count_documents({})
    total_users = db.users.count_documents({"role": "customer"})

    # Total revenue from delivered orders
    pipeline = [
        {"$match": {"order_status": {"$nin": ["Cancelled"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
    ]
    revenue_result = list(db.orders.aggregate(pipeline))
    total_sales = revenue_result[0]["total"] if revenue_result else 0.0

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_users": total_users,
        "total_sales": round(total_sales, 2),
    }
