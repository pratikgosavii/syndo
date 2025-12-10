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
def _validate_coordinates(lat_str: str, lon_str: str, location_name: str) -> tuple:
    """
    Validate and convert coordinate strings to floats.
    Returns: (is_valid, latitude, longitude)
    Valid ranges: latitude -90 to 90, longitude -180 to 180
    """
    try:
        lat = float(lat_str) if lat_str else None
        lon = float(lon_str) if lon_str else None
        
        if lat is None or lon is None:
            print(f"⚠️ [uEngage] {location_name} coordinates are missing")
            return (False, None, None)
        
        # Validate ranges: latitude must be between -90 and 90, longitude between -180 and 180
        if not (-90 <= lat <= 90):
            print(f"❌ [uEngage] {location_name} latitude {lat} is invalid (must be between -90 and 90)")
            return (False, lat, lon)
        
        if not (-180 <= lon <= 180):
            print(f"❌ [uEngage] {location_name} longitude {lon} is invalid (must be between -180 and 180)")
            return (False, lat, lon)
        
        print(f"✅ [uEngage] {location_name} coordinates are valid: lat={lat}, lon={lon}")
        return (True, lat, lon)
    except (ValueError, TypeError) as e:
        print(f"❌ [uEngage] {location_name} coordinates cannot be converted to float: {lat_str}, {lon_str} - {e}")
        return (False, None, None)


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
    print("=" * 80)
    print("🚀 [uEngage] create_delivery_task - START")
    print(f"Order ID: {getattr(order, 'order_id', 'N/A')}")
    
    # Use Rider API new spec
    if not (UENGAGE_RIDER_BASE and UENGAGE_ACCESS_TOKEN):
        print("❌ [uEngage] Missing credentials")
        print(f"UENGAGE_RIDER_BASE: {UENGAGE_RIDER_BASE}")
        print(f"UENGAGE_ACCESS_TOKEN: {'SET' if UENGAGE_ACCESS_TOKEN else 'MISSING'}")
        return {"ok": False, "status_code": None, "error": "missing_credentials", "message": "uEngage rider API not configured"}

    print(f"✅ [uEngage] Credentials check passed")
    print(f"UENGAGE_RIDER_BASE: {UENGAGE_RIDER_BASE}")
    print(f"UENGAGE_ACCESS_TOKEN: {UENGAGE_ACCESS_TOKEN[:10]}...")

    try:
        item0 = order.items.select_related("product").first()
        print(f"📦 [uEngage] First order item: {item0}")
        vendor_user = item0.product.user if item0 and getattr(item0.product, "user", None) else None
        print(f"👤 [uEngage] Vendor user: {vendor_user} (ID: {vendor_user.id if vendor_user else 'N/A'})")
        
        pickup = _pickup_from_company_profile(vendor_user)
        print(f"📍 [uEngage] Pickup details: {pickup}")
        
        drop = _drop_from_order(order)
        print(f"🏠 [uEngage] Drop details: {drop}")
        
        if not (pickup and drop):
            print("❌ [uEngage] Missing pickup or drop addresses")
            return {"ok": False, "status_code": None, "error": "missing_addresses", "message": "Pickup/Drop addresses missing"}

        # storeId from CompanyProfile, fallback to default "89" for testing
        store_id = None
        try:
            cp = vendor_user.user_company_profile if vendor_user else None
            print(f"🏪 [uEngage] Company Profile: {cp}")
            store_id = getattr(cp, "uengage_store_id", None)
            print(f"🏪 [uEngage] Store ID from CompanyProfile: {store_id}")
        except Exception as e:
            print(f"⚠️ [uEngage] Exception getting store_id: {e}")
            store_id = None
        if not store_id:
            # Use default store_id "89" for testing if not set in CompanyProfile
            store_id = "89"
            print(f"🏪 [uEngage] Using default store_id: {store_id}")

        # Get vendor store for pickup coordinates
        vs = vendor_user.vendor_store.first() if vendor_user and getattr(vendor_user, "vendor_store", None) else None
        print(f"🏬 [uEngage] Vendor Store: {vs}")
        pickup_lat_str = str(getattr(vs, "latitude", "") or "") if vs else ""
        pickup_lon_str = str(getattr(vs, "longitude", "") or "") if vs else ""
        pickup_city = getattr(cp, "city", "") or "" if cp else ""
        print(f"📍 [uEngage] Pickup coordinates (raw): lat={pickup_lat_str}, lon={pickup_lon_str}, city={pickup_city}")
        
        # Validate pickup coordinates
        pickup_valid, pickup_lat_float, pickup_lon_float = _validate_coordinates(pickup_lat_str, pickup_lon_str, "Pickup")
        if not pickup_valid:
            print("❌ [uEngage] Invalid pickup coordinates - cannot create delivery task")
            return {"ok": False, "status_code": None, "error": "invalid_pickup_coordinates", "message": f"Invalid pickup coordinates: lat={pickup_lat_str}, lon={pickup_lon_str}"}
        
        pickup_lat = str(pickup_lat_float)
        pickup_lon = str(pickup_lon_float)
        
        # Get drop coordinates
        addr = getattr(order, "address", None)
        print(f"🏠 [uEngage] Order address: {addr}")
        drop_city = getattr(addr, "town_city", "") or "" if addr else ""
        drop_lat_str = str(getattr(addr, "latitude", "") or "") if addr else ""
        drop_lon_str = str(getattr(addr, "longitude", "") or "") if addr else ""
        print(f"📍 [uEngage] Drop coordinates (raw): lat={drop_lat_str}, lon={drop_lon_str}, city={drop_city}")
        
        # Validate drop coordinates
        drop_valid, drop_lat_float, drop_lon_float = _validate_coordinates(drop_lat_str, drop_lon_str, "Drop")
        if not drop_valid:
            print("❌ [uEngage] Invalid drop coordinates - cannot create delivery task")
            return {"ok": False, "status_code": None, "error": "invalid_drop_coordinates", "message": f"Invalid drop coordinates: lat={drop_lat_str}, lon={drop_lon_str}"}
        
        drop_lat = str(drop_lat_float)
        drop_lon = str(drop_lon_float)
        
        # Build order items list
        order_items = []
        for item in order.items.all():
            order_items.append({
                "id": str(item.product.id) if item.product else "",
                "name": item.product.name if item.product else "",
                "quantity": item.quantity,
                "price": float(item.price)
            })
        print(f"📦 [uEngage] Order items count: {len(order_items)}")
        print(f"📦 [uEngage] Order items: {order_items}")
        
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
        
        print(f"🌐 [uEngage] API URL: {url}")
        print(f"🔑 [uEngage] Headers: {headers}")
        print(f"📤 [uEngage] Payload: {payload}")
        
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        print(f"📥 [uEngage] Response Status Code: {resp.status_code}")
        print(f"📥 [uEngage] Response Headers: {dict(resp.headers)}")
        
        try:
            data = resp.json()
            print(f"📥 [uEngage] Response JSON: {data}")
        except Exception as e:
            data = {"message": resp.text}
            print(f"⚠️ [uEngage] Failed to parse JSON, raw text: {resp.text}")
            print(f"⚠️ [uEngage] Exception: {e}")

        # Docs show status as "true"/boolean and keys: taskId, vendor_order_id, Status_code
        status_ok = False
        if isinstance(data, dict):
            status_ok = (data.get("status") in (True, "true", "200", "ACCEPTED"))
        print(f"✅ [uEngage] Status OK: {status_ok}")
        print(f"📊 [uEngage] Response status value: {data.get('status') if isinstance(data, dict) else 'N/A'}")
        
        if resp.status_code in (200, 201) and status_ok:
            task_id = data.get("taskId") or data.get("task_id") or None
            tracking_url = data.get("tracking_url") or None
            print(f"✅ [uEngage] Task created successfully!")
            print(f"🆔 [uEngage] Task ID: {task_id}")
            print(f"🔗 [uEngage] Tracking URL: {tracking_url}")
            print("=" * 80)
            return {"ok": True, "status_code": resp.status_code, "task_id": task_id, "tracking_url": tracking_url, "message": data.get("message"), "raw": data}
        
        print(f"❌ [uEngage] Task creation failed")
        print(f"📊 [uEngage] Error: {data.get('error') if isinstance(data, dict) else 'N/A'}")
        print(f"📊 [uEngage] Message: {data.get('message') if isinstance(data, dict) else resp.text}")
        print("=" * 80)
        return {"ok": False, "status_code": resp.status_code, "error": (data.get("error") if isinstance(data, dict) else None), "message": (data.get("message") if isinstance(data, dict) else resp.text), "raw": data}
    except Exception as e:
        print(f"💥 [uEngage] Exception in create_delivery_task: {str(e)}")
        logger.exception("uEngage create_delivery_task exception")
        print("=" * 80)
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
    print("=" * 80)
    print("🔍 [uEngage] get_serviceability_for_order - START")
    print(f"Order ID: {getattr(order, 'order_id', 'N/A')}")
    
    if not (UENGAGE_RIDER_BASE and UENGAGE_ACCESS_TOKEN):
        print("❌ [uEngage] Missing credentials")
        print(f"UENGAGE_RIDER_BASE: {UENGAGE_RIDER_BASE}")
        print(f"UENGAGE_ACCESS_TOKEN: {'SET' if UENGAGE_ACCESS_TOKEN else 'MISSING'}")
        return {"ok": False, "status_code": None, "error": "missing_credentials", "message": "uEngage rider API not configured"}

    print(f"✅ [uEngage] Credentials check passed")
    print(f"UENGAGE_RIDER_BASE: {UENGAGE_RIDER_BASE}")
    print(f"UENGAGE_ACCESS_TOKEN: {UENGAGE_ACCESS_TOKEN[:10]}...")

    try:
        item0 = order.items.select_related("product").first()
        print(f"📦 [uEngage] First order item: {item0}")
        vendor_user = item0.product.user if item0 and getattr(item0.product, "user", None) else None
        print(f"👤 [uEngage] Vendor user: {vendor_user} (ID: {vendor_user.id if vendor_user else 'N/A'})")
        
        if not vendor_user:
            print("❌ [uEngage] Vendor not found for order")
            return {"ok": False, "status_code": None, "error": "missing_vendor", "message": "Vendor not found for order"}
        
        try:
            cp = vendor_user.user_company_profile
            print(f"🏪 [uEngage] Company Profile: {cp}")
            store_id = getattr(cp, "uengage_store_id", None)
            print(f"🏪 [uEngage] Store ID from CompanyProfile: {store_id}")
        except Exception as e:
            print(f"⚠️ [uEngage] Exception getting store_id: {e}")
            store_id = None
        if not store_id:
            # Use default store_id "89" for testing if not set in CompanyProfile
            store_id = "89"
            print(f"🏪 [uEngage] Using default store_id: {store_id}")
        
        vs = vendor_user.vendor_store.first() if vendor_user and getattr(vendor_user, "vendor_store", None) else None
        print(f"🏬 [uEngage] Vendor Store: {vs}")
        p_lat_str = str(getattr(vs, "latitude", "") or "") if vs else ""
        p_lon_str = str(getattr(vs, "longitude", "") or "") if vs else ""
        print(f"📍 [uEngage] Pickup coordinates (raw): lat={p_lat_str}, lon={p_lon_str}")
        
        # Validate pickup coordinates
        pickup_valid, p_lat, p_lon = _validate_coordinates(p_lat_str, p_lon_str, "Pickup")
        if not pickup_valid:
            print("❌ [uEngage] Invalid pickup coordinates - cannot check serviceability")
            return {"ok": False, "status_code": None, "error": "invalid_pickup_coordinates", "message": f"Invalid pickup coordinates: lat={p_lat_str}, lon={p_lon_str}"}
        
        addr = getattr(order, "address", None)
        print(f"🏠 [uEngage] Order address: {addr}")
        d_lat_str = str(getattr(addr, "latitude", "") or "") if addr else ""
        d_lon_str = str(getattr(addr, "longitude", "") or "") if addr else ""
        print(f"📍 [uEngage] Drop coordinates (raw): lat={d_lat_str}, lon={d_lon_str}")
        
        # Validate drop coordinates
        drop_valid, d_lat, d_lon = _validate_coordinates(d_lat_str, d_lon_str, "Drop")
        if not drop_valid:
            print("❌ [uEngage] Invalid drop coordinates - cannot check serviceability")
            return {"ok": False, "status_code": None, "error": "invalid_drop_coordinates", "message": f"Invalid drop coordinates: lat={d_lat_str}, lon={d_lon_str}"}

        url = f"{UENGAGE_RIDER_BASE}/getServiceability"
        payload = {
            "store_id": str(store_id),
            "pickupDetails": {"latitude": str(p_lat), "longitude": str(p_lon)},
            "dropDetails": {"latitude": str(d_lat), "longitude": str(d_lon)},
        }
        headers = {"Content-Type": "application/json", "access-token": UENGAGE_ACCESS_TOKEN}
        
        print(f"🌐 [uEngage] API URL: {url}")
        print(f"🔑 [uEngage] Headers: {headers}")
        print(f"📤 [uEngage] Payload: {payload}")
        print(f"📍 [uEngage] SERVICEABILITY CHECK COORDINATES:")
        print(f"   🏬 PICKUP:  lat={p_lat}, lon={p_lon}")
        print(f"   🏠 DROP:    lat={d_lat}, lon={d_lon}")
        print(f"   🆔 STORE ID: {store_id}")
        
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📥 [uEngage] Response Status Code: {resp.status_code}")
        print(f"📥 [uEngage] Response Headers: {dict(resp.headers)}")
        
        try:
            data = resp.json()
            print(f"📥 [uEngage] Response JSON: {data}")
        except Exception as e:
            data = {"message": resp.text}
            print(f"⚠️ [uEngage] Failed to parse JSON, raw text: {resp.text}")
            print(f"⚠️ [uEngage] Exception: {e}")
        
        # Expect status "200" or similar with serviceability flags
        service_ok = False
        if isinstance(data, dict):
            status_value = data.get("status")
            print(f"📊 [uEngage] Response status: {status_value} (type: {type(status_value)})")
            # Check if status is 200 (can be int or string)
            if status_value in (200, "200", "success", True):
                svc = data.get("serviceability") or {}
                print(f"📊 [uEngage] Serviceability object: {svc}")
                rider_serviceable = svc.get("riderServiceAble")
                location_serviceable = svc.get("locationServiceAble")
                print(f"📊 [uEngage] riderServiceAble: {rider_serviceable}")
                print(f"📊 [uEngage] locationServiceAble: {location_serviceable}")
                # Service is OK only if BOTH rider and location are serviceable
                service_ok = bool(rider_serviceable and location_serviceable)
                print(f"✅ [uEngage] Service OK (both rider and location): {service_ok}")
                if not service_ok:
                    if not rider_serviceable:
                        print(f"⚠️ [uEngage] Service failed: No rider available")
                    if not location_serviceable:
                        print(f"⚠️ [uEngage] Service failed: Location not serviceable")
            else:
                print(f"⚠️ [uEngage] Status not 200/success, serviceability check failed")
        else:
            print(f"⚠️ [uEngage] Response is not a dict")
        
        print("=" * 80)
        return {"ok": service_ok, "status_code": resp.status_code, "raw": data}
    except Exception as e:
        print(f"💥 [uEngage] Exception in get_serviceability_for_order: {str(e)}")
        logger.exception("uEngage get_serviceability_for_order exception")
        print("=" * 80)
        return {"ok": False, "status_code": None, "error": "exception", "message": str(e)}

