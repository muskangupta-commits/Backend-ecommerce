from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime
import re


class SendOTPRequest(BaseModel):
    identifier: str

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v):
        v = v.strip()
        if re.match(r"^\d{10}$", v):
            return v
        if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v):
            return v
        raise ValueError("Please enter a valid email address or 10-digit phone number.")


class VerifyOTPRequest(BaseModel):
    identifier: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    price: float
    original_price: Optional[float] = None
    image: str
    stock: int = 0
    rating: Optional[float] = None
    brand: Optional[str] = None

    @field_validator("price", "original_price", mode="before")
    @classmethod
    def price_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price must be positive.")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    image: Optional[str] = None
    stock: Optional[int] = None
    rating: Optional[float] = None
    brand: Optional[str] = None


class CartItemRequest(BaseModel):
    product_id: str
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1.")
        return v


class ShippingAddress(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    postal_code: str


class OrderCreate(BaseModel):
    items: List[CartItemRequest]
    shipping_address: ShippingAddress
    payment_method: str = "COD"
    payment_id: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid = ["Order Placed", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"]
        if v not in valid:
            raise ValueError(f"Status must be one of: {', '.join(valid)}")
        return v
