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
                # Cashfree Easy Split REQUIRES vendor_id - vendors must be pre-registered in Cashfree
                # Check if vendor has a Cashfree vendor_id stored
                cashfree_vendor_id = None
                
                # Try to get Cashfree vendor_id from vendor_bank (if field exists)
                if hasattr(vendor_bank_account, 'cashfree_vendor_id'):
                    cashfree_vendor_id = getattr(vendor_bank_account, 'cashfree_vendor_id', None)
                
                # If not in vendor_bank, try to get from vendor_store
                if not cashfree_vendor_id:
                    try:
                        from vendor.models import vendor_store
                        store = vendor_store.objects.filter(user=vendor_user).first()
                        if store and hasattr(store, 'cashfree_vendor_id'):
                            cashfree_vendor_id = getattr(store, 'cashfree_vendor_id', None)
                    except Exception:
                        pass
                
                # If no Cashfree vendor_id found, we cannot create split
                # Cashfree requires vendor_id for Easy Split
                if not cashfree_vendor_id:
                    logger.warning(
                        f"Vendor {vendor_user.id} ({vendor_user.username or vendor_user.mobile}) "
                        f"has no Cashfree vendor_id registered. Skipping split. "
                        f"Vendor must be registered in Cashfree first using Create Vendor API."
                    )
                    continue
                
                split_amount = float(vendor_amount)
                split_config = {
                    "vendor_id": str(cashfree_vendor_id),  # Required by Cashfree
                    "amount": split_amount,
                    "account_number": vendor_bank_account.account_number,
                    "ifsc": vendor_bank_account.ifsc_code,
                    "account_holder": vendor_bank_account.account_holder or vendor_bank_account.name,
                }
                
                splits.append(split_config)
                
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


