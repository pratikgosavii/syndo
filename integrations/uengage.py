import logging
import requests
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

UENGAGE_API_BASE: str = getattr(settings, "UENGAGE_API_BASE", "").rstrip("/")
UENGAGE_API_KEY: str = getattr(settings, "UENGAGE_API_KEY", "")
UENGAGE_WABA: str = getattr(settings, "UENGAGE_WABA", "")


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {UENGAGE_API_KEY}",
        "Content-Type": "application/json",
    }


def send_template(to: str, template_name: str, body_params: List[str]) -> Dict:
    """
    Send a WhatsApp template message via uEngage.
    body_params: ordered variables for the template body.
    """
    if not (UENGAGE_API_BASE and UENGAGE_API_KEY):
        logger.error("uEngage credentials missing. Skipping send_template.")
        return {"status": "SKIPPED", "reason": "missing_credentials"}

    # Example endpoint/payload; adjust to your uEngage account spec if needed
    url = f"{UENGAGE_API_BASE}/v1/whatsapp/send-template"
    payload = {
        "from": UENGAGE_WABA or None,
        "to": to,
        "template": {
            "name": template_name,
            "language": "en",
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": v} for v in body_params],
                }
            ],
        },
    }

    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=15)
        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}
        if resp.status_code in (200, 201):
            return {"status": "OK", "data": data}
        logger.error("uEngage send_template failed: %s %s", resp.status_code, data)
        return {"status": "ERROR", "code": resp.status_code, "data": data}
    except Exception as e:
        logger.exception("uEngage send_template exception")
        return {"status": "ERROR", "exception": str(e)}


def get_recipient_phone(order) -> Optional[str]:
    """
    Determine best recipient phone number for an order.
    Preference: Address.mobile_number -> User.mobile -> User.phone
    """
    try:
        if getattr(order, "address", None) and getattr(order.address, "mobile_number", None):
            return str(order.address.mobile_number)
    except Exception:
        pass
    try:
        if getattr(order, "user", None):
            for attr in ("mobile", "mobile_number", "phone"):
                val = getattr(order.user, attr, None)
                if val:
                    return str(val)
    except Exception:
        pass
    return None


def notify_delivery_event(order, event: str, tracking_link: Optional=str, rider_name: Optional[str]=None, rider_phone: Optional[str]=None):
    """
    High-level helper to send delivery-related templates for an Order.
    event: one of ["order_confirmed", "packed", "shipped", "out_for_delivery", "delivered", "cancelled"]
    """
    to = get_recipient_phone(order)
    if not to:
        logger.warning("uEngage: No recipient phone for order %s", getattr(order, "order_id", None))
        return {"status": "SKIPPED", "reason": "no_recipient"}

    order_id = getattr(order, "order_id", "")
    store_name = ""
    try:
        # derive vendor store from first item
        item = order.items.select_related("product").first()
        if item and getattr(item.product, "user", None) and getattr(item.product.user, "vendor_store", None):
            vs = item.product.user.vendor_store.first()
            if vs and getattr(vs, "name", None):
                store_name = vs.name
    except Exception:
        store_name = ""

    template_map = {
        "order_confirmed": ("order_confirmed", [order_id, store_name]),
        "packed": ("order_packed", [order_id, store_name]),
        "shipped": ("order_shipped", [order_id, tracking_link or ""]),
        "out_for_delivery": ("order_out_for_delivery", [order_id, rider_name or "", rider_phone or "", tracking_link or ""]),
        "delivered": ("order_delivered", [order_id]),
        "cancelled": ("order_cancelled", [order_id]),
    }
    tpl = template_map.get(event)
    if not tpl:
        return {"status": "SKIPPED", "reason": f"unknown_event:{event}"}

    template_name, params = tpl
    return send_template(to, template_name, params)

