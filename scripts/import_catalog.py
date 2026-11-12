import urllib.request
import json
import os
import sys
from datetime import datetime

CATEGORY_MAP = {
    "smartphones": "Mobiles",
    "mobile-accessories": "Mobiles",
    "laptops": "Electronics",
    "tablets": "Electronics",
    "mens-shirts": "Fashion",
    "mens-shoes": "Fashion",
    "womens-dresses": "Fashion",
    "womens-shoes": "Fashion",
    "tops": "Fashion",
    "kitchen-accessories": "Home & Kitchen",
    "home-decoration": "Home & Kitchen",
    "furniture": "Home & Kitchen",
    "groceries": "Home & Kitchen",
    "beauty": "Beauty",
    "skin-care": "Beauty",
    "fragrances": "Beauty",
    "sports-accessories": "Sports",
    "motorcycle": "Sports",
    "vehicle": "Accessories",
    "sunglasses": "Accessories",
    "womens-jewellery": "Accessories",
    "womens-bags": "Accessories",
    "mens-watches": "Accessories",
    "womens-watches": "Accessories",
}

def fetch_and_transform():
    url = "https://dummyjson.com/products?limit=194"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching live catalog: {e}")
        return []

    transformed = []
    now = datetime.utcnow()

    for item in data.get("products", []):
        cat_raw = item.get("category", "")
        department = CATEGORY_MAP.get(cat_raw, "Home & Kitchen")
        
        # Convert USD to INR (e.g. 1 USD ~ 85 INR)
        usd_price = item.get("price", 10)
        inr_price = max(199, round(usd_price * 85))
        discount = item.get("discountPercentage", 15)
        original_price = round(inr_price / (1 - (discount / 100)))

        # Image priority: thumbnail, first image, or placeholder
        image = item.get("thumbnail")
        if not image and item.get("images"):
            image = item["images"][0]

        tags = item.get("tags", [])
        tags.append(cat_raw)
        tags.append(cat_raw.replace("-", " "))

        transformed.append({
            "sku": item.get("sku", f"DJ-{item['id']}"),
            "name": item.get("title", "Product"),
            "category": department,
            "raw_category": cat_raw,
            "brand": item.get("brand", "Cartify Select"),
            "price": inr_price,
            "original_price": original_price,
            "rating": round(item.get("rating", 4.5), 1),
            "stock": item.get("stock", 25),
            "image": image,
            "description": item.get("description", ""),
            "tags": " ".join(tags),
            "created_at": now,
            "updated_at": now,
        })

    return transformed

if __name__ == "__main__":
    products = fetch_and_transform()
    print(f"Successfully processed {len(products)} products from live catalog.")
