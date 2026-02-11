# vendor/templatetags/custom_filters.py
from django import template

register = template.Library()

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