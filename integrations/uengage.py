import logging
import requests
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

UENGAGE_API_BASE: str = getattr(settings, "UENGAGE_API_BASE", "").rstrip("/")
UENGAGE_API_KEY: str = getattr(settings, "UENGAGE_API_KEY", "")
UENGAGE_WABA: str = getattr(settings, "UENGAGE_WABA", "")
UENGAGE_DELIVERY_BASE: str = getattr(settings, "UENGAGE_DELIVERY_BASE", UENGAGE_API_BASE).rstrip("/")
UENGAGE_RIDER_BASE: str = getattr(settings, "UENGAGE_RIDER_BASE", "").rstrip("/")
UENGAGE_ACCESS_TOKEN: str = getattr(settings, "UENGAGE_ACCESS_TOKEN", "")


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
            data = {"message": resp.text}

        # According to docs: success -> { status: boolean, message: string }
        status_bool = None
        if isinstance(data, dict):
            status_bool = data.get("status")

        if resp.status_code in (200, 201) and status_bool is True:
            return {"ok": True, "status_code": resp.status_code, "message": data.get("message"), "raw": data}

        # Normalize error payloads for 400/401/404 or any non-OK
        error = (isinstance(data, dict) and data.get("error")) or None
        message = (isinstance(data, dict) and data.get("message")) or resp.text
        logger.error("uEngage send_template failed: status=%s code=%s error=%s message=%s",
                     status_bool, resp.status_code, error, message)
        return {"ok": False, "status_code": resp.status_code, "error": error, "message": message, "raw": data}
    except Exception as e:
        logger.exception("uEngage send_template exception")
        return {"ok": False, "status_code": None, "error": "exception", "message": str(e)}


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


def notify_delivery_event(order, event: str, tracking_link: Optional[str]=None, rider_name: Optional[str]=None, rider_phone: Optional[str]=None):
    """
    High-level helper to send delivery-related templates for an Order.
    event: one of ["order_confirmed", "packed", "shipped", "out_for_delivery", "delivered", "cancelled"]
    """
    # Gate by vendor DeliveryMode.is_auto_assign_enabled
    try:
        vendor_user = None
        item0 = order.items.select_related("product").first()
        if item0 and getattr(item0.product, "user", None):
            vendor_user = item0.product.user
        if vendor_user:
            from vendor.models import DeliveryMode  # local import to avoid circulars
            enabled = DeliveryMode.objects.filter(user=vendor_user, is_auto_assign_enabled=True).exists()
            if not enabled:
                return {"status": "SKIPPED", "reason": "auto_assign_disabled"}
    except Exception:
        # If check fails, do not block notifications silently; proceed best-effort
        pass

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


# -----------------------------
# Delivery Task APIs (assumptive endpoints; adjust to real docs)
# -----------------------------
def _pickup_from_company_profile(vendor_user):
    try:
        cp = vendor_user.user_company_profile
    except Exception:
        return None
    if not cp:
        return None
    address = ", ".join([
        p for p in [
            cp.address_line_1, cp.address_line_2, cp.city, cp.state.name if getattr(cp.state, "name", None) else None, cp.pincode, cp.country
        ] if p
    ])
    return {
        "name": cp.company_name or "",
        "phone": cp.contact or "",
        "address": address or "",
    }


def _drop_from_order(order):
    addr = getattr(order, "address", None)
    if not addr:
        return None
    address = ", ".join([
        p for p in [
            addr.flat_building, addr.area_street, addr.landmark, addr.town_city, addr.state, addr.pincode
        ] if p
    ])
    return {
        "name": addr.full_name or "",
        "phone": addr.mobile_number or "",
        "address": address or "",
    }


