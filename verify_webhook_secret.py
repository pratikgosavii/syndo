#!/usr/bin/env python
"""
Script to verify Cashfree webhook secret configuration.
Run: python verify_webhook_secret.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syndo.settings')
import django
django.setup()

from django.conf import settings
import hmac
import hashlib
import base64
import json

def verify_webhook_secret():
    """Verify webhook secret configuration"""
    print("=" * 80)
    print("CASHFREE WEBHOOK SECRET VERIFICATION")
    print("=" * 80)
    print()
    
    # Get webhook secret from settings
    webhook_secret = getattr(settings, 'CASHFREE_WEBHOOK_SECRET', None)
    webhook_secret_env = os.getenv('CASHFREE_WEBHOOK_SECRET', None)
    
    print("📋 Configuration Check:")
    print(f"   CASHFREE_WEBHOOK_SECRET (from settings): {'✅ Set' if webhook_secret else '❌ Not Set'}")
    print(f"   CASHFREE_WEBHOOK_SECRET (from env): {'✅ Set' if webhook_secret_env else '❌ Not Set'}")
    
    # Use the one that's set
    active_secret = webhook_secret or webhook_secret_env
    
    if not active_secret:
        print()
        print("❌ ERROR: CASHFREE_WEBHOOK_SECRET is not configured!")
        print()
        print("To fix:")
        print("1. Get your webhook secret from Cashfree Dashboard:")
        print("   - Go to: Settings → Developer → Webhooks")
        print("   - Copy the 'Webhook Secret' value")
        print()
        print("2. Set it in your environment:")
        print("   export CASHFREE_WEBHOOK_SECRET='your_secret_here'")
        print()
        print("   Or add to .env file:")
        print("   CASHFREE_WEBHOOK_SECRET=your_secret_here")
        print()
        return
    
    # Mask the secret for display
    if len(active_secret) > 8:
        masked_secret = f"{active_secret[:4]}...{active_secret[-4:]}"
    else:
        masked_secret = "***"
    
    print(f"   Active secret: {masked_secret} (length: {len(active_secret)})")
    print()
    
    # Test signature computation
    print("🧪 Testing Signature Computation:")
    print()
    
    # Sample webhook payload (from your logs)
    sample_payload = {
        "data": {
            "order": {
                "order_id": "25-26-01-JAN-ONL-0010",
                "order_amount": 320.40,
                "order_currency": "INR"
            },
            "payment": {
                "cf_payment_id": "5114924283999",
                "payment_status": "SUCCESS",
                "payment_amount": 320.40
            }
        },
        "type": "PAYMENT_SUCCESS_WEBHOOK"
    }
    
    sample_timestamp = "1767785899837"
    sample_body = json.dumps(sample_payload)
    
    print("   Test payload:")
    print(f"   - Timestamp: {sample_timestamp}")
    print(f"   - Body: {sample_body[:100]}...")
    print()
    
    # Try different signature formats
    print("   Computing signatures with different formats:")
    print()
    
    # Format 1: 2023-08-01 with timestamp (string)
    message1 = f"{sample_timestamp}.{sample_body}"
    sig1 = base64.b64encode(hmac.new(active_secret.encode("utf-8"), message1.encode("utf-8"), hashlib.sha256).digest()).decode()
    print(f"   1. 2023-08-01 format (timestamp.string): {sig1[:40]}...")
    
    # Format 2: Body only
    sig2 = base64.b64encode(hmac.new(active_secret.encode("utf-8"), sample_body.encode("utf-8"), hashlib.sha256).digest()).decode()
    print(f"   2. Body only format: {sig2[:40]}...")
    
    # Format 3: 2023-08-01 with timestamp (bytes)
    message3 = sample_timestamp.encode('utf-8') + b'.' + sample_body.encode('utf-8')
    sig3 = base64.b64encode(hmac.new(active_secret.encode("utf-8"), message3, hashlib.sha256).digest()).decode()
    print(f"   3. 2023-08-01 format (bytes): {sig3[:40]}...")
    print()
    
    print("=" * 80)
    print("✅ Verification complete!")
    print("=" * 80)
    print()
    print("📝 Next Steps:")
    print("1. Compare the computed signatures above with the signature in your webhook logs")
    print("2. If none match, your CASHFREE_WEBHOOK_SECRET might be incorrect")
    print("3. Verify the secret in Cashfree Dashboard → Settings → Developer → Webhooks")
    print("4. Make sure the secret in your environment matches the one in Cashfree dashboard")
    print()

if __name__ == "__main__":
    verify_webhook_secret()

