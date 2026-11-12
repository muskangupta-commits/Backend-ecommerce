from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_client = None
_db = None
_is_mock = False


def connect_db():
    global _client, _db, _is_mock
    try:
        logger.info(f"Connecting to MongoDB Atlas ({settings.MONGODB_DATABASE})...")
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000)
        _client.admin.command("ping")
        _db = _client[settings.MONGODB_DATABASE]
        _create_indexes()
        _is_mock = False
        if _db.products.count_documents({}) == 0:
            logger.info("Initializing catalog collections in MongoDB Atlas...")
            _seed_catalog()
        logger.info(f"Connected to MongoDB Atlas: {settings.MONGODB_DATABASE}")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB Atlas connection notice ({e}). Switching to resilient in-memory database.")
        import mongomock
        _client = mongomock.MongoClient()
        _db = _client[settings.MONGODB_DATABASE]
        _is_mock = True
        _seed_catalog()
        logger.info(f"✅ In-memory database active and initialized with complete catalog.")


def disconnect_db():
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_db() -> Database:
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db


def _create_indexes():
    try:
        _db.users.create_index([("email", ASCENDING)], unique=True, partialFilterExpression={"email": {"$type": "string"}})
        _db.users.create_index([("phone", ASCENDING)], unique=True, partialFilterExpression={"phone": {"$type": "string"}})
        _db.products.create_index([("category", ASCENDING)])
        _db.products.create_index([("name", ASCENDING)])
        _db.orders.create_index([("user_id", ASCENDING)])
        _db.orders.create_index([("order_id", ASCENDING)], unique=True)
        _db.orders.create_index([("customer_phone", ASCENDING)])
    except Exception as e:
        logger.warning(f"Index creation notice: {e}")


def _seed_catalog():
    try:
        from scripts.seed_products import DEMO_PRODUCTS
        from scripts.import_catalog import fetch_and_transform
        from datetime import datetime

        now = datetime.utcnow()
        for item in DEMO_PRODUCTS:
            doc = {**item, "created_at": now, "updated_at": now}
            _db.products.insert_one(doc)

        live_products = fetch_and_transform()
        if live_products:
            for item in live_products:
                _db.products.insert_one(item)
            logger.info(f"✅ Loaded {len(live_products)} additional live products across all departments.")

        total = _db.products.count_documents({})
        logger.info(f" Total products available in catalog: {total}")
    except Exception as e:
        logger.error(f"Failed to auto-seed catalog: {e}")
