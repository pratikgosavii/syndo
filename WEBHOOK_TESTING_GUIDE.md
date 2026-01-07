# Cashfree Webhook Testing Guide

## How to Check if Webhook is Working

### 1. Check Webhook Logs

The webhook logs are written to: `logs/webhook.log`

**On Windows (local):**
```powershell
# Navigate to project directory
cd "C:\Users\Pratik Gosavi\OneDrive\Desktop\hope again\syndo"

# View recent webhook logs (last 50 lines)
Get-Content logs\webhook.log -Tail 50

# Or watch logs in real-time (if using PowerShell 5.1+)
Get-Content logs\webhook.log -Wait -Tail 20
```

**On Linux/VPS (production):**
```bash
# View recent webhook logs
tail -f logs/webhook.log

# Or view last 100 lines
tail -n 100 logs/webhook.log

# Search for specific order_id
grep "25-26-01-JAN-ONL-0010" logs/webhook.log
```

### 2. What to Look For in Logs

#### ✅ **Successful Webhook Processing:**
```
[CASHFREE_WEBHOOK] ========== WEBHOOK RECEIVED ==========
[CASHFREE_WEBHOOK] Method: POST
[CASHFREE_WEBHOOK] Signature present: True
[CASHFREE_WEBHOOK] Webhook version: 2023-08-01
[CASHFREE_WEBHOOK] Signature verified successfully
[CASHFREE_WEBHOOK] Event type: PAYMENT_SUCCESS_WEBHOOK
[CASHFREE_WEBHOOK] Extracted order_id: 25-26-01-JAN-ONL-0010
[CASHFREE_WEBHOOK] Extracted status: SUCCESS
[CASHFREE_WEBHOOK] Order found by cashfree_order_id: 25-26/01/JAN/ONL-0010 (ID: 123)
[CASHFREE_WEBHOOK] Payment successful! Marking order as paid
[CASHFREE_WEBHOOK] Order updated successfully. New status: cashfree_status=SUCCESS, is_paid=True
[CASHFREE_WEBHOOK] ========== WEBHOOK PROCESSED SUCCESSFULLY ==========
```

#### ⚠️ **Signature Verification Failed (but proceeding in test mode):**
```
[CASHFREE_WEBHOOK] Invalid signature. Expected: j2SNSgcNXTVwQ/DZbW/8..., Got: w2tuVfqEzUdxtovQN6co...
[CASHFREE_WEBHOOK] Signature mismatch, but proceeding in test mode
```
**Action:** Check your `CASHFREE_WEBHOOK_SECRET` environment variable matches Cashfree dashboard.

#### ❌ **Order Not Found:**
```
[CASHFREE_WEBHOOK] Order not found for order_id: 25-26-01-JAN-ONL-0010
[CASHFREE_WEBHOOK] Tried: cashfree_order_id=25-26-01-JAN-ONL-0010, order_id=25-26-01-JAN-ONL-0010
```
**Action:** Verify the order exists in your database and `cashfree_order_id` matches.

### 3. Check Order Status in Database

**Using Django Shell:**
```python
python manage.py shell

from customer.models import Order

# Find order by order_id
order = Order.objects.get(order_id="25-26/01/JAN/ONL-0010")
print(f"Order ID: {order.order_id}")
print(f"Cashfree Order ID: {order.cashfree_order_id}")
print(f"Status: {order.status}")
print(f"Is Paid: {order.is_paid}")
print(f"Cashfree Status: {order.cashfree_status}")
print(f"Payment Mode: {order.payment_mode}")
```

### 4. Test Webhook Manually (Optional)

You can test the webhook endpoint manually using curl or Postman:

```bash
curl -X POST https://vendor.svindo.com/cashfree/webhook/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Version: 2023-08-01" \
  -H "X-Webhook-Signature: YOUR_SIGNATURE" \
  -H "X-Webhook-Timestamp: 1767785899837" \
  -d '{
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
  }'
```

### 5. Check Cashfree Dashboard

1. Go to Cashfree Dashboard → Webhooks
2. Check webhook delivery status
3. View webhook payloads sent by Cashfree
4. Check for any failed delivery attempts

### 6. Monitor Real-time Logs (Production)

**On VPS, use `tail -f` to watch logs in real-time:**
```bash
tail -f logs/webhook.log | grep CASHFREE_WEBHOOK
```

### 7. Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| No logs appearing | Check file permissions: `chmod 666 logs/webhook.log` |
| Signature verification fails | Verify `CASHFREE_WEBHOOK_SECRET` matches Cashfree dashboard |
| Order not found | Check `cashfree_order_id` in Order model matches webhook payload |
| 404 error | Verify webhook URL is correct: `/cashfree/webhook/` |
| 500 error | Check Django error logs: `logs/requests.log` or console output |

### 8. Verify Order Update After Webhook

After a successful webhook, verify the order was updated:

```python
# In Django shell
from customer.models import Order

order = Order.objects.get(order_id="YOUR_ORDER_ID")
assert order.is_paid == True, "Order should be marked as paid"
assert order.cashfree_status == "SUCCESS", "Cashfree status should be SUCCESS"
assert order.payment_mode == "Cashfree", "Payment mode should be Cashfree"
print("✅ Order updated correctly!")
```

### 9. Check Console Output

The webhook also logs to console/stderr, so if you're running Django with `python manage.py runserver`, you'll see logs in the terminal as well.

---

## Quick Test Command

**Windows PowerShell:**
```powershell
Get-Content logs\webhook.log -Tail 30 | Select-String "CASHFREE_WEBHOOK"
```

**Linux/VPS:**
```bash
tail -n 30 logs/webhook.log | grep CASHFREE_WEBHOOK
```

This will show the last 30 lines containing "CASHFREE_WEBHOOK" from the log file.

