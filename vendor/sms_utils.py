"""
SMS utility functions for sending SMS via MSGClub API
"""
import http.client
import json
import logging
from decimal import Decimal
from datetime import datetime
from django.conf import settings
import re

logger = logging.getLogger(__name__)


def send_sms_via_msgclub(phone_number, message):
    """
    Send SMS via MSGClub API
    
    Args:
        phone_number: Customer phone number (string)
        message: SMS message content (string)
    
    Returns:
        tuple: (success: bool, response_data: dict or error_message: str)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"{'='*80}")
    logger.info(f"[SMS LOG] [{timestamp}] Starting SMS send process")
    logger.info(f"[SMS LOG] Phone Number: {phone_number}")
    logger.info(f"[SMS LOG] Message: {message[:100]}{'...' if len(message) > 100 else ''}")
    logger.info(f"{'='*80}")
    
    try:
        from django.conf import settings
        
        # Get API credentials from settings
        api_key = getattr(settings, 'SMS_API_KEY', '')
        api_host = getattr(settings, 'SMS_API_URL', 'msg.msgclub.net')
        api_endpoint = getattr(settings, 'SMS_API_ENDPOINT', 'rest/services/sendSMS/sendGroupSms')
        use_https = bool(getattr(settings, 'SMS_USE_HTTPS', True))
        # MSGClub accounts commonly use AUTH_KEY as the parameter name.
        # We keep api_key as default for backward compatibility, but we also auto-retry with AUTH_KEY
        # if the gateway responds with "Token Not Found".
        auth_param = getattr(settings, 'SMS_AUTH_PARAM', 'api_key')
        mobile_param = getattr(settings, 'SMS_MOBILE_PARAM', 'mobile')
        message_param = getattr(settings, 'SMS_MESSAGE_PARAM', 'message')
        sender_id = getattr(settings, 'SMS_SENDER_ID', '') or ''
        sender_param = getattr(settings, 'SMS_SENDER_PARAM', 'senderId')

        # MSGClub / DLT params (names vary; we keep them configurable in settings)
        entity_id = getattr(settings, "SMS_ENTITY_ID", "") or ""
        tmid = getattr(settings, "SMS_TM_ID", "") or ""
        template_id = getattr(settings, "SMS_TEMPLATE_ID_INVOICE", "") or ""
        entity_param = getattr(settings, "SMS_ENTITY_PARAM", "entityid")
        tmid_param = getattr(settings, "SMS_TM_PARAM", "tmid")
        template_param = getattr(settings, "SMS_TEMPLATE_PARAM", "templateid")

        # Route / content type params (as per MSGClub sample)
        route_id = getattr(settings, "SMS_ROUTE_ID", "") or ""
        route_param = getattr(settings, "SMS_ROUTE_PARAM", "routeId")
        sms_content_type = getattr(settings, "SMS_CONTENT_TYPE", "") or ""
        sms_content_type_param = getattr(settings, "SMS_CONTENT_TYPE_PARAM", "smsContentType")

        # Optional consent failover param
        consent_failover_id = getattr(settings, "SMS_CONSENT_FAILOVER_ID", "") or ""
        consent_failover_param = getattr(settings, "SMS_CONSENT_FAILOVER_PARAM", "concentFailoverId")
        
        logger.info(f"[SMS LOG] API Host: {api_host}")
        logger.info(f"[SMS LOG] API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else 'N/A'}")
        logger.info(f"[SMS LOG] Param names: auth={auth_param}, mobile={mobile_param}, message={message_param}")
        
        if not api_key:
            error_msg = "SMS API key not configured"
            logger.error(f"[SMS LOG] ERROR: {error_msg}")
            logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
            return False, error_msg

        conn_cls = http.client.HTTPSConnection if use_https else http.client.HTTPConnection
        conn = conn_cls(api_host)
        
        headers = {
            'Cache-Control': "no-cache"
        }
        
        import urllib.parse
        endpoint = api_endpoint

        def _build_params(auth_key_name: str):
            p = {
                mobile_param: phone_number,
                message_param: message,
                auth_key_name: api_key,
            }
            if sender_id:
                p[sender_param] = sender_id

            # Optional route/content-type params
            if route_id:
                p[route_param] = route_id
            if sms_content_type:
                p[sms_content_type_param] = sms_content_type

            # Optional DLT params (required on some routes/accounts)
            if entity_id:
                p[entity_param] = entity_id
            if tmid:
                p[tmid_param] = tmid
            if template_id:
                p[template_param] = template_id

            # Optional consent failover
            if consent_failover_id:
                p[consent_failover_param] = consent_failover_id
            return p

        params = _build_params(auth_param)

        # Validate sender id if provided/required by provider
        # MSGClub commonly requires exactly 6 alphabets (A-Z).
        
       
        query_string = urllib.parse.urlencode(params)
        full_endpoint = f"{endpoint}?{query_string}"
        
        logger.info(f"[SMS LOG] Endpoint: {endpoint}")
        # Do NOT log full URL with API key in plain text
        safe_query = query_string.replace(str(api_key), "****")
        logger.info(f"[SMS LOG] Full URL: {'https' if use_https else 'http'}://{api_host}/{endpoint}?{safe_query}")
        logger.info(f"[SMS LOG] Sending GET request...")
        
        def _request_once(ep):
            # http.client expects the request path to start with "/". Some servers respond 400 otherwise.
            if ep and not ep.startswith("/"):
                ep = "/" + ep
            conn.request("GET", ep, headers=headers)
            res = conn.getresponse()
            status_code = res.status
            data = res.read()
            response_text = data.decode("utf-8", errors="replace")
            return status_code, dict(res.getheaders()), response_text

        status_code, resp_headers, response_text = _request_once(full_endpoint)

        # Fallback: some MSGClub docs show a comma-separated path. If our primary endpoint fails
        # with an empty body, retry once with comma-separated style.
        if (status_code >= 400) and (not response_text) and ("," not in endpoint):
            fallback_endpoint = endpoint.replace("/", ",")
            fallback_full = f"{fallback_endpoint}?{query_string}"
            logger.warning(f"[SMS LOG] Primary endpoint failed with HTTP {status_code} and empty body; retrying fallback endpoint format...")
            status_code, resp_headers, response_text = _request_once(fallback_full)
        
        logger.info(f"[SMS LOG] Response Status Code: {status_code}")
        logger.info(f"[SMS LOG] Response Headers: {resp_headers}")
        logger.info(f"[SMS LOG] Response Body: {response_text}")
        
        conn.close()
        
        # Treat non-2xx as failure (MSGClub sometimes returns 400 with empty body)
        if status_code < 200 or status_code >= 300:
            error_msg = f"HTTP {status_code} from SMS API: {response_text or 'Empty response'}"
            logger.error(f"[SMS LOG] ERROR: {error_msg}")
            logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
            return False, error_msg

        # Many gateways (including MSGClub) may return HTTP 200 even for application-level errors.
        # So we must inspect the response body.
        if response_text:
            try:
                response_data = json.loads(response_text)

                # Common MSGClub error: token not found (usually wrong auth param name or invalid key)
                resp_code = str(response_data.get("responseCode", "")).strip()
                resp_msg = str(response_data.get("response", "")).strip()
                if resp_code == "3009" or resp_msg.lower() == "token not found":
                    logger.warning(f"[SMS LOG] Gateway responded Token Not Found (responseCode=3009). Retrying with AUTH_KEY param name...")
                    # Retry once with AUTH_KEY
                    retry_params = _build_params("AUTH_KEY")
                    retry_qs = urllib.parse.urlencode(retry_params)
                    retry_full = f"{endpoint}?{retry_qs}"
                    status_code2, resp_headers2, response_text2 = _request_once(retry_full)
                    logger.info(f"[SMS LOG] Retry Response Status Code: {status_code2}")
                    logger.info(f"[SMS LOG] Retry Response Headers: {resp_headers2}")
                    logger.info(f"[SMS LOG] Retry Response Body: {response_text2}")

                    if status_code2 < 200 or status_code2 >= 300:
                        error_msg = f"HTTP {status_code2} from SMS API (retry): {response_text2 or 'Empty response'}"
                        logger.error(f"[SMS LOG] ERROR: {error_msg}")
                        logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
                        return False, error_msg

                    if not response_text2:
                        error_msg = "Empty response from SMS API (retry)"
                        logger.error(f"[SMS LOG] ERROR: {error_msg}")
                        logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
                        return False, error_msg

                    try:
                        response_data2 = json.loads(response_text2)
                        resp_code2 = str(response_data2.get("responseCode", "")).strip()
                        resp_msg2 = str(response_data2.get("response", "")).strip()
                        accepted_codes = {"0", "200", "3001"}
                        if resp_code2 and resp_code2 not in accepted_codes:
                            error_msg = f"Gateway error (retry): {resp_msg2 or response_text2}"
                            logger.error(f"[SMS LOG] ERROR: {error_msg}")
                            logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
                            return False, error_msg
                        logger.info(f"[SMS LOG] SUCCESS: SMS accepted by gateway for {phone_number} (retry, responseCode={resp_code2})")
                        return True, response_data2
                    except json.JSONDecodeError:
                        # Non-JSON but 2xx; treat as accepted unless it looks like an error
                        if "error" in response_text2.lower() or "invalid" in response_text2.lower():
                            error_msg = f"Gateway error (retry): {response_text2}"
                            logger.error(f"[SMS LOG] ERROR: {error_msg}")
                            logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
                            return False, error_msg
                        logger.info(f"[SMS LOG] SUCCESS: SMS accepted by gateway for {phone_number} (non-JSON retry)")
                        return True, response_text2

                accepted_codes = {"0", "200", "3001"}

                # If responseCode exists and is a non-accepted code, treat as failure.
                if resp_code and resp_code not in accepted_codes:
                    error_msg = f"Gateway error: {resp_msg or response_text}"
                    logger.error(f"[SMS LOG] ERROR: {error_msg}")
                    logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
                    return False, error_msg

                logger.info(f"[SMS LOG] SUCCESS: SMS accepted by gateway for {phone_number} (responseCode={resp_code})")
                logger.info(f"[SMS LOG] Response Data: {json.dumps(response_data, indent=2)}")
                logger.info(f"{'='*80}")
                logger.info(f"SMS accepted by gateway for {phone_number}. Response: {response_data}")
                return True, response_data
            except json.JSONDecodeError:
                # If response is not JSON, treat as success only if it doesn't look like an error
                if "error" in response_text.lower() or "invalid" in response_text.lower() or "token" in response_text.lower():
                    error_msg = f"Gateway error: {response_text}"
                    logger.error(f"[SMS LOG] ERROR: {error_msg}")
                    logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
                    return False, error_msg
                logger.info(f"[SMS LOG] SUCCESS: SMS accepted by gateway for {phone_number}")
                logger.info(f"[SMS LOG] Response (non-JSON): {response_text}")
                logger.info(f"{'='*80}")
                logger.info(f"SMS accepted by gateway for {phone_number}. Response: {response_text}")
                return True, response_text
        else:
            error_msg = "Empty response from SMS API"
            logger.error(f"[SMS LOG] ERROR: {error_msg}")
            logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        error_str = str(e)
        logger.error(f"[SMS LOG] EXCEPTION: Error sending SMS to {phone_number}")
        logger.error(f"[SMS LOG] Exception Type: {type(e).__name__}")
        logger.error(f"[SMS LOG] Exception Message: {error_str}")
        logger.error(f"{'='*80}")
        logger.error(f"Error sending SMS to {phone_number}: {error_str}")
        return False, error_str


def send_sale_sms(sale, invoice_type='invoice'):
    """
    Send SMS for a sale based on invoice type and SMS settings
    
    Args:
        sale: Sale instance
        invoice_type: Type of invoice ('invoice' or other types like 'quotation', 'sales_order', etc.)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # Ensure logger is properly initialized
    if not logger.handlers:
        # If no handlers, add a console handler as fallback
        import logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"{'#'*80}")
    logger.info(f"[SMS SALE LOG] [{timestamp}] Processing SMS for Sale #{sale.id}")
    logger.info(f"[SMS SALE LOG] Invoice Type: {invoice_type}")
    logger.info(f"{'#'*80}")
    
    from .models import SMSSetting, vendor_customers
    
    # Check if sale has customer
    if not sale.customer:
        logger.warning(f"[SMS SALE LOG] SKIPPED: No customer associated with sale {sale.id}")
        logger.warning(f"SMS not sent for sale {sale.id}: No customer associated with sale")
        return False, "No customer associated with sale"
    
    # Check if user has SMS settings
    if not sale.user:
        logger.warning(f"[SMS SALE LOG] SKIPPED: No user associated with sale {sale.id}")
        logger.warning(f"SMS not sent for sale {sale.id}: No user associated with sale")
        return False, "No user associated with sale"
    
    logger.info(f"[SMS SALE LOG] Sale ID: {sale.id}")
    logger.info(f"[SMS SALE LOG] User: {sale.user.username} (ID: {sale.user.id})")
    logger.info(f"[SMS SALE LOG] Customer: {sale.customer.name} (ID: {sale.customer.id})")
    
    try:
        sms_setting, created = SMSSetting.objects.get_or_create(
            user=sale.user,
            defaults={'available_credits': Decimal('100.00')}
        )
        if created:
            logger.info(f"[SMS SALE LOG] Created new SMS settings for user {sale.user.username} with 100 default credits")
        else:
            logger.info(f"[SMS SALE LOG] Using existing SMS settings for user {sale.user.username}")
        logger.info(f"[SMS SALE LOG] Available Credits: {sms_setting.available_credits}")
        logger.info(f"[SMS SALE LOG] Used Credits: {sms_setting.used_credits}")
        logger.info(f"[SMS SALE LOG] Enable Purchase Message: {sms_setting.enable_purchase_message}")
        logger.info(f"[SMS SALE LOG] Enable Quote Message: {sms_setting.enable_quote_message}")
    except Exception as e:
        error_msg = f"Error getting SMS settings: {str(e)}"
        logger.error(f"[SMS SALE LOG] ERROR: {error_msg}")
        logger.error(f"SMS not sent for sale {sale.id}: {error_msg}")
        return False, error_msg
    
    # Determine which setting to check based on invoice type
    should_send = False
    setting_type = ""
    
    if invoice_type == 'invoice':
        # Check enable_purchase_message for invoice type
        should_send = sms_setting.enable_purchase_message
        setting_type = "purchase message"
    else:
        # Check enable_quote_message for all other types
        should_send = sms_setting.enable_quote_message
        setting_type = "quote message"
    
    logger.info(f"[SMS SALE LOG] Checking {setting_type} setting: {should_send}")
    
    if not should_send:
        logger.info(f"[SMS SALE LOG] SKIPPED: {setting_type.capitalize()} is disabled for sale {sale.id}")
        logger.info(f"SMS not sent for sale {sale.id} (invoice_type: {invoice_type}): {setting_type.capitalize()} is disabled")
        return False, f"{setting_type.capitalize()} is disabled"
    
    # Check if there are available credits before sending SMS
    try:
        available_credits = Decimal(sms_setting.available_credits or 0)
        if available_credits <= 0:
            error_msg = f"Insufficient SMS credits. Available: {available_credits}, Required: 1"
            logger.warning(f"[SMS SALE LOG] SKIPPED: {error_msg}")
            logger.warning(f"SMS not sent for sale {sale.id}: {error_msg}")
            return False, error_msg
        logger.info(f"[SMS SALE LOG] Available Credits: {available_credits} (sufficient for sending)")
    except Exception as e:
        error_msg = f"Error checking SMS credits: {str(e)}"
        logger.error(f"[SMS SALE LOG] ERROR: {error_msg}")
        logger.error(f"SMS not sent for sale {sale.id}: {error_msg}")
        return False, error_msg
    
    # Get customer phone number
    customer = sale.customer
    phone_number = getattr(customer, 'contact', None)
    
    logger.info(f"[SMS SALE LOG] Customer Phone (raw): {phone_number}")
    
    if not phone_number:
        logger.warning(f"[SMS SALE LOG] SKIPPED: Customer phone number not found for customer {customer.id}")
        logger.warning(f"SMS not sent for sale {sale.id}: Customer phone number not found for customer {customer.id}")
        return False, "Customer phone number not found"
    
    # Clean phone number (remove any non-digit characters except +)
    import re
    phone_number_cleaned = re.sub(r'[^\d+]', '', str(phone_number))

    # Normalize for MSGClub (often expects country code). If it's a plain 10-digit Indian number,
    # prepend "91". If it already has +91/91, keep as-is.
    normalized = phone_number_cleaned.strip()
    if normalized.startswith("+"):
        normalized = normalized[1:]
    # drop leading 0 for local formats like 08830...
    normalized = normalized.lstrip("0")
    if len(normalized) == 10 and normalized.isdigit():
        normalized = "91" + normalized

    logger.info(f"[SMS SALE LOG] Customer Phone (cleaned): {phone_number_cleaned}")
    logger.info(f"[SMS SALE LOG] Customer Phone (normalized): {normalized}")
    
    # Prepare SMS message
    invoice_number = sale.invoice_number or f"#{sale.id}"
    total_amount = getattr(sale, "total_amount", None) or getattr(sale, "total_bill_amount", None) or 0

    # Get shop/store name
    from .models import vendor_store
    try:
        store = sale.user.vendor_store.first()
        shop_name = store.name if store else "Svindo"
    except Exception:
        shop_name = "Svindo"

    # Build an invoice link (must match approved DLT template)
    try:
        base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
    except Exception:
        base = ""

    # Our approved template expects URL like:
    # https://vendor.svindo.com/vendor/customer-sale-invoice/?{#var#}
    # We'll fill var with "id=<sale_id>"
    invoice_query = f"id={sale.id}"
    invoice_link = f"{base}/vendor/customer-sale-invoice/?{invoice_query}" if base else ""

    if invoice_type == 'invoice':
        # Match DLT-approved template wording EXACTLY; only replace vars.
        # Template:
        # From Svindo: Your purchase invoice is generated. Thank you for shopping {#var#}.
        # Your purchase amount is Rs. {#var#}. Download your invoice:
        # https://vendor.svindo.com/vendor/customer-sale-invoice/?{#var#} (Valid for 7 days).
        message = (
            f"From Svindo: Your purchase invoice is generated. Thank you for shopping with {shop_name}. "
            f"Your purchase amount is Rs. {total_amount}. "
            f"Download your invoice: {invoice_link} (Valid for 7 days)."
        )
    else:
        invoice_type_display = invoice_type.replace('_', ' ').title()
        message = f"Dear {customer.name}, Your {invoice_type_display} {invoice_number} for Rs {total_amount} has been prepared. Please review."
    
    logger.info(f"[SMS SALE LOG] Invoice Number: {invoice_number}")
    logger.info(f"[SMS SALE LOG] Total Amount: Rs {total_amount}")
    logger.info(f"[SMS SALE LOG] SMS Message: {message}")
    logger.info(f"[SMS SALE LOG] Calling send_sms_via_msgclub()...")
    
    # Send SMS
    logger.info(f"Attempting to send SMS for sale {sale.id} to customer {customer.name} ({normalized}), invoice_type: {invoice_type}")
    success, response = send_sms_via_msgclub(normalized, message)
    
    if success:
        # Update SMS credits (deduct 1 credit for SMS sent)
        try:
            old_credits = sms_setting.available_credits
            sms_setting.available_credits = max(Decimal('0'), sms_setting.available_credits - Decimal('1'))
            sms_setting.used_credits += Decimal('1')
            sms_setting.save(update_fields=['available_credits', 'used_credits'])
            logger.info(f"[SMS SALE LOG] Credits deducted: {old_credits} → {sms_setting.available_credits} (deducted 1)")
            logger.info(f"[SMS SALE LOG] Used Credits: {sms_setting.used_credits}")
        except Exception as e:
            logger.error(f"[SMS SALE LOG] ERROR: Failed to update SMS credits: {str(e)}")
            # Continue even if credit update fails - SMS was already sent
        
        # "success" here means the gateway accepted the SMS request; delivery to handset can still fail/delay.
        details = ""
        try:
            if isinstance(response, dict):
                rc = response.get("responseCode")
                r = response.get("response")
                if r:
                    details = f" (responseCode={rc}, message_id={r})"
                else:
                    details = f" (responseCode={rc})"
            elif response:
                details = f" ({response})"
        except Exception:
            details = ""

        logger.info(f"[SMS SALE LOG] SUCCESS: SMS accepted by gateway for sale {sale.id}{details}")
        logger.info(f"{'#'*80}")
        logger.info(f"SMS accepted by gateway for sale {sale.id} to {phone_number_cleaned}{details}")
        return True, f"SMS accepted by gateway{details}"
    else:
        error_msg = f"Failed to send SMS: {response}"
        logger.error(f"[SMS SALE LOG] FAILED: {error_msg}")
        logger.error(f"{'#'*80}")
        logger.error(f"SMS failed for sale {sale.id} to {phone_number_cleaned}: {error_msg}")
        return False, error_msg


