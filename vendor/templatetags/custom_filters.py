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
    """Return pill class for transaction type (light bg + dark text, cash ledger style)."""
    if not transaction_type:
        return "pill-default"
    t = str(transaction_type).lower()
    if t in ("sale", "sale (pos)"):
        return "pill-sale"
    if t in ("purchase",):
        return "pill-purchase"
    if t in ("expense",):
        return "pill-expense"
    if t in ("cash_transfer", "transfer", "transfered"):
        return "pill-transfer"
    if t in ("adjustment",):
        return "pill-adjustment"
    if t in ("deposit",):
        return "pill-deposit"
    if t in ("withdrawal",):
        return "pill-withdrawal"
    return "pill-receipt"


@register.filter
def cash_reference_display(entry):
    """Return display label for cash ledger reference (e.g. PUR-2026-057, INV-2026-086)."""
    return ledger_reference_display(entry)


@register.filter
def ledger_reference_display(entry):
    """Return display label for any ledger reference (e.g. EXP-0016, PAY-0068, PUR-2026-057)."""
    if not entry:
        return "–"
    from vendor.signals import _get_invoice_label
    return _get_invoice_label(entry.transaction_type, entry.reference_id) or "–"