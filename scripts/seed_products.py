import os
import sys
from datetime import datetime
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

# Add parent directory to path so we can import app modules if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ecommerce_db")

DEMO_PRODUCTS = [
    # Electronics
    {
        "sku": "ELEC-001",
        "name": "Sony WH-1000XM5 Wireless Noise-Canceling Headphones",
        "category": "Electronics",
        "brand": "Sony",
        "price": 24990,
        "original_price": 29990,
        "rating": 4.8,
        "stock": 35,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
        "description": "Industry-leading noise canceling with two processors and 8 microphones. Up to 30-hour battery life with ultra-comfortable lightweight design."
    },
    {
        "sku": "ELEC-002",
        "name": "Apple Watch Series 9 GPS 45mm",
        "category": "Electronics",
        "brand": "Apple",
        "price": 41999,
        "original_price": 44900,
        "rating": 4.7,
        "stock": 20,
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80",
        "description": "S9 SiP chip enables a magical new way to use your watch without touching the screen. Advanced health and safety features."
    },
    {
        "sku": "ELEC-003",
        "name": "JBL Flip 6 Portable Bluetooth Speaker",
        "category": "Electronics",
        "brand": "JBL",
        "price": 9999,
        "original_price": 13999,
        "rating": 4.6,
        "stock": 45,
        "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600&auto=format&fit=crop&q=80",
        "description": "Bold JBL Original Pro Sound with IP67 waterproof and dustproof design. 12 hours of playtime on a single charge."
    },
    {
        "sku": "ELEC-004",
        "name": "Logitech MX Master 3S Wireless Performance Mouse",
        "category": "Electronics",
        "brand": "Logitech",
        "price": 8995,
        "original_price": 10995,
        "rating": 4.9,
        "stock": 28,
        "image": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&auto=format&fit=crop&q=80",
        "description": "Quiet Clicks and 8,000 DPI track-on-glass sensor. MagSpeed electromagnetic scrolling for ultimate precision."
    },

    # Mobiles
    {
        "sku": "MOB-001",
        "name": "Apple iPhone 15 Pro (128 GB) - Natural Titanium",
        "category": "Mobiles",
        "brand": "Apple",
        "price": 127990,
        "original_price": 134900,
        "rating": 4.9,
        "stock": 15,
        "image": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80",
        "description": "Forged in titanium with aerospace-grade strength. A17 Pro game-changing chip with pro camera system."
    },
    {
        "sku": "MOB-002",
        "name": "Samsung Galaxy S24 Ultra 5G (Titanium Gray)",
        "category": "Mobiles",
        "brand": "Samsung",
        "price": 119999,
        "original_price": 134999,
        "rating": 4.8,
        "stock": 18,
        "image": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=600&auto=format&fit=crop&q=80",
        "description": "Galaxy AI is here. 200MP camera with revolutionary Nightography zoom and integrated S Pen stylus."
    },
    {
        "sku": "MOB-003",
        "name": "OnePlus 12 (Silky Black, 256 GB)",
        "category": "Mobiles",
        "brand": "OnePlus",
        "price": 64999,
        "original_price": 69999,
        "rating": 4.6,
        "stock": 25,
        "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600&auto=format&fit=crop&q=80",
        "description": "Snapdragon 8 Gen 3, 4th Gen Hasselblad Camera System with 100W SUPERVOOC ultra-fast charging."
    },
    {
        "sku": "MOB-004",
        "name": "Google Pixel 8 Pro (Bay, 128 GB)",
        "category": "Mobiles",
        "brand": "Google",
        "price": 89999,
        "original_price": 106999,
        "rating": 4.7,
        "stock": 12,
        "image": "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=600&auto=format&fit=crop&q=80",
        "description": "Engineered by Google with Tensor G3 chip and next-gen camera capabilities including Magic Editor."
    },

    # Fashion
    {
        "sku": "FASH-001",
        "name": "Levi's Men's Slim Fit Denim Trucker Jacket",
        "category": "Fashion",
        "brand": "Levi's",
        "price": 3899,
        "original_price": 5999,
        "rating": 4.5,
        "stock": 40,
        "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&auto=format&fit=crop&q=80",
        "description": "Classic trucker silhouette in durable non-stretch denim. Timeless aesthetic designed to improve with age."
    },
    {
        "sku": "FASH-002",
        "name": "Nike Air Max 270 React Running Shoes",
        "category": "Fashion",
        "brand": "Nike",
        "price": 8495,
        "original_price": 11995,
        "rating": 4.7,
        "stock": 30,
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80",
        "description": "Nike's biggest heel Air unit yet delivers all-day cushioning and sleek streetwear styling."
    },
    {
        "sku": "FASH-003",
        "name": "Ray-Ban Classic Polarized Aviator Sunglasses",
        "category": "Fashion",
        "brand": "Ray-Ban",
        "price": 7990,
        "original_price": 9990,
        "rating": 4.8,
        "stock": 25,
        "image": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&auto=format&fit=crop&q=80",
        "description": "Iconic pilot shape with crystal green polarized lenses providing 100% UV protection and glare elimination."
    },
    {
        "sku": "FASH-004",
        "name": "Tommy Hilfiger Men's Organic Cotton Polo",
        "category": "Fashion",
        "brand": "Tommy Hilfiger",
        "price": 2799,
        "original_price": 3999,
        "rating": 4.4,
        "stock": 50,
        "image": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=600&auto=format&fit=crop&q=80",
        "description": "Crafted with 100% breathable organic piqué cotton with signature embroidered flag on chest."
    },
    {
        "sku": "FASH-005",
        "name": "Allen Solly Men's Regular Fit Cotton Casual Shirt",
        "category": "Fashion",
        "brand": "Allen Solly",
        "price": 1499,
        "original_price": 2299,
        "rating": 4.6,
        "stock": 45,
        "image": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&auto=format&fit=crop&q=80",
        "description": "Premium 100% breathable combed cotton men's button-down casual shirt with curved hem."
    },
    {
        "sku": "FASH-006",
        "name": "Peter England Men's Slim Fit Formal Plain Shirt (Sky Blue)",
        "category": "Fashion",
        "brand": "Peter England",
        "price": 1299,
        "original_price": 1899,
        "rating": 4.5,
        "stock": 60,
        "image": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=600&auto=format&fit=crop&q=80",
        "description": "Crisp poly-cotton formal shirt featuring spread collar and single cuff for professional corporate attire."
    },

    # Home & Kitchen
    {
        "sku": "HOME-001",
        "name": "Philips Air Fryer HD9252/90 4.1L Digital Touch",
        "category": "Home & Kitchen",
        "brand": "Philips",
        "price": 6999,
        "original_price": 11995,
        "rating": 4.6,
        "stock": 35,
        "image": "https://images.unsplash.com/photo-1585670210693-e7fdd16b142e?w=600&auto=format&fit=crop&q=80",
        "description": "Rapid Air technology fries with up to 90% less fat. Preset touch programs for effortless crispy meals."
    },
    {
        "sku": "HOME-002",
        "name": "Nespresso Vertuo Pop Coffee Machine",
        "category": "Home & Kitchen",
        "brand": "Nespresso",
        "price": 14999,
        "original_price": 18999,
        "rating": 4.7,
        "stock": 16,
        "image": "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=600&auto=format&fit=crop&q=80",
        "description": "Centrifusion barcode extraction technology makes 4 cup sizes from Espresso to large Mug with rich crema."
    },
    {
        "sku": "HOME-003",
        "name": "Dyson V8 Absolute Cordless Vacuum Cleaner",
        "category": "Home & Kitchen",
        "brand": "Dyson",
        "price": 29900,
        "original_price": 39900,
        "rating": 4.8,
        "stock": 14,
        "image": "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=600&auto=format&fit=crop&q=80",
        "description": "Engineered for deep cleans with acoustic baffles, digital motor V8, and whole-machine filtration."
    },
    {
        "sku": "HOME-004",
        "name": "Instant Pot Duo 7-in-1 Electric Pressure Cooker 6 Qt",
        "category": "Home & Kitchen",
        "brand": "Instant Pot",
        "price": 8499,
        "original_price": 12999,
        "rating": 4.7,
        "stock": 22,
        "image": "https://images.unsplash.com/photo-1544233726-9f1d2b27be8b?w=600&auto=format&fit=crop&q=80",
        "description": "Pressure cooker, slow cooker, rice cooker, steamer, sauté pan, yogurt maker and food warmer in one."
    },
    {
        "sku": "HOME-005",
        "name": "Preethi Zodiac MG-218 750-Watt Mixer Grinder with 5 Jars",
        "category": "Home & Kitchen",
        "brand": "Preethi",
        "price": 8999,
        "original_price": 11495,
        "rating": 4.8,
        "stock": 30,
        "image": "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=600&auto=format&fit=crop&q=80",
        "description": "Powerful Vega W5 motor with 3-in-1 Insta Fresh fruit juicer jar, master chef food processor jar, and stainless steel grinding jars."
    },
    {
        "sku": "HOME-006",
        "name": "KitchenAid Artisan Series 5-Quart Tilt-Head Stand Mixer (Empire Red)",
        "category": "Home & Kitchen",
        "brand": "KitchenAid",
        "price": 42990,
        "original_price": 49990,
        "rating": 4.9,
        "stock": 14,
        "image": "https://images.unsplash.com/photo-1594385208974-2e75f8d7bb48?w=600&auto=format&fit=crop&q=80",
        "description": "Iconic stand mixer with 10 speeds and 59 touchpoints around the bowl for thorough ingredient incorporation."
    },
    {
        "sku": "HOME-007",
        "name": "Bosch TrueMixx Pro 1000-Watt Mixer Grinder (Bold Black)",
        "category": "Home & Kitchen",
        "brand": "Bosch",
        "price": 7499,
        "original_price": 9999,
        "rating": 4.7,
        "stock": 25,
        "image": "https://images.unsplash.com/photo-1588854337236-6889d631faa8?w=600&auto=format&fit=crop&q=80",
        "description": "PoundingBlade technology with stone pounding effect for authentic masala flavors, active cooling, and overload protection."
    },
    {
        "sku": "HOME-008",
        "name": "Philips Daily Collection 250W Hand Mixer and Blender",
        "category": "Home & Kitchen",
        "brand": "Philips",
        "price": 2499,
        "original_price": 3295,
        "rating": 4.6,
        "stock": 40,
        "image": "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=600&auto=format&fit=crop&q=80",
        "description": "Ergonomic lightweight hand mixer with dual stainless steel strip beaters and 3 speed controls for effortless whipping and blending."
    },
    {
        "sku": "HOME-009",
        "name": "Bajaj Rex 500W Mixer Grinder with 3 Stainless Steel Jars",
        "category": "Home & Kitchen",
        "brand": "Bajaj",
        "price": 2199,
        "original_price": 3599,
        "rating": 4.5,
        "stock": 50,
        "image": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=600&auto=format&fit=crop&q=80",
        "description": "Durable 500W motor with multi-functional blade system, rust-proof stainless steel jars, and easy-grip handles."
    },
    {
        "sku": "HOME-010",
        "name": "NutriBullet Pro 900W High-Speed Personal Mixer & Blender",
        "category": "Home & Kitchen",
        "brand": "NutriBullet",
        "price": 7999,
        "original_price": 10999,
        "rating": 4.8,
        "stock": 28,
        "image": "https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=600&auto=format&fit=crop&q=80",
        "description": "Compact high-speed extractor with 900 watts of power to pulverize the toughest fruits, vegetables, seeds, and nuts."
    },
    {
        "sku": "HOME-011",
        "name": "ArtStreet Solid Wood Collage Photo Frame Set of 8 (Black)",
        "category": "Home & Kitchen",
        "brand": "ArtStreet",
        "price": 1199,
        "original_price": 2499,
        "rating": 4.6,
        "stock": 35,
        "image": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=600&auto=format&fit=crop&q=80",
        "description": "Premium solid wood wall photo frames set with plexiglass sheet and multiple layout templates for family photos."
    },
    {
        "sku": "HOME-012",
        "name": "Paper Plane Design Classic Tabletop Picture & Photo Frame 5x7",
        "category": "Home & Kitchen",
        "brand": "Paper Plane",
        "price": 499,
        "original_price": 899,
        "rating": 4.5,
        "stock": 50,
        "image": "https://images.unsplash.com/photo-1582561424760-0321d75e81fa?w=600&auto=format&fit=crop&q=80",
        "description": "Elegant textured desktop photo frame with easel stand, ideal for portrait photography and living room table decor."
    },

    # Beauty
    {
        "sku": "BEAU-001",
        "name": "Dior Sauvage Eau De Parfum 100ml",
        "category": "Beauty",
        "brand": "Dior",
        "price": 11500,
        "original_price": 13500,
        "rating": 4.9,
        "stock": 20,
        "image": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=600&auto=format&fit=crop&q=80",
        "description": "Juicy and spicy Calabrian bergamot blends with smoky accents of Papua New Guinean vanilla absolute."
    },
    {
        "sku": "BEAU-002",
        "name": "The Ordinary Niacinamide 10% + Zinc 1% 60ml",
        "category": "Beauty",
        "brand": "The Ordinary",
        "price": 950,
        "original_price": 1100,
        "rating": 4.6,
        "stock": 80,
        "image": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=600&auto=format&fit=crop&q=80",
        "description": "High-strength vitamin and mineral blemish formula that visibly targets skin texture and enlarged pores."
    },
    {
        "sku": "BEAU-003",
        "name": "CeraVe Hydrating Facial Cleanser 473ml",
        "category": "Beauty",
        "brand": "CeraVe",
        "price": 1350,
        "original_price": 1699,
        "rating": 4.7,
        "stock": 60,
        "image": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600&auto=format&fit=crop&q=80",
        "description": "Formulated with 3 essential ceramides and hyaluronic acid to cleanse and hydrate without stripping skin barrier."
    },
    {
        "sku": "BEAU-004",
        "name": "L'Oréal Professionnel Absolut Repair Hair Mask",
        "category": "Beauty",
        "brand": "L'Oréal",
        "price": 890,
        "original_price": 1150,
        "rating": 4.5,
        "stock": 42,
        "image": "https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=600&auto=format&fit=crop&q=80",
        "description": "Enriched with Gold Quinoa and protein to instantly restore damaged hair fiber with lightweight touch."
    },

    # Books
    {
        "sku": "BOOK-001",
        "name": "Atomic Habits by James Clear (Hardcover)",
        "category": "Books",
        "brand": "Penguin Random House",
        "price": 599,
        "original_price": 799,
        "rating": 4.9,
        "stock": 100,
        "image": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80",
        "description": "An easy and proven way to build good habits and break bad ones. Over 15 million copies sold globally."
    },
    {
        "sku": "BOOK-002",
        "name": "The Psychology of Money by Morgan Housel",
        "category": "Books",
        "brand": "Harriman House",
        "price": 380,
        "original_price": 499,
        "rating": 4.8,
        "stock": 75,
        "image": "https://images.unsplash.com/photo-1592496431122-2349e0fbc666?w=600&auto=format&fit=crop&q=80",
        "description": "Timeless lessons on wealth, greed, and happiness doing well with money through human behavior."
    },
    {
        "sku": "BOOK-003",
        "name": "Deep Work by Cal Newport",
        "category": "Books",
        "brand": "Grand Central Publishing",
        "price": 450,
        "original_price": 599,
        "rating": 4.7,
        "stock": 50,
        "image": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop&q=80",
        "description": "Rules for focused success in a distracted world. Master difficult information and produce better results."
    },
    {
        "sku": "BOOK-004",
        "name": "Sapiens: A Brief History of Humankind by Yuval Noah Harari",
        "category": "Books",
        "brand": "Harper",
        "price": 540,
        "original_price": 699,
        "rating": 4.8,
        "stock": 65,
        "image": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=600&auto=format&fit=crop&q=80",
        "description": "Explore how biology and history have defined us and enhanced our understanding of what it means to be human."
    },

    # Sports
    {
        "sku": "SPRT-001",
        "name": "Spalding NBA Zi/O Excel Indoor/Outdoor Basketball",
        "category": "Sports",
        "brand": "Spalding",
        "price": 2499,
        "original_price": 3499,
        "rating": 4.6,
        "stock": 30,
        "image": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=600&auto=format&fit=crop&q=80",
        "description": "Composite leather cover with foam-backed design for tacky grip and tournament-grade feel."
    },
    {
        "sku": "SPRT-002",
        "name": "Yonex Astrox 88D Play Carbon Badminton Racket",
        "category": "Sports",
        "brand": "Yonex",
        "price": 3199,
        "original_price": 4500,
        "rating": 4.7,
        "stock": 25,
        "image": "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=600&auto=format&fit=crop&q=80",
        "description": "Rotational generator system for rapid power smashes and quick counter-attacks."
    },
    {
        "sku": "SPRT-003",
        "name": "Manduka PRO Yoga Mat 6mm Non-Slip High Density",
        "category": "Sports",
        "brand": "Manduka",
        "price": 6999,
        "original_price": 8999,
        "rating": 4.9,
        "stock": 18,
        "image": "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=600&auto=format&fit=crop&q=80",
        "description": "Ultra-dense cushioning provides joint protection, unmatched comfort and proprietary dotted bottom."
    },
    {
        "sku": "SPRT-004",
        "name": "Bowflex SelectTech 552 Adjustable Dumbbells Pair",
        "category": "Sports",
        "brand": "Bowflex",
        "price": 31990,
        "original_price": 41990,
        "rating": 4.8,
        "stock": 10,
        "image": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=600&auto=format&fit=crop&q=80",
        "description": "Replaces 15 sets of weights in one compact footprint. Adjusts from 2 to 24 kg with smooth turn dial."
    },

    # Accessories
    {
        "sku": "ACC-001",
        "name": "Bellroy Classic Premium Leather Backpack 20L",
        "category": "Accessories",
        "brand": "Bellroy",
        "price": 10900,
        "original_price": 13900,
        "rating": 4.8,
        "stock": 22,
        "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80",
        "description": "Clean lines and certified eco-tanned leather with dedicated 16-inch laptop pocket and lumbar support."
    },
    {
        "sku": "ACC-002",
        "name": "Fossil Minimalist Stainless Steel Chronograph Watch",
        "category": "Accessories",
        "brand": "Fossil",
        "price": 7495,
        "original_price": 10995,
        "rating": 4.5,
        "stock": 35,
        "image": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&auto=format&fit=crop&q=80",
        "description": "Slim 44mm case with navy sunray dial, brown leather strap, and 50m water resistance."
    },
    {
        "sku": "ACC-003",
        "name": "Anker 737 Power Bank (PowerCore 24K 140W)",
        "category": "Accessories",
        "brand": "Anker",
        "price": 11999,
        "original_price": 14999,
        "rating": 4.9,
        "stock": 28,
        "image": "https://images.unsplash.com/photo-1609592424109-dd9892f1b177?w=600&auto=format&fit=crop&q=80",
        "description": "Ultra-powerful two-way fast charging with smart digital display and massive 24,000mAh capacity."
    },
    {
        "sku": "ACC-004",
        "name": "Peak Design Everyday Sling 6L V2 Ash",
        "category": "Accessories",
        "brand": "Peak Design",
        "price": 9999,
        "original_price": 12500,
        "rating": 4.7,
        "stock": 19,
        "image": "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=600&auto=format&fit=crop&q=80",
        "description": "Weatherproof 400D recycled nylon canvas with FlexFold dividers for mirrorless gear and everyday essentials."
    }
]


def seed_database():
    print(f"Connecting to MongoDB: {MONGODB_DATABASE}...")
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[MONGODB_DATABASE]
        print("Connected successfully!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return False

    operations = []
    now = datetime.utcnow()

    for item in DEMO_PRODUCTS:
        product_doc = {
            "sku": item["sku"],
            "name": item["name"],
            "category": item["category"],
            "brand": item["brand"],
            "price": item["price"],
            "original_price": item["original_price"],
            "rating": item["rating"],
            "stock": item["stock"],
            "image": item["image"],
            "description": item["description"],
            "updated_at": now,
        }
        operations.append(
            UpdateOne(
                {"sku": item["sku"]},
                {
                    "$set": product_doc,
                    "$setOnInsert": {"created_at": now}
                },
                upsert=True
            )
        )

    if operations:
        result = db.products.bulk_write(operations)
        print(f"Seed complete!")
        print(f"Matched: {result.matched_count}")
        print(f"Upserted: {len(result.upserted_ids)}")
        print(f"Modified: {result.modified_count}")
        total = db.products.count_documents({})
        print(f"Total products in collection: {total}")
        return True
    return False


if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1)
