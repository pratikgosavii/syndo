"""
SMS utility functions for sending SMS via MSGClub API
"""
import http.client
import json
from decimal import Decimal
from django.conf import settings
import re

def send_sms_via_msgclub(phone_number, message):
    """
    Send SMS via MSGClub API
    """
    try:
        from django.conf import settings
        
        # Get API credentials from settings
        api_key = getattr(settings, 'SMS_API_KEY', '')
        api_host = getattr(settings, 'SMS_API_URL', 'msg.msgclub.net')
        api_endpoint = getattr(settings, 'SMS_API_ENDPOINT', 'rest/services/sendSMS/sendGroupSms')
        use_https = bool(getattr(settings, 'SMS_USE_HTTPS', True))
        auth_param = getattr(settings, 'SMS_AUTH_PARAM', 'api_key')
        mobile_param = getattr(settings, 'SMS_MOBILE_PARAM', 'mobile')
        message_param = getattr(settings, 'SMS_MESSAGE_PARAM', 'message')
        sender_id = getattr(settings, 'SMS_SENDER_ID', '') or ''
        sender_param = getattr(settings, 'SMS_SENDER_PARAM', 'senderId')

        # MSGClub / DLT params
        entity_id = getattr(settings, "SMS_ENTITY_ID", "") or ""
        tmid = getattr(settings, "SMS_TM_ID", "") or ""
        template_id = getattr(settings, "SMS_TEMPLATE_ID_INVOICE", "") or ""
        entity_param = getattr(settings, "SMS_ENTITY_PARAM", "entityid")
        tmid_param = getattr(settings, "SMS_TM_PARAM", "tmid")
        template_param = getattr(settings, "SMS_TEMPLATE_PARAM", "templateid")

        # Route / content type params
        route_id = getattr(settings, "SMS_ROUTE_ID", "") or ""
        route_param = getattr(settings, "SMS_ROUTE_PARAM", "routeId")
        sms_content_type = getattr(settings, "SMS_CONTENT_TYPE", "") or ""
        sms_content_type_param = getattr(settings, "SMS_CONTENT_TYPE_PARAM", "smsContentType")

        # Optional consent failover param
        consent_failover_id = getattr(settings, "SMS_CONSENT_FAILOVER_ID", "") or ""
        consent_failover_param = getattr(settings, "SMS_CONSENT_FAILOVER_PARAM", "concentFailoverId")
        
        if not api_key:
            return False, "SMS API key not configured"

        conn_cls = http.client.HTTPSConnection if use_https else http.client.HTTPConnection
        conn = conn_cls(api_host)
        
        headers = {'Cache-Control': "no-cache"}
        
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
            if route_id:
                p[route_param] = route_id
            if sms_content_type:
                p[sms_content_type_param] = sms_content_type
            if entity_id:
                p[entity_param] = entity_id
            if tmid:
                p[tmid_param] = tmid
            if template_id:
                p[template_param] = template_id
            if consent_failover_id:
                p[consent_failover_param] = consent_failover_id
            return p

        params = _build_params(auth_param)
        query_string = urllib.parse.urlencode(params)
        full_endpoint = f"{endpoint}?{query_string}"
        
        def _request_once(ep):
            if ep and not ep.startswith("/"):
                ep = "/" + ep
            conn.request("GET", ep, headers=headers)
            res = conn.getresponse()
            status_code = res.status
            data = res.read()
            response_text = data.decode("utf-8", errors="replace")
            return status_code, dict(res.getheaders()), response_text

        status_code, resp_headers, response_text = _request_once(full_endpoint)

        # Fallback: some MSGClub docs show a comma-separated path
        if (status_code >= 400) and (not response_text) and ("," not in endpoint):
            fallback_endpoint = endpoint.replace("/", ",")
            fallback_full = f"{fallback_endpoint}?{query_string}"
            status_code, resp_headers, response_text = _request_once(fallback_full)
        
        conn.close()
        
        if status_code < 200 or status_code >= 300:
            return False, f"HTTP {status_code}: {response_text or 'Empty response'}"

        if response_text:
            try:
                response_data = json.loads(response_text)
                resp_code = str(response_data.get("responseCode", "")).strip()
                resp_msg = str(response_data.get("response", "")).strip()
                
                if resp_code == "3009" or resp_msg.lower() == "token not found":
                    retry_params = _build_params("AUTH_KEY")
                    retry_qs = urllib.parse.urlencode(retry_params)
                    retry_full = f"{endpoint}?{retry_qs}"
                    status_code2, resp_headers2, response_text2 = _request_once(retry_full)

                    if status_code2 < 200 or status_code2 >= 300:
                        return False, f"HTTP {status_code2} (retry): {response_text2 or 'Empty response'}"

                    if not response_text2:
                        return False, "Empty response (retry)"

                    try:
                        response_data2 = json.loads(response_text2)
                        resp_code2 = str(response_data2.get("responseCode", "")).strip()
                        accepted_codes = {"0", "200", "3001"}
                        if resp_code2 and resp_code2 not in accepted_codes:
                            return False, f"Gateway error (retry): {response_text2}"
                        return True, response_data2
                    except json.JSONDecodeError:
                        if "error" in response_text2.lower() or "invalid" in response_text2.lower():
                            return False, f"Gateway error (retry): {response_text2}"
                        return True, response_text2

                accepted_codes = {"0", "200", "3001"}
                if resp_code and resp_code not in accepted_codes:
                    return False, f"Gateway error: {resp_msg or response_text}"

                return True, response_data
            except json.JSONDecodeError:
                if "error" in response_text.lower() or "invalid" in response_text.lower() or "token" in response_text.lower():
                    return False, f"Gateway error: {response_text}"
                return True, response_text
        else:
            return False, "Empty response from SMS API"
            
    except Exception as e:
        return False, str(e)


