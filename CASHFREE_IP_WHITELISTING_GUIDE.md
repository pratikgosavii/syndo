# Cashfree IP Whitelisting Guide

## Problem: "Your IP address is not allowed" (403 Error)

When you see this error in your order response:
```json
{
  "cashfree_status": "ERROR:403:IP_NOT_WHITELISTED",
  "payment": {
    "status": "ERROR",
    "code": 403,
    "message": "Your IP address is not allowed"
  }
}
```

This means your server's IP address is not whitelisted in Cashfree's dashboard.

## Solution: Whitelist Your Server IP

### Step 1: Find Your Server IP Address

**On Linux/VPS:**
```bash
# Get your public IP address
curl ifconfig.me
# or
curl ipinfo.io/ip
# or
curl icanhazip.com
```

**On Windows (if testing locally):**
```powershell
# Get your public IP
Invoke-RestMethod -Uri "https://api.ipify.org"
```

**For Production Server:**
- If you're using a VPS (like DigitalOcean, AWS, etc.), check your server's public IP in the hosting dashboard
- If you're behind a load balancer or proxy, you may need to whitelist the load balancer's IP

### Step 2: Add IP to Cashfree Dashboard

**⚠️ IMPORTANT: You need IP Whitelisting (for API calls), NOT Domain/App Whitelisting (for payments)**

1. **Login to Cashfree Dashboard**
   - Go to: https://merchant.cashfree.com/ (for production) or https://sandbox.cashfree.com/ (for testing)

2. **Navigate to IP Whitelist Settings**
   
   **Option A: Via Settings Menu**
   - Go to: **Settings** (top menu) → **Security** → **IP Whitelist**
   
   **Option B: Via Developer Menu**
   - Go to: **Developer** (top menu) → **API Settings** → **IP Whitelist**
   
   **Option C: Direct URL (if available)**
   - Try: `https://merchant.cashfree.com/settings/security/ip-whitelist`
   - Or: `https://sandbox.cashfree.com/settings/security/ip-whitelist`
   
   **If you see "Website Link" or "App Link" options:**
   - ❌ You're in the **wrong section** (Domain/App Whitelisting)
   - ✅ Go back and look for **"IP Whitelist"** or **"API IP Whitelist"** or **"Server IP"** section
   - The correct section should show options to add IP addresses, not domains/app packages

3. **Add Your IP Address**
   - Click **"Add IP"** or **"Whitelist IP"** or **"Add New IP"**
   - Enter your server's public IP address (from Step 1)
   - Add a description (e.g., "Production Server" or "VPS Server")
   - Click **Save** or **Submit**

**Note:** If you can't find IP Whitelist settings:
- Some Cashfree accounts may have IP whitelisting disabled by default
- Contact Cashfree support to enable IP whitelisting for your account
- Email: support@cashfree.com or use dashboard support chat

4. **For Multiple Environments**
   - Add your **production server IP**
   - Add your **staging/test server IP** (if different)
   - Add your **local development IP** (if testing from local machine)

### Step 3: Verify IP Whitelisting

After adding the IP, wait a few minutes for changes to propagate, then test again:

```bash
# Test by creating a new order
# The error should no longer appear
```

### Step 4: Check Current IP in Logs

The Cashfree integration logs will show which IP is being used. Check your logs:

```bash
# View recent Cashfree API calls
grep "Cashfree API" logs/requests.log | tail -20
```

## Common Issues

### Issue 0: Can't Find IP Whitelist Section (Only See Domain/App Whitelisting)

**Problem:** You see options for "Website Link" or "App Link" but no IP whitelisting.

**Solution:**

1. **Check Different Menu Locations:**
   - Try: **Settings** → **API Settings** → **IP Whitelist**
   - Try: **Developer** → **Security** → **IP Whitelist**
   - Try: **Settings** → **Advanced Settings** → **IP Whitelist**

2. **Check if IP Whitelisting is Enabled:**
   - Some Cashfree accounts have IP whitelisting disabled by default
   - You may need to contact Cashfree support to enable it

3. **Alternative: Disable IP Whitelisting (Not Recommended for Production):**
   - Some accounts allow disabling IP whitelisting entirely
   - Go to: **Settings** → **Security** → **API Security**
   - Look for "Disable IP Whitelist" or "Allow All IPs" option
   - ⚠️ **Warning:** This reduces security - only use for testing

