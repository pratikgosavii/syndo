from django import template
from num2words import num2words

register = template.Library()

@register.filter
def in_words(value):
    """
    Convert a numeric amount to Indian Rupees in words.
    Example: 275 -> "Two Hundred Seventy Five Rupees Only"
    """
    try:
        words = num2words(value, lang="en_IN").title()
        return f"{words} Rupees Only"
    except Exception:
        return value
