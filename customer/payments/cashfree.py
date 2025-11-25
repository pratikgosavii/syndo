import requests
import os
import json
import hmac
import hashlib
import base64
from django.conf import settings
from customer.models import Order

# Cashfree API configuration (no hardcoded secrets; use environment variables)
CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY")
CASHFREE_BASE_URL = os.getenv("CASHFREE_BASE_URL", "https://sandbox.cashfree.com/pg")
CASHFREE_WEBHOOK_SECRET = os.getenv("CASHFREE_WEBHOOK_SECRET")


def _cashfree_headers():
    return {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2022-09-01",
        "Content-Type": "application/json",
    }


def create_order_for(order: Order, customer_id=None, customer_email=None, customer_phone=None, return_url=None, notify_url=None):
    """
    Creates a Cashfree order for a given Order instance and stores payment_session_id.
    Idempotent per order_id: if already created, returns existing session.
    """
    if order.cashfree_session_id and order.cashfree_status in (None, "", "CREATED"):
        return {
            "order_id": order.cashfree_order_id or order.order_id,
            "payment_session_id": order.cashfree_session_id,
            "status": order.cashfree_status or "CREATED",
            "payment_link": order.payment_link,
        }

    payload = {
        "order_id": order.order_id,
        "order_amount": float(order.total_amount or 0),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(customer_id or (order.user_id or "guest")),
            "customer_email": customer_email or getattr(order.user, "email", "") or "noemail@example.com",
            "customer_phone": customer_phone or "",
        },
        "order_meta": {},
    }
    if return_url:
        payload["order_meta"]["return_url"] = return_url
    if notify_url:
        payload["order_meta"]["notify_url"] = notify_url

    url = f"{CASHFREE_BASE_URL}/orders"
    resp = requests.post(url, headers=_cashfree_headers(), json=payload, timeout=15)
    try:
        data = resp.json()
    except Exception:
        data = {"status": "ERROR", "message": resp.text}

    if resp.status_code in (200, 201) and data.get("payment_session_id"):
        order.cashfree_order_id = data.get("order_id", order.order_id)
        order.cashfree_session_id = data.get("payment_session_id")
        order.cashfree_status = "CREATED"
        order.payment_link = data.get("payment_link")
        order.save(update_fields=["cashfree_order_id", "cashfree_session_id", "cashfree_status", "payment_link"])
        return {
            "order_id": order.cashfree_order_id,
            "payment_session_id": order.cashfree_session_id,
            "status": order.cashfree_status,
            "payment_link": order.payment_link,
        }

    order.cashfree_status = f"ERROR:{resp.status_code}"
    order.save(update_fields=["cashfree_status"])
    return {"status": "ERROR", "code": resp.status_code, "data": data}


def refresh_order_status(order: Order):
    """
    Fetch order status from Cashfree and update local fields.
    """
    order_id = order.cashfree_order_id or order.order_id
    if not order_id:
        return {"status": "ERROR", "message": "Missing order_id"}

    url = f"{CASHFREE_BASE_URL}/orders/{order_id}"
    resp = requests.get(url, headers=_cashfree_headers(), timeout=15)
    try:
        data = resp.json()
    except Exception:
        data = {"status": "ERROR", "message": resp.text}

    cf_status = data.get("order_status") or data.get("status")
    if cf_status:
        order.cashfree_status = cf_status
        order.save(update_fields=["cashfree_status"])
    return data


def verify_webhook_signature(raw_body, signature):
    """
    Verifies Cashfree webhook signature.
    """
    secret = CASHFREE_WEBHOOK_SECRET
    computed = base64.b64encode(hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(signature, computed)

