import requests
import json
import hmac
import hashlib
import base64
import logging
import re
from django.conf import settings
from customer.models import Order

# Cashfree API configuration (centralized via Django settings)
CASHFREE_APP_ID = getattr(settings, "CASHFREE_APP_ID", None)
CASHFREE_SECRET_KEY = getattr(settings, "CASHFREE_SECRET_KEY", None)
CASHFREE_BASE_URL = getattr(settings, "CASHFREE_BASE_URL", "https://sandbox.cashfree.com/pg")
CASHFREE_WEBHOOK_SECRET = getattr(settings, "CASHFREE_WEBHOOK_SECRET", None)


logger = logging.getLogger(__name__)

def _mask(val: str | None) -> str:
    if not val:
        return "None"
    if len(val) <= 8:
        return "***"
    return f"{val[:4]}...{val[-4:]}"

# Log loaded config (masked) once
logger.info(
    "Cashfree config loaded: app_id=%s, secret=%s, base_url=%s",
    _mask(CASHFREE_APP_ID),
    _mask(CASHFREE_SECRET_KEY),
    CASHFREE_BASE_URL,
)
if not CASHFREE_APP_ID or not CASHFREE_SECRET_KEY:
    logger.error("Cashfree credentials missing or empty. Ensure .env is loaded or environment vars are set.")


def _cashfree_headers(api_version="2023-08-01"):
    """
    Get Cashfree API headers.
    Default to 2023-08-01 for Easy Split support.
    """
    return {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": api_version,
        "Content-Type": "application/json",
    }


def _sanitize_order_id_for_cashfree(order_id: str) -> str:
    """
    Sanitize order_id to be Cashfree-compliant.
    Cashfree accepts: alphanumeric, hyphens, underscores
    Rejects: forward slashes, spaces, and other special characters
    """
    if not order_id:
        return order_id
    # Replace forward slashes with hyphens, remove spaces, keep alphanumeric, hyphens, underscores
    sanitized = order_id.replace("/", "-").replace(" ", "-")
    # Remove any other invalid characters (keep only alphanumeric, hyphens, underscores)
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', sanitized)
    return sanitized


def _calculate_vendor_splits(order: Order):
    """
    Calculate vendor splits for Easy Split payment.
    Returns a list of split configurations for each vendor based on their order items.
    
    Returns:
        list: List of split dictionaries with vendor bank details and amounts
        None: If no valid vendor splits can be calculated
    """
    from vendor.models import vendor_bank
    from decimal import Decimal
    
    try:
        # Get all order items with product and vendor info
        order_items = order.items.select_related('product', 'product__user').all()
        
        if not order_items.exists():
            logger.warning(f"No order items found for order {order.order_id}")
            return None
        
        # Group items by vendor and calculate totals
        vendor_amounts = {}
        for item in order_items:
            vendor_user = item.product.user
            if not vendor_user:
                logger.warning(f"Product {item.product.id} has no vendor user, skipping split")
                continue
            
            # Calculate item total (price * quantity)
            item_total = Decimal(str(item.price)) * Decimal(str(item.quantity))
            
            # Add tax if applicable (you may need to adjust this based on your tax calculation)
            # For now, we'll use the order's tax_total proportionally
            # Or you can calculate tax per item if stored separately
            
            if vendor_user.id not in vendor_amounts:
                vendor_amounts[vendor_user.id] = {
                    'vendor_user': vendor_user,
                    'amount': Decimal('0.00'),
                    'items': []
                }
            
            vendor_amounts[vendor_user.id]['amount'] += item_total
            vendor_amounts[vendor_user.id]['items'].append(item)
        
        if not vendor_amounts:
            logger.warning(f"No valid vendors found for order {order.order_id}")
            return None
        
        # Get vendor bank accounts and build splits
        splits = []
        total_split_amount = Decimal('0.00')
        
        for vendor_id, vendor_data in vendor_amounts.items():
            vendor_user = vendor_data['vendor_user']
            vendor_amount = vendor_data['amount']
            
            # Get vendor's bank account marked for online orders
            try:
                vendor_bank_account = vendor_bank.objects.filter(
                    user=vendor_user,
                    online_order_bank=True,
                    is_active=True
                ).first()
                
                if not vendor_bank_account:
                    logger.warning(
                        f"Vendor {vendor_user.id} ({vendor_user.username or vendor_user.mobile}) "
                        f"has no active bank account marked for online orders. Skipping split."
                    )
                    continue
                
                # Validate bank account details
                if not vendor_bank_account.account_number or not vendor_bank_account.ifsc_code:
                    logger.warning(
                        f"Vendor {vendor_user.id} bank account {vendor_bank_account.id} "
                        f"missing account_number or ifsc_code. Skipping split."
                    )
                    continue
                
                # Add split configuration
                split_amount = float(vendor_amount)
                splits.append({
                    "vendor_id": str(vendor_id),
                    "amount": split_amount,
                    "account_number": vendor_bank_account.account_number,
                    "ifsc": vendor_bank_account.ifsc_code,
                    "account_holder": vendor_bank_account.account_holder or vendor_bank_account.name,
                })
                
                total_split_amount += vendor_amount
                
                logger.info(
                    f"Added split for vendor {vendor_id}: ₹{split_amount} "
                    f"(Account: {vendor_bank_account.account_number[-4:]}...)"
                )
                
            except Exception as e:
                logger.error(f"Error processing split for vendor {vendor_id}: {e}", exc_info=True)
                continue
        
        if not splits:
            logger.warning(f"No valid splits created for order {order.order_id}")
            return None
        
        # Verify split amounts don't exceed order total (with small tolerance for rounding)
        order_total = Decimal(str(order.total_amount or 0))
        tolerance = Decimal('0.01')  # Allow 1 paisa difference for rounding
        
        if total_split_amount > order_total + tolerance:
            logger.warning(
                f"Split total ({total_split_amount}) exceeds order total ({order_total}). "
                f"Adjusting splits proportionally."
            )
            # Adjust splits proportionally
            ratio = order_total / total_split_amount
            for split in splits:
                split['amount'] = float(Decimal(str(split['amount'])) * ratio)
            total_split_amount = order_total
        
        logger.info(
            f"Created {len(splits)} split(s) for order {order.order_id}: "
            f"Total split amount: ₹{total_split_amount}, Order total: ₹{order_total}"
        )
        
        return splits
        
    except Exception as e:
        logger.error(f"Error calculating vendor splits for order {order.order_id}: {e}", exc_info=True)
        return None


