# Quick Setup: Cashfree Webhook Secret

## Current Status

Your webhook secret is **NOT configured** in Django settings. The code is using a default value `"test_webhook_secret"` which won't match Cashfree's signature.

## Quick Fix (3 Steps)

### Step 1: Get Webhook Secret from Cashfree

1. Login to **Cashfree Sandbox Dashboard**: https://sandbox.cashfree.com/
2. Go to: **Settings** → **Developer** → **Webhooks**
3. Find **"Webhook Secret"** or **"Secret Key"**
4. Click **"Show"** or **"Reveal"** to see it
5. **Copy the entire secret** (it's a long string)

### Step 2: Set Environment Variable on Your VPS

**Option A: Add to .env file (Recommended)**

```bash
# Edit .env file
nano /var/www/syndo/.env

# Add this line (replace with your actual secret):
CASHFREE_WEBHOOK_SECRET=your_actual_webhook_secret_from_dashboard

# Save and exit (Ctrl+X, then Y, then Enter)
```

**Option B: Export directly (Temporary)**

```bash
export CASHFREE_WEBHOOK_SECRET='your_actual_webhook_secret_from_dashboard'
```

### Step 3: Restart Your Django Application

```bash
# If using systemd:
sudo systemctl restart gunicorn
# or
sudo systemctl restart your-service-name

# If using supervisor:
supervisorctl restart syndo

# If using uWSGI:
sudo systemctl restart uwsgi

# If running manually, just restart the process
```

### Step 4: Verify It's Working

```bash
# Check if secret is loaded
python check_webhook_status.py

# Should now show:
# ✅ CASHFREE_WEBHOOK_SECRET: Set

# Test webhook signature
python verify_webhook_secret.py
```

## Check Current Secret

To see what secret is currently being used:

```bash
python manage.py shell

from django.conf import settings
import os

# Check from settings
print("From settings:", getattr(settings, 'CASHFREE_WEBHOOK_SECRET', 'Not set'))

# Check from environment
print("From env:", os.getenv('CASHFREE_WEBHOOK_SECRET', 'Not set'))
```

## Important Notes

1. **Sandbox vs Production**: Sandbox and Production have **different webhook secrets**
   - Make sure you're using the **sandbox secret** if you're testing
   - Check your `CASHFREE_BASE_URL` - if it's `sandbox.cashfree.com`, use sandbox secret

2. **Secret Format**: The webhook secret is usually:
   - 32+ characters long
   - Alphanumeric with special characters
   - Case-sensitive

3. **After Setting**: Wait for the next webhook or trigger a test payment to verify signature works

## Troubleshooting

### Still showing "Not Set" after adding to .env?

1. **Check .env file location:**
   ```bash
   # Should be in project root
   ls -la /var/www/syndo/.env
   ```

2. **Check if django-environ or python-dotenv is loading it:**
   ```bash
   # Check settings.py for dotenv loading
   grep -i "dotenv\|environ" /var/www/syndo/syndo/settings.py
   ```

3. **Manually load in settings.py (temporary fix):**
   ```python
   # In syndo/settings.py, add:
   import os
   from dotenv import load_dotenv
   load_dotenv()
   
   CASHFREE_WEBHOOK_SECRET = os.getenv('CASHFREE_WEBHOOK_SECRET')
   ```

### Signature Still Failing?

1. **Verify secret matches dashboard:**
   - Copy secret from dashboard again
   - Make sure no extra spaces or newlines
   - Check if it's the correct environment (sandbox vs production)

2. **Check webhook version:**
   - Your webhooks are using version `2021-09-21`
   - Signature format: `timestamp + raw_body` (no dot separator)
   - The code now handles this correctly

3. **Test signature computation:**
   ```bash
   python verify_webhook_secret.py
   ```

## After Fixing

Once the secret is set correctly, you should see in logs:

```
✅ [CASHFREE_WEBHOOK] Signature verified successfully using format: 2021-09-21_format
```

Instead of:

```
❌ [CASHFREE_WEBHOOK] Invalid signature
```

---

**Need help?** Check `FIX_WEBHOOK_SIGNATURE.md` for more detailed troubleshooting.