def _normalize_indian_phone_for_gateway(phone_number):
    """
    Normalize phone numbers for MSGClub.
    - Removes non-digits (keeps leading + then strips it)
    - Strips leading 0
    - If 10 digits, prepends 91
    Returns normalized digits-only string or "".
    """
    if not phone_number:
        return ""
    import re
    cleaned = re.sub(r"[^\d+]", "", str(phone_number)).strip()
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    cleaned = cleaned.lstrip("0")
    if len(cleaned) == 10 and cleaned.isdigit():
        cleaned = "91" + cleaned
    return cleaned


def _deduct_sms_credits(sms_setting, credits_to_deduct=1):
    """
    Deduct SMS credits safely. Returns (success: bool, message: str).
    """
    try:
        from decimal import Decimal
        credits_to_deduct = Decimal(str(credits_to_deduct or 0))
        if credits_to_deduct <= 0:
            return True, "No credits to deduct"
        old_credits = Decimal(sms_setting.available_credits or 0)
        if old_credits < credits_to_deduct:
            return False, f"Insufficient SMS credits. Available: {old_credits}, Required: {credits_to_deduct}"
        sms_setting.available_credits = max(Decimal("0"), old_credits - credits_to_deduct)
        sms_setting.used_credits = Decimal(sms_setting.used_credits or 0) + credits_to_deduct
        sms_setting.save(update_fields=["available_credits", "used_credits"])
        return True, f"Credits deducted: {old_credits} → {sms_setting.available_credits} (deducted {credits_to_deduct})"
    except Exception as e:
        return False, f"Failed to update SMS credits: {str(e)}"


