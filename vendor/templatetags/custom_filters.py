# vendor/templatetags/custom_filters.py
import os
from django import template

register = template.Library()


@register.filter
def basename(value):
    """Return the filename part of a file path (e.g. for FileField.name)."""
    if not value:
        return ""
    return os.path.basename(str(value))

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def replace_underscore(value):
    return value.replace("_", " ").title()

@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, False)


@register.filter
def ledger_debit(amount):
    """For ledger table: show amount if negative (outflow), else None for hyphen."""
    if amount is None:
        return None
    return abs(float(amount)) if float(amount) < 0 else None


@register.filter
def ledger_credit(amount):
    """For ledger table: show amount if positive (inflow), else None for hyphen."""
    if amount is None:
        return None
    return float(amount) if float(amount) > 0 else None


@register.filter
def abs_amount(value):
    """Return absolute value for display (e.g. negative balance as positive with minus prefix)."""
    if value is None:
        return 0
    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return 0


@register.filter
def ledger_type_pill_class(transaction_type):
    """Return Bootstrap-style pill class for transaction type (Transactions UI)."""
    if not transaction_type:
        return "pill-default"
    t = str(transaction_type).lower()
    if t in ("sale", "sale (pos)"):
        return "pill-sale"
    if t in ("purchase",):
        return "pill-purchase"
    if t in ("expense",):
        return "pill-expense"
    return "pill-receipt"  # receipt, payment, deposit, refund, etc.