import json
import os
from django.conf import settings
from typing import Any, Dict, Tuple

import requests


class QuickKYCError(Exception):
    pass


def _get_config() -> Tuple[str, str]:
    """
    Resolve QuickKYC configuration from Django settings first,
    then fall back to environment variables.
    """
    base_url = getattr(settings, "QUICKKYC_BASE_URL", None) or os.getenv("QUICKKYC_BASE_URL", "https://api.quickekyc.com/api/v1")
    api_key = getattr(settings, "QUICKKYC_API_KEY", None) or os.getenv("QUICKKYC_API_KEY", "")
    base_url = base_url.rstrip("/")
    if not api_key:
        raise QuickKYCError("QuickKYC configuration missing (QUICKKYC_API_KEY).")
    return base_url, api_key


def _post(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    base_url, api_key = _get_config()
    url = f"{base_url}{endpoint}"
    headers = {
        "Content-Type": "application/json",
    }
    # QuickKYC uses API key inside payload as "key" per docs
    payload = {**payload, "key": api_key}
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
    except requests.RequestException as e:
        raise QuickKYCError(f"QuickKYC request error: {e}") from e

    if resp.status_code >= 400:
        raise QuickKYCError(f"QuickKYC HTTP {resp.status_code}: {resp.text}")
    try:
        return resp.json()
    except Exception:
        raise QuickKYCError("QuickKYC returned non-JSON response")


def verify_pan(pan_number: str, full_name: str = "") -> Dict[str, Any]:
    """
    Verify PAN number via QuickKYC.
    Depending on provider, name may be optional. Kept for future parity.
    """
    # API expects "id_number" for the PAN
    payload = {"id_number": pan_number}
    # Some providers support name; QuickKYC pan API may ignore it
    if full_name:
        payload["name"] = full_name
    return _post("/pan/pan", payload)


def verify_gstin(gstin: str) -> Dict[str, Any]:
    """Verify GSTIN via QuickKYC."""
    payload = {"id_number": gstin, "filing_status_get": True}
    return _post("/corporate/gstin", payload)


def verify_bank(account_number: str, ifsc: str, account_holder: str = "") -> Dict[str, Any]:
    """
    Verify bank account via QuickKYC.
    Some providers support penny-drop or name match. Keep name optional.
    """
    payload = {"id_number": account_number, "ifsc": ifsc}
    if account_holder:
        payload["name"] = account_holder
    return _post("/bank-verification/pd", payload)

def verify_fssai(fssai_number: str) -> Dict[str, Any]:
    """Verify FSSAI number via QuickKYC."""
    payload = {"id_number": fssai_number}
    return _post("/corporate/fssai_verification", payload)