def create_delivery_task(order) -> Dict:
    """
    Create a delivery task with uEngage for the given order.
    Returns normalized dict: { ok, status_code, task_id, tracking_url, message, error, raw }
    """
    # Use Rider API new spec
    if not (UENGAGE_RIDER_BASE and UENGAGE_ACCESS_TOKEN):
        return {"ok": False, "status_code": None, "error": "missing_credentials", "message": "uEngage rider API not configured"}

    try:
        item0 = order.items.select_related("product").first()
        vendor_user = item0.product.user if item0 and getattr(item0.product, "user", None) else None
        pickup = _pickup_from_company_profile(vendor_user)
        drop = _drop_from_order(order)
        if not (pickup and drop):
            return {"ok": False, "status_code": None, "error": "missing_addresses", "message": "Pickup/Drop addresses missing"}

        # storeId from CompanyProfile, fallback to default "89" for testing
        store_id = None
        try:
            cp = vendor_user.user_company_profile if vendor_user else None
            store_id = getattr(cp, "uengage_store_id", None)
        except Exception:
            store_id = None
        if not store_id:
            # Use default store_id "89" for testing if not set in CompanyProfile
            store_id = "89"

        # Get vendor store for pickup coordinates
        vs = vendor_user.vendor_store.first() if vendor_user and getattr(vendor_user, "vendor_store", None) else None
        pickup_lat = str(getattr(vs, "latitude", "") or "") if vs else ""
        pickup_lon = str(getattr(vs, "longitude", "") or "") if vs else ""
        pickup_city = getattr(cp, "city", "") or "" if cp else ""
        
        # Get drop coordinates
        addr = getattr(order, "address", None)
        drop_city = getattr(addr, "town_city", "") or "" if addr else ""
        drop_lat = str(getattr(addr, "latitude", "") or "") if addr else ""
        drop_lon = str(getattr(addr, "longitude", "") or "") if addr else ""
        
        # Build order items list
        order_items = []
        for item in order.items.all():
            order_items.append({
                "id": str(item.product.id) if item.product else "",
                "name": item.product.name if item.product else "",
                "quantity": item.quantity,
                "price": float(item.price)
            })
        
        url = f"{UENGAGE_RIDER_BASE}/createTask"
        payload = {
            "storeId": str(store_id),
            "pickup_details": {
                "name": pickup["name"],
                "contact_number": pickup["phone"],
                "address": pickup["address"],
                "city": pickup_city,
                "latitude": pickup_lat,
                "longitude": pickup_lon,
            },
            "drop_details": {
                "name": drop["name"],
                "contact_number": drop["phone"],
                "address": drop["address"],
                "city": drop_city,
                "latitude": drop_lat,
                "longitude": drop_lon,
            },
            "order_details": {
                "order_total": str(order.total_amount or ""),
                "paid": "true" if getattr(order, "is_paid", False) else "false",
                "vendor_order_id": getattr(order, "order_id", ""),
                "order_source": "pos",
                "customer_orderId": getattr(order, "order_id", ""),
            },
            "order_items": order_items,
            "authentication": {
                "delivery_otp": "234",
                "rto_otp": "true"
            }
        }
        headers = {"Content-Type": "application/json", "access-token": UENGAGE_ACCESS_TOKEN}
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        try:
            data = resp.json()
        except Exception:
            data = {"message": resp.text}

        # Docs show status as "true"/boolean and keys: taskId, vendor_order_id, Status_code
        status_ok = False
        if isinstance(data, dict):
            status_ok = (data.get("status") in (True, "true", "200", "ACCEPTED"))
        if resp.status_code in (200, 201) and status_ok:
            task_id = data.get("taskId") or data.get("task_id") or None
            tracking_url = data.get("tracking_url") or None
            return {"ok": True, "status_code": resp.status_code, "task_id": task_id, "tracking_url": tracking_url, "message": data.get("message"), "raw": data}
        return {"ok": False, "status_code": resp.status_code, "error": (data.get("error") if isinstance(data, dict) else None), "message": (data.get("message") if isinstance(data, dict) else resp.text), "raw": data}
    except Exception as e:
        logger.exception("uEngage create_delivery_task exception")
        return {"ok": False, "status_code": None, "error": "exception", "message": str(e)}


