"""
Utility functions for generating document serial numbers.
Format: YY-YY/MM/MONTH/PREFIX-0001
Example: 24-25/05/NOV/SAL-0001
"""
from datetime import datetime
from django.db.models import Max
from django.utils import timezone


def get_financial_year(date=None):
    """
    Get financial year in format YY-YY (e.g., 24-25 for FY 2024-25)
    Financial year runs from April to March
    """
    if date is None:
        date = timezone.now().date()
    
    year = date.year
    month = date.month
    
    # If month is April (4) or later, it's the current FY
    # If month is Jan-Mar, it's the previous FY
    if month >= 4:
        # FY 2024-25 means April 2024 to March 2025
        start_year = year % 100
        end_year = (year + 1) % 100
    else:
        # FY 2023-24 means April 2023 to March 2024
        start_year = (year - 1) % 100
        end_year = year % 100
    
    return f"{start_year:02d}-{end_year:02d}"


def get_month_info(date=None):
    """
    Get month number and abbreviated month name
    Returns: (month_number, month_name) e.g., (05, 'NOV')
    """
    if date is None:
        date = timezone.now().date()
    
    month_number = date.month
    month_names = [
        '', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
        'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
    ]
    month_name = month_names[month_number]
    
    return f"{month_number:02d}", month_name


def generate_serial_number(prefix, model_class, date=None, user=None, filter_kwargs=None):
    """
    Generate serial number in format: YY-YY/MM/MONTH/PREFIX-0001
    
    Args:
        prefix: Document prefix (e.g., 'SAL', 'PUR', 'ONL')
        model_class: Django model class to query for last number
        date: Date to use for FY and month (defaults to today)
        user: Optional user to filter by
        filter_kwargs: Additional filter kwargs for the query
    
    Returns:
        Serial number string (e.g., '24-25/05/NOV/SAL-0001')
    """
    if date is None:
        date = timezone.now().date()
    
    fy = get_financial_year(date)
    month_num, month_name = get_month_info(date)
    
    # Build filter for finding last document in current FY and month
    filter_dict = {}
    if user:
        filter_dict['user'] = user
    if filter_kwargs:
        filter_dict.update(filter_kwargs)
    
    # Get the field name that stores the serial number
    # Try common field names
    serial_field = None
    for field_name in ['serial_number', 'invoice_number', 'purchase_code', 'order_id', 'payment_number']:
        if hasattr(model_class, field_name):
            serial_field = field_name
            break
    
    if not serial_field:
        # Fallback: use id
        last_doc = model_class.objects.filter(**filter_dict).order_by('-id').first()
        last_number = last_doc.id if last_doc else 0
    else:
        # Find last document with matching FY and month
        # Pattern: YY-YY/MM/MONTH/PREFIX-XXXX
        pattern_start = f"{fy}/{month_num}/{month_name}/{prefix}-"
        
        # Get all documents matching the pattern
        all_docs = model_class.objects.filter(**filter_dict)
        matching_docs = []
        
        for doc in all_docs:
            serial_value = getattr(doc, serial_field, None)
            if serial_value and serial_value.startswith(pattern_start):
                try:
                    # Extract number part
                    number_part = serial_value.split('-')[-1]
                    number = int(number_part)
                    matching_docs.append((doc, number))
                except (ValueError, IndexError):
                    continue
        
        if matching_docs:
            last_number = max(matching_docs, key=lambda x: x[1])[1]
        else:
            last_number = 0
    
    # Generate new serial number
    next_number = last_number + 1
    serial_number = f"{fy}/{month_num}/{month_name}/{prefix}-{next_number:04d}"
    
    return serial_number

