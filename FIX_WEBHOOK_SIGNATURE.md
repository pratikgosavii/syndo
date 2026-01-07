# Fix Cashfree Webhook Signature Verification

## Problem: Signature Verification Failing

You're seeing this error:
```
[CASHFREE_WEBHOOK] Invalid signature. Expected: 3TfrhMERFd5EqgY82BPv..., Got: ycpm3kqH5iaJ2EmcbZuC...
```

This means the webhook secret in your environment doesn't match the one configured in Cashfree dashboard.

## Solution: Verify and Update Webhook Secret

### Step 1: Get Webhook Secret from Cashfree Dashboard

1. **Login to Cashfree Dashboard**
   - Sandbox: https://sandbox.cashfree.com/
   - Production: https://merchant.cashfree.com/

2. **Navigate to Webhook Settings**
   - Go to: **Settings** → **Developer** → **Webhooks**
   - OR: **Developer** → **Webhooks**
   - OR: **Settings** → **Webhooks**

3. **Find Your Webhook Secret**
   - Look for **"Webhook Secret"** or **"Secret Key"**
   - It should be a long string (usually 32+ characters)
   - Click **"Show"** or **"Reveal"** if it's hidden
   - **Copy the entire secret** (don't miss any characters)

### Step 2: Update Environment Variable

**On Linux/VPS:**
```bash
# Edit your .env file or environment configuration
nano /var/www/syndo/.env

# Add or update this line:
CASHFREE_WEBHOOK_SECRET=your_webhook_secret_from_dashboard

# Or export it directly (temporary, for testing):
export CASHFREE_WEBHOOK_SECRET='your_webhook_secret_from_dashboard'

# Restart your Django application/server
sudo systemctl restart gunicorn  # or whatever service you use
# OR if using supervisor:
supervisorctl restart syndo
```

**On Windows (Local Development):**
```powershell
# Add to .env file in project root:
CASHFREE_WEBHOOK_SECRET=your_webhook_secret_from_dashboard

# Or set environment variable:
$env:CASHFREE_WEBHOOK_SECRET="your_webhook_secret_from_dashboard"
```

### Step 3: Verify Configuration

Run the verification script:
```bash
python verify_webhook_secret.py
```

This will:
- Check if the secret is configured
- Test signature computation with sample data
- Show you what signatures should look like

### Step 4: Test Webhook Again

1. **Trigger a test payment** (or wait for Cashfree to send a webhook)
2. **Check logs:**
   ```bash
   tail -f logs/webhook.log | grep CASHFREE_WEBHOOK
   ```
3. **Look for:**
   - ✅ `Signature verified successfully` (success!)
   - ❌ `Invalid signature` (secret still wrong)

## Common Issues

### Issue 1: Secret Has Extra Spaces or Newlines

**Problem:** Secret copied with extra whitespace

**Solution:**
```bash
# Trim whitespace when setting
export CASHFREE_WEBHOOK_SECRET=$(echo "your_secret" | tr -d '[:space:]')
```

### Issue 2: Secret Not Loading from .env

**Problem:** Environment variable not being loaded

**Solution:**
- Make sure `.env` file is in project root
- Check if you're using `python-dotenv` or `django-environ`
- Verify `.env` is not in `.gitignore` (but secret should be!)
- Restart your Django server after updating `.env`

### Issue 3: Different Secrets for Sandbox vs Production

**Problem:** Using sandbox secret in production or vice versa

**Solution:**
- Sandbox and Production have **different webhook secrets**
- Make sure you're using the correct secret for your environment
- Check `CASHFREE_BASE_URL` matches your environment:
  - Sandbox: `https://sandbox.cashfree.com/pg`
  - Production: `https://api.cashfree.com/pg`

### Issue 4: Secret Changed in Dashboard

**Problem:** Secret was regenerated in Cashfree dashboard

**Solution:**
- If you regenerated the secret in dashboard, you **must** update your environment variable
- Old secret will no longer work
- Update immediately after regenerating

## Quick Test

After updating the secret, test with a sample webhook:

```python
# In Django shell
python manage.py shell

from customer.views import cashfree_webhook
from django.test import RequestFactory
import json

# Create a test request
factory = RequestFactory()
payload = {
    "data": {
        "order": {"order_id": "TEST-001"},
        "payment": {"payment_status": "SUCCESS"}
    },
    "type": "PAYMENT_SUCCESS_WEBHOOK"
}

request = factory.post(
    '/cashfree/webhook/',
    data=json.dumps(payload),
    content_type='application/json',
    HTTP_X_WEBHOOK_VERSION='2023-08-01',
    HTTP_X_WEBHOOK_TIMESTAMP='1767785899837',
    HTTP_X_WEBHOOK_SIGNATURE='test_signature'  # This will fail, but you'll see the computed signature
)

# Check logs to see computed signature
```

## Verify in Logs

After fixing, check your webhook logs:

```bash
# View recent webhook activity
tail -n 50 logs/webhook.log | grep -A 5 "CASHFREE_WEBHOOK"

# Look for successful verification:
# ✅ [CASHFREE_WEBHOOK] Signature verified successfully
```

## Still Not Working?

1. **Double-check the secret:**
   - Copy it again from Cashfree dashboard
   - Make sure no extra characters
   - Verify it's the correct environment (sandbox vs production)

2. **Check signature format:**
   - Run `python verify_webhook_secret.py`
   - Compare computed signatures with received signature in logs
   - The logs now show multiple computed formats to help debug

3. **Contact Cashfree Support:**
   - Email: support@cashfree.com
   - Ask: "My webhook signature verification is failing. Can you verify my webhook secret?"
   - Provide: Your merchant ID and a sample webhook payload

---

**Note:** The webhook will still process even if signature verification fails (in test mode), but you should fix it for production security.