def cancel_delivery_task(task_id: str) -> Dict:
    if not (UENGAGE_RIDER_BASE and UENGAGE_ACCESS_TOKEN):
        return {"ok": False, "status_code": None, "error": "missing_credentials", "message": "uEngage rider API not configured"}
    try:
        url = f"{UENGAGE_RIDER_BASE}/cancelTask"
        payload = {"storeId": "", "taskId": task_id}
        headers = {"Content-Type": "application/json", "access-token": UENGAGE_ACCESS_TOKEN}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        try:
            data = resp.json()
        except Exception:
            data = {"message": resp.text}
        status_bool = isinstance(data, dict) and (data.get("status") in (True, "true"))
        if resp.status_code in (200, 201) and status_bool:
            return {"ok": True, "status_code": resp.status_code, "message": data.get("message"), "raw": data}
        return {"ok": False, "status_code": resp.status_code, "error": (data.get("error") if isinstance(data, dict) else None), "message": (data.get("message") if isinstance(data, dict) else resp.text), "raw": data}
    except Exception as e:
        logger.exception("uEngage cancel_delivery_task exception")
        return {"ok": False, "status_code": None, "error": "exception", "message": str(e)}


def get_delivery_status(task_id: str) -> Dict:
    if not (UENGAGE_RIDER_BASE and UENGAGE_ACCESS_TOKEN):
        return {"ok": False, "status_code": None, "error": "missing_credentials", "message": "uEngage rider API not configured"}
    try:
        url = f"{UENGAGE_RIDER_BASE}/trackTaskStatus"
        payload = {"storeId": "", "taskId": task_id}
        headers = {"Content-Type": "application/json", "access-token": UENGAGE_ACCESS_TOKEN}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        try:
            data = resp.json()
        except Exception:
            data = {"message": resp.text}
        status_bool = isinstance(data, dict) and (data.get("status") in (True, "true"))
        if resp.status_code in (200, 201) and status_bool:
            return {"ok": True, "status_code": resp.status_code, "message": data.get("message"), "raw": data}
        return {"ok": False, "status_code": resp.status_code, "error": (data.get("error") if isinstance(data, dict) else None), "message": (data.get("message") if isinstance(data, dict) else resp.text), "raw": data}
    except Exception as e:
        logger.exception("uEngage get_delivery_status exception")
        return {"ok": False, "status_code": None, "error": "exception", "message": str(e)}


def get_serviceability_for_order(order) -> Dict:
    """
    Calls /getServiceability with pickup/drop lat/lon for this order's vendor store and address.
    """
    if not (UENGAGE_RIDER_BASE and UENGAGE_ACCESS_TOKEN):
        return {"ok": False, "status_code": None, "error": "missing_credentials", "message": "uEngage rider API not configured"}
    try:
        item0 = order.items.select_related("product").first()
        vendor_user = item0.product.user if item0 and getattr(item0.product, "user", None) else None
        if not vendor_user:
            return {"ok": False, "status_code": None, "error": "missing_vendor", "message": "Vendor not found for order"}
        try:
            cp = vendor_user.user_company_profile
            store_id = getattr(cp, "uengage_store_id", None)
        except Exception:
            store_id = None
        if not store_id:
            # Use default store_id "89" for testing if not set in CompanyProfile
            store_id = "89"
        vs = vendor_user.vendor_store.first() if getattr(vendor_user, "vendor_store", None) else None
        p_lat = str(getattr(vs, "latitude", "") or "")
        p_lon = str(getattr(vs, "longitude", "") or "")
        addr = getattr(order, "address", None)
        d_lat = str(getattr(addr, "latitude", "") or "")
        d_lon = str(getattr(addr, "longitude", "") or "")

        url = f"{UENGAGE_RIDER_BASE}/getServiceability"
        payload = {
            "store_id": str(store_id),
            "pickupDetails": {"latitude": p_lat, "longitude": p_lon},
            "dropDetails": {"latitude": d_lat, "longitude": d_lon},
        }
        headers = {"Content-Type": "application/json", "access-token": UENGAGE_ACCESS_TOKEN}
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        try:
            data = resp.json()
        except Exception:
            data = {"message": resp.text}
        # Expect status "200" or similar with serviceability flags
        service_ok = False
        if isinstance(data, dict):
            if data.get("status") in (200, "200"):
                svc = data.get("serviceability") or {}
                service_ok = bool(svc.get("riderServiceAble") and svc.get("locationServiceAble"))
        return {"ok": service_ok, "status_code": resp.status_code, "raw": data}
    except Exception as e:
        logger.exception("uEngage get_serviceability_for_order exception")
        return {"ok": False, "status_code": None, "error": "exception", "message": str(e)}

