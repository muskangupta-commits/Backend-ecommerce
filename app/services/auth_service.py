import random
import re
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from app.database.connection import get_db
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_otp_store: dict = {}
OTP_EXPIRY_MINUTES = 10


def _serialize_user(user: dict) -> dict:
    if not user:
        return None
    user = dict(user)
    user["id"] = str(user.pop("_id"))
    user.setdefault("phone", None)
    user.setdefault("email", None)
    user["saved_address"] = user.get("saved_address")
    return user


def generate_otp(identifier: str) -> str:
    if settings.DEMO_OTP_ENABLED and settings.ENVIRONMENT == "development":
        otp = settings.DEMO_OTP
    else:
        otp = str(random.randint(100000, 999999))

    _otp_store[identifier] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    }
    logger.info(f"OTP generated for {identifier}: {otp}")
    return otp


def verify_otp(identifier: str, otp: str) -> bool:
    record = _otp_store.get(identifier)
    if not record:
        return False
    if datetime.utcnow() > record["expires_at"]:
        del _otp_store[identifier]
        return False
    if record["otp"] != otp:
        return False
    del _otp_store[identifier]
    return True


def get_or_create_user(identifier: str) -> dict:
    db = get_db()
    is_phone = re.match(r"^\d{10}$", identifier)

    if is_phone:
        user = db.users.find_one({"phone": identifier})
        if not user:
            new_user = {
                "name": f"User {identifier[-4:]}",
                "phone": identifier,
                "role": "customer",
                "created_at": datetime.utcnow(),
            }
            result = db.users.insert_one(new_user)
            user = db.users.find_one({"_id": result.inserted_id})
    else:
        user = db.users.find_one({"email": identifier})
        if not user:
            new_user = {
                "name": identifier.split("@")[0].replace(".", " ").title(),
                "email": identifier,
                "role": "customer",
                "created_at": datetime.utcnow(),
            }
            result = db.users.insert_one(new_user)
            user = db.users.find_one({"_id": result.inserted_id})

    return _serialize_user(user)


def check_user_exists(identifier: str) -> bool:
    """Check if a user already exists by phone or email."""
    db = get_db()
    is_phone = re.match(r"^\d{10}$", identifier)
    if is_phone:
        user = db.users.find_one({"phone": identifier})
    else:
        user = db.users.find_one({"email": identifier})
    return user is not None


def get_user_by_id(user_id: str) -> Optional[dict]:
    try:
        db = get_db()
        user = db.users.find_one({"_id": ObjectId(user_id)})
        return _serialize_user(user)
    except Exception:
        return None


def update_user_profile(user_id: str, update_data: dict) -> Optional[dict]:
    """Update user profile fields (name, email, saved_address, etc.)."""
    db = get_db()
    allowed_fields = {"name", "email", "saved_address"}
    update_fields = {k: v for k, v in update_data.items() if k in allowed_fields and v is not None}

    if not update_fields:
        return get_user_by_id(user_id)

    update_fields["updated_at"] = datetime.utcnow()

    try:
        user_filter = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"_id": user_id}
        db.users.update_one(user_filter, {"$set": update_fields})
        return get_user_by_id(user_id)
    except Exception as e:
        logger.warning(f"Could not update user profile: {e}")
        return get_user_by_id(user_id)


def ensure_admin_exists():
    db = get_db()
    admin = db.users.find_one({"role": "admin"})
    if not admin:
        db.users.insert_one({
            "name": "Admin",
            "email": "admin@cartify.com",
            "phone": "0000000000",
            "role": "admin",
            "created_at": datetime.utcnow(),
        })
        logger.info("Admin account initialized: admin@cartify.com")
