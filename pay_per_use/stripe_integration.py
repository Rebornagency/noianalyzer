import os
import stripe
from typing import Dict, Any, Optional
from .models import JobStatus, CreditPackage
from .database import db_service
from uuid import uuid4

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Legacy product/price configuration for backward compatibility
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


def create_checkout_session(email: str, job_id: str) -> str:
    """Create a Stripe Checkout Session and return the URL for redirect (LEGACY - for direct payment)."""
    if not STRIPE_PRICE_ID:
        raise RuntimeError("Missing STRIPE_PRICE_ID environment variable for legacy payment.")
    
    metadata = {"job_id": job_id, "email": email, "type": "legacy_payment"}
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


def create_credit_checkout_session(email: str, package_id: str) -> str:
    """Create a Stripe Checkout Session for credit purchase."""
    package = db_service.get_package_by_id(package_id)
    if not package:
        raise ValueError(f"Credit package {package_id} not found")
    
    # Get or create user to get user_id for metadata
    user = db_service.get_or_create_user(email)
    
    metadata = {
        "type": "credit_purchase",
        "user_id": user.user_id,
        "package_id": package_id,
        "email": email
    }
    
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=email,
        line_items=[{"price": package.stripe_price_id, "quantity": 1}],
        success_url=os.getenv("CREDIT_SUCCESS_URL", "https://example.com/credit-success?session_id={CHECKOUT_SESSION_ID}"),
        cancel_url=os.getenv("CREDIT_CANCEL_URL", "https://example.com/pricing"),
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