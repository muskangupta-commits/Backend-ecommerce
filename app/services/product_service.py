from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, List
from app.database.connection import get_db
import math
import re


CATEGORIES = [
    "Electronics", "Mobiles", "Fashion", "Home & Kitchen",
    "Beauty", "Books", "Sports", "Accessories"
]


def _serialize(doc: dict) -> dict:
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def _build_search_regex(word: str) -> str:
    clean = re.sub(r"[^\w]", "", word).strip()
    if not clean:
        return ""
    if clean.lower().endswith("s") and len(clean) > 3:
        stem = clean[:-1]
        return f"{stem}('?s)?"
    return f"{clean}('?s)?"


def get_products(
    search: str = "",
    category: str = "",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "newest",
    page: int = 1,
    limit: int = 50,
) -> dict:
    db = get_db()
    query = {}

    if category and category.lower() != "all":
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    price_filter = {}
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price
    if price_filter:
        query["price"] = price_filter

    # Sorting
    sort_map = {
        "price_asc": [("price", 1)],
        "price_desc": [("price", -1)],
        "newest": [("created_at", -1)],
        "rating": [("rating", -1)],
    }
    sort_order = sort_map.get(sort_by, [("created_at", -1)])

    if search:
        search_terms = search.strip().split()
        patterns = [_build_search_regex(w) for w in search_terms if _build_search_regex(w)]

        if patterns:
            # 1. Try strict matching (all words match across fields)
            and_clauses = []
            for p in patterns:
                and_clauses.append({
                    "$or": [
                        {"name": {"$regex": p, "$options": "i"}},
                        {"description": {"$regex": p, "$options": "i"}},
                        {"category": {"$regex": p, "$options": "i"}},
                        {"brand": {"$regex": p, "$options": "i"}},
                        {"tags": {"$regex": p, "$options": "i"}},
                    ]
                })

            strict_query = {**query, "$and": and_clauses}
            total = db.products.count_documents(strict_query)

            if total > 0:
                skip = (page - 1) * limit
                products = list(db.products.find(strict_query).sort(sort_order).skip(skip).limit(limit))
                return {
                    "products": [_serialize(p) for p in products],
                    "total": total,
                    "page": page,
                    "pages": math.ceil(total / limit) if limit else 1,
                }

            # 2. Relaxed matching: ANY word matches ($or)
            or_clauses = []
            for p in patterns:
                or_clauses.extend([
                    {"name": {"$regex": p, "$options": "i"}},
                    {"description": {"$regex": p, "$options": "i"}},
                    {"category": {"$regex": p, "$options": "i"}},
                    {"brand": {"$regex": p, "$options": "i"}},
                    {"tags": {"$regex": p, "$options": "i"}},
                ])
            query["$or"] = or_clauses

    total = db.products.count_documents(query)
    skip = (page - 1) * limit
    products = list(db.products.find(query).sort(sort_order).skip(skip).limit(limit))

    return {
        "products": [_serialize(p) for p in products],
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if limit else 1,
    }


def get_product_by_id(product_id: str) -> Optional[dict]:
    try:
        db = get_db()
        product = db.products.find_one({"_id": ObjectId(product_id)})
        return _serialize(product)
    except InvalidId:
        return None


def get_related_products(category: str, exclude_id: str, limit: int = 6) -> List[dict]:
    db = get_db()
    try:
        exclude_oid = ObjectId(exclude_id)
    except InvalidId:
        exclude_oid = None
    query = {"category": {"$regex": f"^{category}$", "$options": "i"}}
    if exclude_oid:
        query["_id"] = {"$ne": exclude_oid}
    products = list(db.products.find(query).limit(limit))
    return [_serialize(p) for p in products]


def create_product(data: dict) -> dict:
    db = get_db()
    data["created_at"] = datetime.utcnow()
    result = db.products.insert_one(data)
    return _serialize(db.products.find_one({"_id": result.inserted_id}))


def update_product(product_id: str, data: dict) -> Optional[dict]:
    try:
        db = get_db()
        data["updated_at"] = datetime.utcnow()
        data = {k: v for k, v in data.items() if v is not None}
        db.products.update_one({"_id": ObjectId(product_id)}, {"$set": data})
        return _serialize(db.products.find_one({"_id": ObjectId(product_id)}))
    except InvalidId:
        return None


def delete_product(product_id: str) -> bool:
    try:
        db = get_db()
        result = db.products.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0
    except InvalidId:
        return False


def get_categories() -> List[str]:
    return CATEGORIES
