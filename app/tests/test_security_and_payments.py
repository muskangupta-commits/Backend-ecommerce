import asyncio
import unittest
from unittest.mock import patch

import mongomock
from fastapi import HTTPException

from app.core import security
from app.models.schemas import OrderCreate
from app.routes import payments
from app.services import order_service


class BackendSecurityAndPaymentTests(unittest.TestCase):
    def test_access_token_authenticates_payload_and_rejects_tampering(self):
        token = security.create_access_token({"sub": "user-1", "role": "customer"})

        self.assertEqual(security.decode_access_token(token)["sub"], "user-1")

        tampered_token = token[:-1] + ("0" if token[-1] != "0" else "1")
        with self.assertRaises(HTTPException) as error:
            security.decode_access_token(tampered_token)
        self.assertEqual(error.exception.status_code, 401)

    def test_payment_endpoints_fail_closed_when_stripe_is_not_configured(self):
        body = payments.CreatePaymentIntentRequest(amount=100)
        credentials = {"sub": "user-1"}
        with patch.object(payments.settings, "STRIPE_SECRET_KEY", ""):
            with self.assertRaises(HTTPException) as create_error:
                asyncio.run(payments.create_payment_intent(body, credentials))
            self.assertEqual(create_error.exception.status_code, 503)

            with self.assertRaises(HTTPException) as verify_error:
                asyncio.run(
                    payments.verify_payment(
                        payments.VerifyPaymentRequest(payment_intent_id="pi_example"),
                        credentials,
                    )
                )
            self.assertEqual(verify_error.exception.status_code, 503)

    def test_cod_order_does_not_trust_client_payment_status(self):
        db = mongomock.MongoClient().ecommerce_db
        product_id = str(
            db.products.insert_one(
                {"name": "Test product", "price": 100, "stock": 2}
            ).inserted_id
        )
        request = OrderCreate.model_validate(
            {
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": {
                    "name": "Test Customer",
                    "email": "customer@example.com",
                    "phone": "1234567890",
                    "address": "1 Test Street",
                    "city": "Test City",
                    "state": "Test State",
                    "postal_code": "12345",
                },
                "payment_method": "COD",
                "payment_status": "Paid",
            }
        )

        with (
            patch.object(order_service, "get_db", return_value=db),
            patch.object(order_service.cart_service, "clear_cart"),
            patch.object(order_service.settings, "STRIPE_SECRET_KEY", ""),
        ):
            order = order_service.place_order(
                user_id="user-1",
                items=[item.model_dump() for item in request.items],
                shipping_address=request.shipping_address.model_dump(),
                payment_method=request.payment_method,
                payment_id=request.payment_id,
            )

        self.assertEqual(order["payment_status"], "Pending")