def send_purchase_sms(purchase, send_to_user=True, send_to_vendor=True):
    """
    Send SMS for a Purchase to:
    - Purchase.user (store owner/creator) mobile
    - Purchase.vendor (supplier) contact

    Uses SMSSetting of Purchase.user for credit + enablement (enable_purchase_message).
    Deducts 1 credit per SMS actually accepted by gateway.
    """
    from decimal import Decimal
    from datetime import datetime
    from django.conf import settings

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"{'#'*80}")
    logger.info(f"[SMS PURCHASE LOG] [{timestamp}] Processing SMS for Purchase #{getattr(purchase, 'id', None)}")
    logger.info(f"{'#'*80}")

    if not getattr(purchase, "user", None):
        return False, "No user associated with purchase"

    from .models import SMSSetting

    try:
        sms_setting, _ = SMSSetting.objects.get_or_create(
            user=purchase.user,
            defaults={"available_credits": Decimal("100.00")},
        )
    except Exception as e:
        return False, f"Error getting SMS settings: {str(e)}"

    if not sms_setting.enable_purchase_message:
        return False, "Purchase message is disabled"

    # Use same DLT-approved message as POS (invoice template)
    total_amount = getattr(purchase, "total_amount", None) or 0
    vendor_name = getattr(getattr(purchase, "vendor", None), "name", None) or "Vendor"

    try:
        base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
    except Exception:
        base = ""
    purchase_link = f"{base}/vendor/purchase-invoice/?id={purchase.id}" if base else ""

    message = (
        f"From Svindo: Your purchase invoice is generated. Thank you for shopping with {vendor_name}. "
        f"Your purchase amount is Rs. {total_amount}. "
        f"Download your invoice: {purchase_link} (Valid for 7 days)."
    )

    results = []

    def _send_one(raw_phone, label):
        normalized = _normalize_indian_phone_for_gateway(raw_phone)
        if not normalized:
            results.append((False, f"{label}: phone not found"))
            return
        # Credit check (1 per SMS)
        available = Decimal(sms_setting.available_credits or 0)
        if available <= 0:
            results.append((False, f"{label}: insufficient credits"))
            return
        ok, resp = send_sms_via_msgclub(normalized, message)
        if ok:
            # Deduct 1 credit per accepted SMS
            _deduct_sms_credits(sms_setting, 1)
            results.append((True, f"{label}: SMS accepted by gateway"))
        else:
            results.append((False, f"{label}: failed ({resp})"))

    if send_to_user:
        _send_one(getattr(purchase.user, "mobile", None), "user")
    if send_to_vendor:
        _send_one(getattr(getattr(purchase, "vendor", None), "contact", None), "vendor")

    any_sent = any(ok for ok, _ in results)
    summary = "; ".join([msg for _, msg in results]) if results else "no recipients"
    return any_sent, summary

