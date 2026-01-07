#!/usr/bin/env python
"""
Quick script to check Cashfree webhook status and recent logs.
Run: python check_webhook_status.py
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

from customer.models import Order
from django.utils import timezone
from datetime import timedelta

def check_webhook_logs():
    """Check if webhook.log exists and show recent entries"""
    log_file = BASE_DIR / "logs" / "webhook.log"
    
    print("=" * 80)
    print("CASHFREE WEBHOOK STATUS CHECK")
    print("=" * 80)
    print()
    
    if not log_file.exists():
        print("❌ webhook.log file not found at:", log_file)
        print("   Make sure the webhook has been called at least once.")
        return
    
    print(f"✅ webhook.log found at: {log_file}")
    print()
    
    # Read last 50 lines
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            
            print("📋 Recent Webhook Activity (last 50 lines):")
            print("-" * 80)
            
            # Filter for CASHFREE_WEBHOOK entries
            cashfree_lines = [line for line in recent_lines if "CASHFREE_WEBHOOK" in line]
            
            if cashfree_lines:
                for line in cashfree_lines[-20:]:  # Show last 20 webhook lines
                    print(line.rstrip())
            else:
                print("   No CASHFREE_WEBHOOK entries found in recent logs.")
                print("   This might mean:")
                print("   - Webhook hasn't been called yet")
                print("   - Logs are in a different location")
                print("   - Logger name mismatch")
            
            print()
            
            # Count webhook calls
            total_calls = len([l for l in lines if "WEBHOOK RECEIVED" in l])
            successful = len([l for l in lines if "WEBHOOK PROCESSED SUCCESSFULLY" in l])
            failed = len([l for l in lines if "Invalid signature" in l or "Order not found" in l])
            
            print("📊 Webhook Statistics:")
            print(f"   Total webhook calls: {total_calls}")
            print(f"   Successful: {successful}")
            print(f"   Failed/Errors: {failed}")
            print()
            
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def check_recent_orders():
    """Check recent orders and their payment status"""
    print("=" * 80)
    print("RECENT ORDERS WITH CASHFREE PAYMENT")
    print("=" * 80)
    print()
    
    # Get orders from last 24 hours
    yesterday = timezone.now() - timedelta(days=1)
    
    orders = Order.objects.filter(
        created_at__gte=yesterday,
        cashfree_order_id__isnull=False
    ).order_by('-created_at')[:10]
    
    if not orders.exists():
        print("   No orders with Cashfree payment in the last 24 hours.")
        return
    
    print(f"📦 Found {orders.count()} order(s) with Cashfree payment (last 24 hours):")
    print()
    
    for order in orders:
        status_icon = "✅" if order.is_paid else "⏳"
        cashfree_status = order.cashfree_status or 'N/A'
        
        # Check for IP whitelisting error
        if "403" in str(cashfree_status) or "IP_NOT_WHITELISTED" in str(cashfree_status):
            status_icon = "❌"
        
        print(f"{status_icon} Order: {order.order_id}")
        print(f"   Cashfree Order ID: {order.cashfree_order_id}")
        print(f"   Status: {order.status}")
        print(f"   Is Paid: {order.is_paid}")
        print(f"   Cashfree Status: {cashfree_status}")
        print(f"   Payment Mode: {order.payment_mode or 'N/A'}")
        print(f"   Created: {order.created_at}")
        
        # Show warning for IP whitelisting errors
        if "403" in str(cashfree_status) or "IP_NOT_WHITELISTED" in str(cashfree_status):
            print(f"   ⚠️  WARNING: IP whitelisting error detected!")
            print(f"      See CASHFREE_IP_WHITELISTING_GUIDE.md for fix instructions")
        print()

def check_ip_whitelisting_errors():
    """Check for IP whitelisting errors in recent orders"""
    print("=" * 80)
    print("IP WHITELISTING ERROR CHECK")
    print("=" * 80)
    print()
    
    # Get orders from last 7 days with 403 errors
    week_ago = timezone.now() - timedelta(days=7)
    
    ip_errors = Order.objects.filter(
        created_at__gte=week_ago,
        cashfree_status__icontains="403"
    ).order_by('-created_at')[:10]
    
    if not ip_errors.exists():
        print("✅ No IP whitelisting errors found in recent orders (last 7 days).")
        print()
        return
    
    print(f"❌ Found {ip_errors.count()} order(s) with IP whitelisting errors:")
    print()
    
    for order in ip_errors:
        print(f"   Order: {order.order_id}")
        print(f"   Cashfree Status: {order.cashfree_status}")
        print(f"   Created: {order.created_at}")
        print()
    
    print("⚠️  ACTION REQUIRED:")
    print("   1. Find your server's public IP address")
    print("   2. Add it to Cashfree Dashboard → Settings → IP Whitelist")
    print("   3. See CASHFREE_IP_WHITELISTING_GUIDE.md for detailed instructions")
    print()

def check_webhook_config():
    """Check webhook configuration"""
    print("=" * 80)
    print("WEBHOOK CONFIGURATION")
    print("=" * 80)
    print()
    
    from django.conf import settings
    
    webhook_secret = getattr(settings, 'CASHFREE_WEBHOOK_SECRET', None)
    app_id = getattr(settings, 'CASHFREE_APP_ID', None)
    secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', None)
    base_url = getattr(settings, 'CASHFREE_BASE_URL', None)
    
    print(f"✅ CASHFREE_APP_ID: {'Set' if app_id else '❌ Not Set'}")
    print(f"✅ CASHFREE_SECRET_KEY: {'Set' if secret_key else '❌ Not Set'}")
    print(f"✅ CASHFREE_WEBHOOK_SECRET: {'Set' if webhook_secret else '❌ Not Set'}")
    print(f"✅ CASHFREE_BASE_URL: {base_url or 'Not Set'}")
    print()
    
    if not webhook_secret:
        print("⚠️  WARNING: CASHFREE_WEBHOOK_SECRET is not set!")
        print("   Webhook signature verification will fail.")
        print("   Set it in your environment variables or settings.py")
        print()

if __name__ == "__main__":
    check_webhook_config()
    print()
    check_ip_whitelisting_errors()
    print()
    check_webhook_logs()
    print()
    check_recent_orders()
    print()
    print("=" * 80)
    print("✅ Status check complete!")
    print("=" * 80)