def create_order_for(order: Order, customer_id=None, customer_email=None, customer_phone=None, return_url=None, notify_url=None, enable_easy_split=True):
    """
    Creates a Cashfree order for a given Order instance and stores payment_session_id.
    Supports Easy Split for multi-vendor orders.
    
    Args:
        order: Order instance
        customer_id: Optional customer ID
        customer_email: Optional customer email
        customer_phone: Optional customer phone
        return_url: Optional return URL
        notify_url: Optional notify URL
        enable_easy_split: If True, automatically calculate and add vendor splits (default: True)
    
    Idempotent per order_id: if already created, returns existing session.
    """
    if order.cashfree_session_id and order.cashfree_status in (None, "", "CREATED"):
        return {
            "order_id": order.cashfree_order_id or order.order_id,
            "payment_session_id": order.cashfree_session_id,
            "status": order.cashfree_status or "CREATED",
            "payment_link": order.payment_link,
        }

    # Ensure phone is present: prefer explicit param, else fallback to user's stored mobile/phone
    fallback_phone = (
        customer_phone
        or getattr(order.user, "mobile", None)
        or getattr(order.user, "mobile_number", None)
        or getattr(order.user, "phone", None)
        or ""
    )

    # Sanitize order_id for Cashfree (remove/replace invalid characters like forward slashes)
    cashfree_order_id = _sanitize_order_id_for_cashfree(order.order_id)
    logger.info(f"Cashfree order_id sanitized: '{order.order_id}' -> '{cashfree_order_id}'")
    
    payload = {
        "order_id": cashfree_order_id,
        "order_amount": float(order.total_amount or 0),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(customer_id or (order.user_id or "guest")),
            "customer_email": customer_email or getattr(order.user, "email", "") or "noemail@example.com",
            "customer_phone": fallback_phone,
        },
        "order_meta": {},
    }
    if return_url:
        payload["order_meta"]["return_url"] = return_url
    if notify_url:
        payload["order_meta"]["notify_url"] = notify_url
    
    # Calculate and add Easy Split configuration if enabled
    if enable_easy_split:
        splits = _calculate_vendor_splits(order)
        if splits:
            payload["order_splits"] = splits
            logger.info(f"Added {len(splits)} vendor split(s) to order {cashfree_order_id}")
        else:
            logger.info(f"No vendor splits calculated for order {cashfree_order_id} (single vendor or no bank accounts)")

    # Use 2023-08-01 API version for Easy Split support
    url = f"{CASHFREE_BASE_URL}/orders"
    resp = requests.post(url, headers=_cashfree_headers(api_version="2023-08-01"), json=payload, timeout=15)
    try:
        data = resp.json()
    except Exception:
        data = {"status": "ERROR", "message": resp.text}
        logger.exception("Cashfree create order JSON parse error (status=%s): %s", resp.status_code, resp.text)

    if resp.status_code in (200, 201) and data.get("payment_session_id"):
        # Cashfree returns the order_id we sent (sanitized version)
        order.cashfree_order_id = data.get("order_id", cashfree_order_id)
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
    # Log the error details for debugging (prints to console if no logging configured)
    logger.error(
        "Cashfree create order failed: status=%s, response=%s",
        resp.status_code,
        json.dumps(data, ensure_ascii=False),
    )
    return {"status": "ERROR", "code": resp.status_code, "data": data}


def refresh_order_status(order: Order):
    """
    Fetch order status from Cashfree and update local fields.
    """
    # Use cashfree_order_id if available (sanitized), otherwise sanitize the original order_id
    order_id = order.cashfree_order_id or _sanitize_order_id_for_cashfree(order.order_id)
    if not order_id:
        return {"status": "ERROR", "message": "Missing order_id"}

    url = f"{CASHFREE_BASE_URL}/orders/{order_id}"
    resp = requests.get(url, headers=_cashfree_headers(api_version="2023-08-01"), timeout=15)
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

