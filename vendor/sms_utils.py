"""
SMS utility functions for sending SMS via MSGClub API
"""
import http.client
import json
import logging
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms_via_msgclub(phone_number, message):
    """
    Send SMS via MSGClub API
    
    Args:
        phone_number: Customer phone number (string)
        message: SMS message content (string)
    
    Returns:
        tuple: (success: bool, response_data: dict or error_message: str)
    """
    try:
        from django.conf import settings
        
        # Get API credentials from settings
        api_key = getattr(settings, 'SMS_API_KEY', '')
        api_host = getattr(settings, 'SMS_API_URL', 'msg.msgclub.net')
        
        if not api_key:
            error_msg = "SMS API key not configured"
            logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
            return False, error_msg
        
        conn = http.client.HTTPConnection(api_host)
        
        headers = {
            'Cache-Control': "no-cache"
        }
        
        # Using the format provided by user - comma-separated path
        # Add query parameters for phone_number, message, and api_key
        # sender_id is optional - only add if provided
        import urllib.parse
        endpoint = "rest,services,sendSMS,sendGroupSms"
        params = {
            'mobile': phone_number,
            'message': message,
            'api_key': api_key,
        }
       
        
        query_string = urllib.parse.urlencode(params)
        full_endpoint = f"{endpoint}?{query_string}"
        
        conn.request("GET", full_endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()
        response_text = data.decode("utf-8")
        
        conn.close()
        
        # Parse response (adjust based on actual API response format)
        # For now, assume success if we get a response
        if response_text:
            try:
                response_data = json.loads(response_text)
                logger.info(f"SMS sent successfully to {phone_number}. Response: {response_data}")
                return True, response_data
            except json.JSONDecodeError:
                # If response is not JSON, treat as success if it's not an error
                logger.info(f"SMS sent successfully to {phone_number}. Response: {response_text}")
                return True, response_text
        else:
            error_msg = "Empty response from SMS API"
            logger.error(f"Failed to send SMS to {phone_number}: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        logger.error(f"Error sending SMS to {phone_number}: {str(e)}")
        return False, str(e)


def send_sale_sms(sale, invoice_type='invoice'):
    """
    Send SMS for a sale based on invoice type and SMS settings
    
    Args:
        sale: Sale instance
        invoice_type: Type of invoice ('invoice' or other types like 'quotation', 'sales_order', etc.)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from .models import SMSSetting, vendor_customers
    
    # Check if sale has customer
    if not sale.customer:
        logger.warning(f"SMS not sent for sale {sale.id}: No customer associated with sale")
        return False, "No customer associated with sale"
    
    # Check if user has SMS settings
    if not sale.user:
        logger.warning(f"SMS not sent for sale {sale.id}: No user associated with sale")
        return False, "No user associated with sale"
    
    try:
        sms_setting, _ = SMSSetting.objects.get_or_create(user=sale.user)
    except Exception as e:
        error_msg = f"Error getting SMS settings: {str(e)}"
        logger.error(f"SMS not sent for sale {sale.id}: {error_msg}")
        return False, error_msg
    
    # Determine which setting to check based on invoice type
    should_send = False
    setting_type = ""
    
    if invoice_type == 'invoice':
        # Check enable_purchase_message for invoice type
        should_send = sms_setting.enable_purchase_message
        setting_type = "purchase message"
    else:
        # Check enable_quote_message for all other types
        should_send = sms_setting.enable_quote_message
        setting_type = "quote message"
    
    if not should_send:
        logger.info(f"SMS not sent for sale {sale.id} (invoice_type: {invoice_type}): {setting_type.capitalize()} is disabled")
        return False, f"{setting_type.capitalize()} is disabled"
    
    # Check if there are available credits
    if sms_setting.available_credits <= 0:
        logger.warning(f"SMS not sent for sale {sale.id}: No SMS credits available (available: {sms_setting.available_credits})")
        return False, "No SMS credits available"
    
    # Get customer phone number
    customer = sale.customer
    phone_number = getattr(customer, 'contact', None)
    
    if not phone_number:
        logger.warning(f"SMS not sent for sale {sale.id}: Customer phone number not found for customer {customer.id}")
        return False, "Customer phone number not found"
    
    # Clean phone number (remove any non-digit characters except +)
    import re
    phone_number = re.sub(r'[^\d+]', '', str(phone_number))
    
    # Prepare SMS message
    invoice_number = sale.invoice_number or f"#{sale.id}"
    total_amount = sale.total_amount or 0
    
    if invoice_type == 'invoice':
        message = f"Dear {customer.name}, Your purchase invoice {invoice_number} for ₹{total_amount} has been generated. Thank you for your business!"
    else:
        invoice_type_display = invoice_type.replace('_', ' ').title()
        message = f"Dear {customer.name}, Your {invoice_type_display} {invoice_number} for ₹{total_amount} has been prepared. Please review."
    
    # Send SMS
    logger.info(f"Attempting to send SMS for sale {sale.id} to customer {customer.name} ({phone_number}), invoice_type: {invoice_type}")
    success, response = send_sms_via_msgclub(phone_number, message)
    
    if success:
        # Update SMS credits (deduct 1 credit for SMS sent)
        sms_setting.available_credits = max(Decimal('0'), sms_setting.available_credits - Decimal('1'))
        sms_setting.used_credits += Decimal('1')
        sms_setting.save(update_fields=['available_credits', 'used_credits'])
        
        logger.info(f"SMS sent successfully for sale {sale.id} to {phone_number}. Remaining credits: {sms_setting.available_credits}")
        return True, "SMS sent successfully"
    else:
        error_msg = f"Failed to send SMS: {response}"
        logger.error(f"SMS failed for sale {sale.id} to {phone_number}: {error_msg}")
        return False, error_msg

