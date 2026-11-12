import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from app.core.config import settings
from app.core.security import get_current_user
import stripe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


class CreatePaymentIntentRequest(BaseModel):
    amount: float = Field(gt=0, allow_inf_nan=False)
    currency: str = "inr"
    order_id: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def only_support_inr(cls, value: str) -> str:
        if value.lower() != "inr":
            raise ValueError("Only INR payments are supported.")
        return "inr"


class VerifyPaymentRequest(BaseModel):
    payment_intent_id: str


@router.get("/config")
async def get_payment_config():
    """Returns Stripe publishable key and active payment capabilities."""
    stripe_enabled = bool(settings.STRIPE_SECRET_KEY)
    return {
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY or None,
        "stripe_enabled": stripe_enabled,
        "supported_methods": ([
            {"id": "Card", "name": "Credit / Debit Card", "provider": "Stripe"},
            {"id": "Online", "name": "UPI / NetBanking / Online", "provider": "Stripe"},
            {"id": "COD", "name": "Cash on Delivery (COD)", "provider": "Offline"},
        ] if stripe_enabled else [
            {"id": "COD", "name": "Cash on Delivery (COD)", "provider": "Offline"},
        ]),
    }


@router.post("/create-intent")
async def create_payment_intent(
    body: CreatePaymentIntentRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Creates a Stripe PaymentIntent for the specified amount using the Stripe SDK.
    Includes test resilience for seamless checkout.
    """
    amount_cents = int(round(body.amount * 100))

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Online payments are not configured.")

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=body.currency,
            automatic_payment_methods={"enabled": True},
            metadata={
                "user_id": current_user.get("sub", ""),
                "customer_phone": current_user.get("phone", ""),
                "order_id": body.order_id or "",
            },
        )
    except stripe.error.StripeError as e:
        logger.warning("Stripe could not create a payment intent: %s", e)
        raise HTTPException(status_code=502, detail="Stripe could not create the payment intent.") from e

    return {
        "success": True,
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "amount": body.amount,
        "currency": body.currency,
        "mode": "stripe",
    }


@router.post("/verify")
async def verify_payment(
    body: VerifyPaymentRequest,
    current_user: dict = Depends(get_current_user),
):
    """Verifies a payment intent status with Stripe."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Online payments are not configured.")

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.retrieve(body.payment_intent_id)
    except stripe.error.StripeError as e:
        logger.warning("Stripe could not verify payment intent: %s", e)
        raise HTTPException(status_code=502, detail="Stripe could not verify the payment.") from e

    if intent.metadata.get("user_id") != current_user.get("sub"):
        raise HTTPException(status_code=404, detail="Payment intent not found.")
    return {
        "verified": intent.status == "succeeded",
        "status": intent.status,
        "payment_intent_id": intent.id,
    }
