import os
import stripe
from typing import Dict, Any
from .models import JobStatus
from uuid import uuid4

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Product/price configuration
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")  # Pre-configured price in Stripe dashboard

if not STRIPE_PRICE_ID:
    raise RuntimeError("Missing STRIPE_PRICE_ID environment variable.")

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


def create_checkout_session(email: str, job_id: str) -> str:
    """Create a Stripe Checkout Session and return the URL for redirect."""
    metadata = {"job_id": job_id, "email": email}
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=email,
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url=os.getenv("CHECKOUT_SUCCESS_URL", "https://example.com/success?job_id={CHECKOUT_SESSION_ID}"),
        cancel_url=os.getenv("CHECKOUT_CANCEL_URL", "https://example.com/cancel"),
        metadata=metadata,
    )
    return session.url


def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify webhook signature and return the event object."""
    if not WEBHOOK_SECRET:
        raise RuntimeError("Missing STRIPE_WEBHOOK_SECRET environment variable.")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
        return event
    except stripe.error.SignatureVerificationError as e:
        raise ValueError(f"Webhook signature verification failed: {e}") 