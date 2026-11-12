import json
import os
import time
from datetime import timedelta
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate an authenticated AES-256-GCM token valid for 7 days by default.
    """
    to_encode = data.copy()
    if expires_delta:
        expire_seconds = int(expires_delta.total_seconds())
    else:
        expire_days = getattr(settings, "TOKEN_EXPIRE_DAYS", 7)
        expire_seconds = expire_days * 86400

    exp_timestamp = int(time.time()) + expire_seconds
    to_encode["exp"] = exp_timestamp

    raw_bytes = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")

    nonce = os.urandom(12)
    key = bytes.fromhex(settings.TOKEN_ENCRYPTION_KEY)
    ciphertext = AESGCM(key).encrypt(nonce, raw_bytes, None)
    return (nonce + ciphertext).hex()


def decode_access_token(token: str) -> dict:
    """
    Decode and validate an authenticated AES-256-GCM token.
    """
    try:
        token_bytes = bytes.fromhex(token)
        if len(token_bytes) < 12 + 16:
            raise ValueError("Token is too short.")
        nonce, ciphertext = token_bytes[:12], token_bytes[12:]
        key = bytes.fromhex(settings.TOKEN_ENCRYPTION_KEY)
        raw_bytes = AESGCM(key).decrypt(nonce, ciphertext, None)
        payload = json.loads(raw_bytes.decode("utf-8"))

        exp = payload.get("exp")
        if exp is None or time.time() > float(exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
