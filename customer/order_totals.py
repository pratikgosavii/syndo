"""
Invoice-style order totals for print online order:
- Per item: line total = quantity × item price. If this total is less than product sales_price
  (single value, not × quantity), use sales_price as the item total; otherwise use (quantity × item price).
  Then add addon_total for print items.
- If product is GST inclusive (tax_inclusive=True): do not add any tax.
- total_amount = item_total + tax_total + shipping_fee + shipping_tax - delivery_discount - coupon.
"""
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
import logging

logger = logging.getLogger("request")


def get_order_invoice_totals(order):
    """
    Compute item_total, tax_total, total_amount for print online order:
    - Per item: line total = quantity × item price. If line total < product sales_price (single value),
      use sales_price as item total; else use line total. Then add addon_total for print items.
    - total_amount = item_total + tax_total + shipping_fee + shipping_tax - delivery_discount - coupon.

    Expects order with items prefetched: items__product, items__print_job__add_ons.
    Returns dict with keys: item_total, tax_total, total_amount (Decimal).
    """
    from vendor.models import CompanyProfile, TaxSettings

    shipping_fee = Decimal(order.shipping_fee or 0)
    delivery_discount = Decimal(order.delivery_discount_amount or 0)
    coupon = Decimal(order.coupon or 0)

    # Determine same_state for CGST/SGST vs IGST and composite scheme (no GST under composite)
    vendor_state_name = None
    first_item = order.items.first()
    vendor_user = None
    if first_item and first_item.product and first_item.product.user:
        vendor_user = first_item.product.user
        company_profile = CompanyProfile.objects.filter(user=vendor_user).first()
        if company_profile:
            if getattr(company_profile, "billing_state", None):
                vendor_state_name = str(company_profile.billing_state)
            elif getattr(company_profile, "state", None):
                vendor_state_name = str(company_profile.state)
    customer_state_name = None
    if order.address and getattr(order.address, "state", None):
        customer_state_name = str(order.address.state)
    same_state = bool(
        vendor_state_name and customer_state_name
        and vendor_state_name.strip().lower() == customer_state_name.strip().lower()
    )

    # Composite scheme: vendor opts out of GST - do not calculate or add any tax
    composite_scheme = False
    try:
        if vendor_user and hasattr(vendor_user, "tax_settings") and vendor_user.tax_settings.composite_scheme:
            composite_scheme = True
    except Exception:
        composite_scheme = False

    sum_taxable = Decimal(0)
    tax_total = Decimal(0)

    for item in order.items.all():
        if not item.product:
            continue
        unit_price = Decimal(item.price or 0)
        quantity = int(item.quantity or 0)
        sales_price = getattr(item.product, "sales_price", None)
        sales_price_val = Decimal(str(sales_price)) if sales_price is not None else None

        addon_total = Decimal(0)
        print_job = getattr(item, "print_job", None)
        item_line_total = unit_price * quantity
        try:
            if print_job and getattr(print_job, "total_amount", None):
                item_line_total = Decimal(str(print_job.total_amount or 0))
            if print_job and hasattr(print_job, "add_ons"):
                for addon in print_job.add_ons.all():
                    addon_total += Decimal(str(getattr(addon, "price_per_unit", 0) or 0))
        except Exception:
            pass

        # If (quantity × item price) total is less than product sales_price, use sales_price as item total.
        if sales_price_val is not None and item_line_total < sales_price_val:
            base_total = sales_price_val
        else:
            base_total = item_line_total
        gross_line_total = base_total + addon_total

        # Match POS GST behavior:
        # - Inclusive: split gross line total into taxable value + GST
        # - Exclusive: keep line total as taxable value and add GST on top
        taxable_val = gross_line_total
        line_tax = Decimal("0.00")
        if not composite_scheme:
            gst_rate = Decimal(str(getattr(item.product, "gst", 0) or 0))
            tax_inclusive = bool(getattr(item.product, "tax_inclusive", False))
            if gst_rate > 0:
                if tax_inclusive:
                    divisor = Decimal("1") + (gst_rate / Decimal("100"))
                    taxable_val = (gross_line_total / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    line_tax = (gross_line_total - taxable_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    taxable_val = gross_line_total
                    line_tax = (taxable_val * gst_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        sum_taxable += taxable_val
        tax_total += line_tax

    item_total = sum_taxable
    total_amount = item_total + tax_total + shipping_fee - delivery_discount - coupon
    total_amount = total_amount.to_integral_value(rounding=ROUND_CEILING).quantize(Decimal("0.01"))
    return {
        "item_total": item_total,
        "tax_total": tax_total,
        "total_amount": total_amount,
    }