def send_sale_sms(sale, invoice_type='invoice'):
    """
    Send SMS for a sale based on invoice type and SMS settings
    """
    from .models import SMSSetting
    
    if not sale.customer or not sale.user:
        return False, "Missing customer or user"
    
    try:
        sms_setting, _ = SMSSetting.objects.get_or_create(
            user=sale.user,
            defaults={'available_credits': Decimal('100.00')}
        )
    except Exception as e:
        return False, str(e)
    
    should_send = sms_setting.enable_purchase_message if invoice_type == 'invoice' else sms_setting.enable_quote_message
    if not should_send:
        return False, "SMS disabled in settings"
    
    try:
        if Decimal(sms_setting.available_credits or 0) <= 0:
            return False, "Insufficient credits"
    except Exception as e:
        return False, str(e)
    
    phone_number = getattr(sale.customer, 'contact', None)
    if not phone_number:
        return False, "Customer phone number not found"
    
    normalized = _normalize_indian_phone_for_gateway(phone_number)
    
    # Prepare SMS message
    total_amount = getattr(sale, "total_amount", None) or getattr(sale, "total_bill_amount", None) or 0
    try:
        store = sale.user.vendor_store.first()
        shop_name = store.name if store else "Svindo"
    except Exception:
        shop_name = "Svindo"

    try:
        base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
    except Exception:
        base = ""

    # Updated invoice link to use path parameter as per urls.py
    invoice_link = f"{base}/vendor/sale-invoice/{sale.id}" if base else ""

    if invoice_type == 'invoice':
        message = (
            f"From Svindo: Your purchase invoice is generated. Thank you for shopping with {shop_name}. "
            f"Your purchase amount is Rs. {total_amount}. "
            f"Download your invoice: {invoice_link} (Valid for 7 days)."
        )
    else:
        invoice_type_display = invoice_type.replace('_', ' ').title()
        invoice_number = sale.invoice_number or f"#{sale.id}"
        message = f"Dear {sale.customer.name}, Your {invoice_type_display} {invoice_number} for Rs {total_amount} has been prepared. Please review."
    
    success, response = send_sms_via_msgclub(normalized, message)
    
    if success:
        try:
            sms_setting.available_credits = max(Decimal('0'), sms_setting.available_credits - Decimal('1'))
            sms_setting.used_credits += Decimal('1')
            sms_setting.save(update_fields=['available_credits', 'used_credits'])
        except Exception:
            pass
        return True, "SMS accepted by gateway"
    else:
        return False, str(response)


def _normalize_indian_phone_for_gateway(phone_number):
    """
    Normalize phone numbers for MSGClub.
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
    Deduct SMS credits safely.
    """
    try:
        credits_to_deduct = Decimal(str(credits_to_deduct or 0))
        if credits_to_deduct <= 0:
            return True, "No credits to deduct"
        old_credits = Decimal(sms_setting.available_credits or 0)
        if old_credits < credits_to_deduct:
            return False, "Insufficient credits"
        sms_setting.available_credits = max(Decimal("0"), old_credits - credits_to_deduct)
        sms_setting.used_credits = Decimal(sms_setting.used_credits or 0) + credits_to_deduct
        sms_setting.save(update_fields=["available_credits", "used_credits"])
        return True, "Credits deducted"
    except Exception as e:
        return False, str(e)


def send_purchase_sms(purchase, send_to_user=True, send_to_vendor=True):
    """
    Send SMS for a Purchase
    """
    from .models import SMSSetting

    if not getattr(purchase, "user", None):
        return False, "No user associated with purchase"

    try:
        sms_setting, _ = SMSSetting.objects.get_or_create(
            user=purchase.user,
            defaults={"available_credits": Decimal("100.00")},
        )
    except Exception as e:
        return False, str(e)

    if not sms_setting.enable_purchase_message:
        return False, "Purchase message is disabled"

    total_amount = getattr(purchase, "total_amount", None) or 0
    vendor_name = getattr(getattr(purchase, "vendor", None), "name", None) or "Vendor"

    try:
        base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
    except Exception:
        base = ""
    
    # Keeping purchase-invoice with query param as per its URL pattern in urls.py
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
        
        available = Decimal(sms_setting.available_credits or 0)
        if available <= 0:
            results.append((False, f"{label}: insufficient credits"))
            return
        
        ok, resp = send_sms_via_msgclub(normalized, message)
        if ok:
            _deduct_sms_credits(sms_setting, 1)
            results.append((True, f"{label}: accepted"))
        else:
            results.append((False, f"{label}: failed"))

    if send_to_user:
        _send_one(getattr(purchase.user, "mobile", None), "user")
    if send_to_vendor:
        _send_one(getattr(getattr(purchase, "vendor", None), "contact", None), "vendor")

    any_sent = any(ok for ok, _ in results)
    summary = "; ".join([msg for _, msg in results]) if results else "no recipients"
    return any_sent, summary

