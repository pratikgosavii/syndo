# Quick Fix: Cashfree IP Whitelisting Issue

## You're Seeing: "Website Link" or "App Link" Options

**This means:** You're in the **Domain/App Whitelisting** section, not **IP Whitelisting**.

### What You Need vs What You're Seeing

| What You Need | What You're Seeing |
|--------------|-------------------|
| ✅ **IP Whitelisting** (for API calls from your server) | ❌ **Domain/App Whitelisting** (for payments from website/app) |
| Allows your server to make API calls | Allows payments from your website domain or mobile app |

## Quick Solutions

### Solution 1: Find the Correct Section

1. **Go back to main menu**
2. **Look for these menu items:**
   - **Settings** → **Security** → **IP Whitelist**
   - **Settings** → **API Settings** → **IP Whitelist**
   - **Developer** → **Security** → **IP Whitelist**
   - **Developer** → **API Settings** → **IP Whitelist**

3. **The correct section should:**
   - Show a form to enter **IP addresses** (like `123.45.67.89`)
   - NOT ask for website domains or app package names
   - Have a button like "Add IP" or "Whitelist IP"

### Solution 2: Disable IP Whitelisting (Sandbox/Testing Only)

If you're using **sandbox/test account** and can't find IP whitelist:

1. Go to: **Settings** → **Security** → **API Security**
2. Look for toggle/option: **"IP Whitelist"** or **"Allow All IPs"**
3. Turn it **OFF** or **Disable**
4. ⚠️ **Only for testing!** Never disable for production.

### Solution 3: Contact Cashfree Support

**If you can't find IP whitelisting anywhere:**

1. **Email:** support@cashfree.com
2. **Subject:** "Need to whitelist server IP for API calls"
3. **Message:**
   ```
   Hi,
   
   I'm getting "Your IP address is not allowed" (403 error) when making API calls.
   I can only see Domain/App whitelisting options in my dashboard, not IP whitelisting.
   
   Please help me:
   1. Enable IP whitelisting for my account, OR
   2. Guide me to the correct section in dashboard
   
   My details:
   - Merchant ID: [YOUR_MERCHANT_ID]
   - Server IP: [YOUR_SERVER_IP]
   - Environment: Sandbox/Production
   
   Thanks!
   ```

## Find Your Server IP First

Before contacting support, get your server IP:

**On Linux/VPS:**
```bash
curl ifconfig.me
```

**On Windows:**
```powershell
Invoke-RestMethod -Uri "https://api.ipify.org"
```

## What to Do Right Now

1. ✅ **Get your server IP** (command above)
2. ✅ **Try to find IP Whitelist section** (Solution 1)
3. ✅ **If not found, try disabling IP whitelist** (Solution 2 - sandbox only)
4. ✅ **If still not working, contact support** (Solution 3)

## After Fixing

Once IP is whitelisted (or whitelisting is disabled), test again:

- Create a new order
- The 403 error should be gone
- Check logs: `grep "Cashfree" logs/requests.log`

---

**Need more help?** See `CASHFREE_IP_WHITELISTING_GUIDE.md` for detailed instructions.