4. **Contact Cashfree Support:**
   - Email: support@cashfree.com
   - Dashboard: Use support chat
   - Ask: "How do I whitelist my server IP address for API calls?"
   - Provide: Your merchant ID and server IP address

5. **Check Cashfree Documentation:**
   - Visit: https://docs.cashfree.com/docs/payments/online/go-live/ip-whitelist
   - Or search: "Cashfree IP whitelist API"

### Issue 1: IP Changes Frequently (Dynamic IP)

If your server has a dynamic IP that changes:

**Solution A: Use Static IP**
- Contact your hosting provider to get a static IP address
- Update the whitelist when IP changes

**Solution B: Use IP Range (if supported)**
- Some Cashfree accounts support IP ranges
- Contact Cashfree support to enable this feature

### Issue 2: Behind Load Balancer/Proxy

If your server is behind a load balancer (AWS ALB, Cloudflare, etc.):

1. **Whitelist the Load Balancer IPs**
   - Get the IP ranges from your provider
   - AWS ALB: Check AWS IP ranges
   - Cloudflare: Check Cloudflare IP ranges

2. **Or Use X-Forwarded-For Header** (if Cashfree supports it)
   - Contact Cashfree support for this option

### Issue 3: Multiple Servers

If you have multiple servers (production, staging, etc.):

- Whitelist **all server IPs** in Cashfree dashboard
- Keep a list of all IPs that need access

## Testing After Whitelisting

1. **Create a test order** with online payment
2. **Check the response** - should not have 403 error
3. **Verify in logs** - should see successful Cashfree API call

```bash
# Check for successful Cashfree order creation
grep "Cashfree order created successfully" logs/requests.log
```

## Alternative Solutions

### Option 1: Disable IP Whitelisting (For Testing/Sandbox Only)

If you can't find IP whitelist settings, you might be able to disable IP whitelisting:

1. Go to Cashfree Dashboard → **Settings** → **Security** → **API Security**
2. Look for:
   - "Disable IP Whitelist"
   - "Allow All IPs"
   - "IP Whitelist: OFF/ON" toggle
3. **⚠️ WARNING**: 
   - This reduces security
   - **Only do this for sandbox/testing accounts**
   - **Never disable for production accounts**

### Option 2: Contact Cashfree Support

If IP whitelisting is not available in your dashboard:

1. **Email Support:**
   - Email: support@cashfree.com
   - Subject: "Enable IP Whitelisting for API Calls"
   - Include:
     - Your merchant ID
     - Your server IP address (from Step 1)
     - Screenshot of your Security/Settings page

2. **Dashboard Support Chat:**
   - Use the chat widget in Cashfree dashboard
   - Ask: "I need to whitelist my server IP for API calls. I only see domain/app whitelisting options."

3. **Phone Support:**
   - Check Cashfree website for support phone number
   - Call and request IP whitelisting activation

## For Development/Testing

If you're testing from your local machine:

1. **Find your local public IP** (see Step 1 above)
2. **Add it to Cashfree sandbox** IP whitelist
3. **Note**: Your IP may change if you restart your router - you'll need to update the whitelist

## Quick Check Script

Run this to see your current public IP:

```bash
python -c "import requests; print('Your public IP:', requests.get('https://api.ipify.org').text)"
```

## Contact Cashfree Support

If you continue to have issues:

1. **Email**: support@cashfree.com
2. **Dashboard**: Use the support chat in Cashfree dashboard
3. **Provide**:
   - Your merchant ID
   - Your server IP address
   - Error message and timestamp
   - Order ID (if applicable)

---

## After Fixing

Once IP is whitelisted, you should see:

✅ **Success Response:**
```json
{
  "cashfree_status": "CREATED",
  "payment": {
    "status": "CREATED",
    "payment_session_id": "...",
    "payment_link": "https://..."
  }
}
```

❌ **Before Fix (403 Error):**
```json
{
  "cashfree_status": "ERROR:403:IP_NOT_WHITELISTED",
  "payment": {
    "status": "ERROR",
    "code": 403,
    "message": "Your IP address is not allowed"
  }
}
```