def create_order_for(order: Order, customer_id=None, customer_email=None, customer_phone=None, return_url=None, notify_url=None, enable_easy_split=False):
    """
    Creates a Cashfree order for a given Order instance and stores payment_session_id.
    Normal payment: user (customer) pays to owner (platform/aggregator); vendor is credited
    via internal ledger (OnlineOrderLedger) when order is paid. No vendor-to-vendor split.
    
    Args:
        order: Order instance
        customer_id: Optional customer ID
        customer_email: Optional customer email
        customer_phone: Optional customer phone
        return_url: Optional return URL
        notify_url: Optional notify URL
        enable_easy_split: If True, add vendor splits (default: False — normal user→owner payment)
    
    Idempotent per order_id: if already created, returns existing session.
    """
    if order.cashfree_session_id and order.cashfree_status in (None, "", "CREATED"):
        # Always return Cashfree-safe order_id (frontend must use this for SDK, not order.order_id)
        cf_order_id = order.cashfree_order_id or _sanitize_order_id_for_cashfree(order.order_id)
        session_id = order.cashfree_session_id
        return {
            "order_id": cf_order_id,
            "cashfree_order_id": cf_order_id,
            "payment_session_id": session_id,
            "order_token": session_id,  # Cashfree SDK expects this as the token for checkout
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
    
    # Clean phone number: remove spaces, dashes, and ensure it starts with country code
    if fallback_phone:
        fallback_phone = str(fallback_phone).strip().replace(" ", "").replace("-", "").replace("+", "")
        # If phone doesn't start with country code (91 for India), add it
        if not fallback_phone.startswith("91") and len(fallback_phone) == 10:
            fallback_phone = "91" + fallback_phone
        elif len(fallback_phone) < 10:
            logger.warning(f"Invalid phone number format: {fallback_phone}, using empty string")
            fallback_phone = ""

    # Sanitize order_id for Cashfree (remove/replace invalid characters like forward slashes)
    cashfree_order_id = _sanitize_order_id_for_cashfree(order.order_id)
    logger.info(f"Cashfree order_id sanitized: '{order.order_id}' -> '{cashfree_order_id}'")
    
    # Validate order amount
    order_amount = float(order.total_amount or 0)
    if order_amount <= 0:
        logger.error(f"Invalid order amount: {order_amount} for order {order.order_id}")
        order.cashfree_status = "ERROR:INVALID_AMOUNT"
        order.save(update_fields=["cashfree_status"])
        return {"status": "ERROR", "code": 400, "message": "Order amount must be greater than 0"}
    
    payload = {
        "order_id": cashfree_order_id,
        "order_amount": order_amount,
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
            # Validate splits before adding
            total_split_amount = sum(float(s.get("amount", 0)) for s in splits)
            
            # Validate each split has required fields (including vendor_id which is required by Cashfree)
            valid_splits = []
            for split in splits:
                # Cashfree requires vendor_id, account_number, and ifsc
                if not split.get("vendor_id"):
                    logger.warning(f"Split missing required vendor_id field, skipping: {split.get('account_number', 'unknown')}")
                    continue
                if not split.get("account_number") or not split.get("ifsc"):
                    logger.warning(f"Split missing required fields (account_number or ifsc), skipping: {split}")
                    continue
                if float(split.get("amount", 0)) <= 0:
                    logger.warning(f"Split amount is 0 or negative, skipping: {split}")
                    continue
                valid_splits.append(split)
            
            if not valid_splits:
                logger.warning(
                    f"No valid splits after validation (vendors may not be registered in Cashfree). "
                    f"Proceeding without Easy Split. Order will still be created successfully."
                )
                splits = None
            elif total_split_amount > order_amount:
                logger.warning(
                    f"Split total ({total_split_amount}) exceeds order amount ({order_amount}). "
                    f"Disabling Easy Split for this order."
                )
                splits = None
            else:
                # Ensure split amounts are properly formatted (round to 2 decimal places)
                for split in valid_splits:
                    split["amount"] = round(float(split.get("amount", 0)), 2)
                
                # Recalculate total after rounding
                total_split_amount = sum(float(s.get("amount", 0)) for s in valid_splits)
                
                # If splits don't add up to order amount, adjust the last split
                if total_split_amount < order_amount and len(valid_splits) > 0:
                    difference = order_amount - total_split_amount
                    valid_splits[-1]["amount"] = round(float(valid_splits[-1]["amount"]) + difference, 2)
                    logger.info(f"Adjusted last split by ₹{difference} to match order total")
                
                payload["order_splits"] = valid_splits
                logger.info(f"✅ Added {len(valid_splits)} vendor split(s) to order {cashfree_order_id}")
                logger.info(f"Total split amount: ₹{sum(float(s.get('amount', 0)) for s in valid_splits)}, Order amount: ₹{order_amount}")
        else:
            logger.info(f"No vendor splits calculated for order {cashfree_order_id} (single vendor or no bank accounts)")

    # Log the full payload before sending (mask sensitive data)
    payload_log = json.dumps(payload, indent=2)
    # Mask account numbers in logs
    if "order_splits" in payload:
        for split in payload["order_splits"]:
            if "account_number" in split:
                acc = split["account_number"]
                if len(acc) > 4:
                    split["account_number"] = f"{acc[:2]}***{acc[-2:]}"
    logger.info(f"Cashfree order creation payload: {json.dumps(payload, indent=2)}")

    # Use 2023-08-01 API version for Easy Split support
    url = f"{CASHFREE_BASE_URL}/orders"
    headers = _cashfree_headers(api_version="2023-08-01")
    logger.info(f"Cashfree API URL: {url}")
    logger.info(f"Cashfree Headers: x-api-version={headers.get('x-api-version')}, x-client-id={_mask(headers.get('x-client-id'))}")
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        logger.info(f"Cashfree API Response Status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Cashfree API request exception: {e}", exc_info=True)
        order.cashfree_status = f"ERROR:EXCEPTION"
        order.save(update_fields=["cashfree_status"])
        return {"status": "ERROR", "code": 500, "message": f"Request failed: {str(e)}"}
    
    try:
        data = resp.json()
        logger.info(f"Cashfree API Response: {json.dumps(data, indent=2)}")
    except Exception:
        data = {"status": "ERROR", "message": resp.text}
        logger.exception("Cashfree create order JSON parse error (status=%s): %s", resp.status_code, resp.text)
        logger.error(f"Raw response text: {resp.text}")

    if resp.status_code in (200, 201) and data.get("payment_session_id"):
        # Cashfree returns the order_id we sent (sanitized version)
        order.cashfree_order_id = data.get("order_id", cashfree_order_id)
        order.cashfree_session_id = data.get("payment_session_id")
        order.cashfree_status = "CREATED"
        order.payment_link = data.get("payment_link")
        order.save(update_fields=["cashfree_order_id", "cashfree_session_id", "cashfree_status", "payment_link"])
        logger.info(f"✅ Cashfree order created successfully: {order.cashfree_order_id}")
        cf_id = order.cashfree_order_id
        session_id = order.cashfree_session_id
        return {
            "order_id": cf_id,
            "cashfree_order_id": cf_id,
            "payment_session_id": session_id,
            "order_token": session_id,  # Cashfree SDK expects this as the token for checkout
            "status": order.cashfree_status,
            "payment_link": order.payment_link,
        }

    # Handle specific error codes with detailed messages
    error_message = data.get("message") or data.get("error") or data.get("error_description") or f"HTTP {resp.status_code} Error"
    error_code = data.get("code") or data.get("error_code") or str(resp.status_code)
    
    if resp.status_code == 400:
        logger.error(
            f"❌ Cashfree 400 Bad Request Error for order {cashfree_order_id}: "
            f"Code: {error_code}, Message: {error_message}, "
            f"Full response: {json.dumps(data, ensure_ascii=False)}"
        )
        order.cashfree_status = f"ERROR:400:{error_code}"
    elif resp.status_code == 403:
        # IP whitelisting error - provide clear guidance
        logger.error(
            f"❌ Cashfree 403 Forbidden Error (IP Not Whitelisted) for order {cashfree_order_id}: "
            f"Message: {error_message}, "
            f"Full response: {json.dumps(data, ensure_ascii=False)}"
        )
        logger.error(
            f"⚠️  ACTION REQUIRED: Your server IP address is not whitelisted in Cashfree dashboard. "
            f"Please add your server IP to Cashfree's IP whitelist: "
            f"Dashboard → Settings → IP Whitelist"
        )
        order.cashfree_status = f"ERROR:403:IP_NOT_WHITELISTED"
        # Enhance error message for user
        error_message = f"IP address not whitelisted. Please contact support. ({error_message})"
    elif resp.status_code == 401:
        logger.error(
            f"❌ Cashfree 401 Unauthorized Error for order {cashfree_order_id}: "
            f"Message: {error_message}, "
            f"Full response: {json.dumps(data, ensure_ascii=False)}"
        )
        logger.error(
            f"⚠️  ACTION REQUIRED: Check your CASHFREE_APP_ID and CASHFREE_SECRET_KEY in environment variables."
        )
        order.cashfree_status = f"ERROR:401:UNAUTHORIZED"
        error_message = f"Authentication failed. Please check API credentials. ({error_message})"
    else:
        order.cashfree_status = f"ERROR:{resp.status_code}"
        logger.error(
            f"❌ Cashfree create order failed: status={resp.status_code}, "
            f"response={json.dumps(data, ensure_ascii=False)}"
        )
    
    order.save(update_fields=["cashfree_status"])
    
    return {
        "status": "ERROR", 
        "code": resp.status_code, 
        "data": data, 
        "message": error_message
    }


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


def create_refund(order: Order, refund_amount, refund_id=None, refund_note=None):
    """
    Refund the user via Cashfree to original payment mode (same as they paid).
    Call when return/exchange is completed for an online-paid order.

    Args:
        order: Order instance (must have cashfree_order_id and be paid via Cashfree)
        refund_amount: Amount to refund in INR (float or Decimal)
        refund_id: Idempotency key (e.g. ret_req_<ReturnExchange.id>). If not set, one is generated.
        refund_note: Optional note for the refund.

    Returns:
        dict: {"status": "OK", "cf_refund_id": "...", "refund_status": "SUCCESS"} on success,
              or {"status": "ERROR", "message": "...", "code": ...} on failure.
    """
    import uuid
    if not order.cashfree_order_id:
        logger.warning(f"[Cashfree Refund] Order {order.order_id} has no cashfree_order_id, skipping refund")
        return {"status": "ERROR", "message": "Order was not paid via Cashfree", "code": 400}

    payment_mode = (getattr(order, "payment_mode", "") or "").strip().lower()
    if payment_mode not in ("cashfree", "online", "upi", "card", "netbanking"):
        logger.info(f"[Cashfree Refund] Order {order.order_id} payment_mode={payment_mode}, not Cashfree; skipping refund")
        return {"status": "ERROR", "message": "Order was not paid via Cashfree", "code": 400}

    try:
        amount_float = float(refund_amount)
    except (TypeError, ValueError):
        logger.error(f"[Cashfree Refund] Invalid refund_amount: {refund_amount}")
        return {"status": "ERROR", "message": "Invalid refund amount", "code": 400}

    if amount_float <= 0:
        logger.warning(f"[Cashfree Refund] Refund amount must be positive, got {amount_float}")
        return {"status": "ERROR", "message": "Refund amount must be positive", "code": 400}

    order_id_cf = order.cashfree_order_id or _sanitize_order_id_for_cashfree(order.order_id)
    if not refund_id:
        refund_id = f"ret_{order_id_cf}_{uuid.uuid4().hex[:12]}"

    # Cashfree accepts alphanumeric, hyphens, underscores for refund_id
    refund_id = re.sub(r"[^a-zA-Z0-9_-]", "", str(refund_id))[:64] or f"ret_{uuid.uuid4().hex[:12]}"

    payload = {
        "refund_id": refund_id,
        "refund_amount": round(amount_float, 2),
        "refund_note": (refund_note or "Return completed")[:500],
    }

    url = f"{CASHFREE_BASE_URL}/orders/{order_id_cf}/refunds"
    headers = _cashfree_headers(api_version="2023-08-01")
    logger.info(f"[Cashfree Refund] POST {url} refund_id={refund_id} amount={amount_float} order={order.order_id}")

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
    except Exception as e:
        logger.error(f"[Cashfree Refund] Request failed: {e}", exc_info=True)
        return {"status": "ERROR", "message": str(e), "code": 500}

    try:
        data = resp.json()
    except Exception:
        data = {"message": resp.text}

    if resp.status_code in (200, 201):
        cf_refund_id = data.get("cf_refund_id") or data.get("refund_id")
        refund_status = data.get("refund_status") or data.get("status")
        logger.info(f"[Cashfree Refund] Success: cf_refund_id={cf_refund_id} refund_status={refund_status}")
        return {
            "status": "OK",
            "cf_refund_id": cf_refund_id,
            "refund_id": refund_id,
            "refund_status": refund_status,
            "refund_amount": amount_float,
        }
    error_message = data.get("message") or data.get("error") or resp.text or f"HTTP {resp.status_code}"
    logger.error(f"[Cashfree Refund] Failed: {resp.status_code} {error_message}")
    return {"status": "ERROR", "message": error_message, "code": resp.status_code, "data": data}


def verify_webhook_signature(raw_body, signature):
    """
    Verifies Cashfree webhook signature.
    """
    secret = CASHFREE_WEBHOOK_SECRET
    computed = base64.b64encode(hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(signature, computed)

