import re
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Cartify E-Commerce API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"

    # MongoDB
    MONGODB_URI: str
    MONGODB_DATABASE: str = "ecommerce_db"

    # Token Encryption (AES-256-GCM)
    TOKEN_ENCRYPTION_KEY: str
    TOKEN_EXPIRE_DAYS: int = 7

    # OTP Configuration
    DEMO_OTP: str = "123456"
    DEMO_OTP_ENABLED: bool = True

    # Optional
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    # Payment (Stripe SDK)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""

    @field_validator("TOKEN_ENCRYPTION_KEY")
    @classmethod
    def validate_token_encryption_key(cls, value: str) -> str:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", value):
            raise ValueError("TOKEN_ENCRYPTION_KEY must be 64 hexadecimal characters.")
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
