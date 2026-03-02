"""
Invoice-style order totals for print online order:
- Per item: line total = quantity × item price. If this total is less than product sales_price
  (single value, not × quantity), use sales_price as the item total; otherwise use (quantity × item price).
  Then add addon_total for print items.
- If product is GST inclusive (tax_inclusive=True): do not add any tax.
- total_amount = item_total + tax_total + shipping_fee + shipping_tax - delivery_discount - coupon.
"""
from decimal import Decimal
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
    from vendor.models import CompanyProfile

    shipping_fee = Decimal(order.shipping_fee or 0)
    delivery_discount = Decimal(order.delivery_discount_amount or 0)
    coupon = Decimal(order.coupon or 0)

    # Determine same_state for CGST/SGST vs IGST
    vendor_state_name = None
    first_item = order.items.first()
    if first_item and first_item.product and first_item.product.user:
        company_profile = CompanyProfile.objects.filter(user=first_item.product.user).first()
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

    sum_taxable = Decimal(0)
    total_sgst = Decimal(0)
    total_cgst = Decimal(0)
    total_igst = Decimal(0)
    any_non_inclusive = False  # track if any line is tax-exclusive

    for item in order.items.all():
        if not item.product:
            continue
        unit_price = Decimal(item.price or 0)
        quantity = int(item.quantity or 0)
        # Line total = quantity × item price (not quantity × sales_price).
        item_line_total = unit_price * quantity
        sales_price = getattr(item.product, "sales_price", None)
        sales_price_val = Decimal(str(sales_price)) if sales_price is not None else None

        addon_total = Decimal(0)
        print_job = getattr(item, "print_job", None)
        try:
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
        taxable_val = base_total + addon_total

        sum_taxable += taxable_val

        # For print order: if product is GST inclusive, do not apply tax (price already includes GST).
        tax_inclusive = bool(getattr(item.product, "tax_inclusive", False))
        if not tax_inclusive:
            any_non_inclusive = True

            sgst_rate = Decimal(getattr(item.product, "sgst_rate", None) or 9)
            cgst_rate = Decimal(getattr(item.product, "cgst_rate", None) or 9)
            sgst_amt = (taxable_val * sgst_rate / Decimal(100)).quantize(Decimal("0.01"))
            cgst_amt = (taxable_val * cgst_rate / Decimal(100)).quantize(Decimal("0.01"))
            total_sgst += sgst_amt
            total_cgst += cgst_amt
            if same_state:
                pass  # item_tax = sgst_amt + cgst_amt already counted
            else:
                item_tax = (
                    taxable_val * Decimal(getattr(item.product, "gst", 0) or 0) / Decimal(100)
                ).quantize(Decimal("0.01"))
                total_igst += item_tax

    item_total = sum_taxable
    tax_total = total_sgst + total_cgst + total_igst

    # Shipping tax (18% GST on shipping)
    shipping_taxable = shipping_fee / Decimal("1.18") if shipping_fee > 0 else Decimal(0)
    shipping_cgst = Decimal(0)
    shipping_sgst = Decimal(0)
    shipping_igst = Decimal(0)

    # Only add GST on shipping when at least one product is tax-exclusive.
    if shipping_fee > 0 and any_non_inclusive:
        if same_state:
            shipping_cgst = (shipping_taxable * Decimal("9") / Decimal("100")).quantize(Decimal("0.01"))
            shipping_sgst = (shipping_taxable * Decimal("9") / Decimal("100")).quantize(Decimal("0.01"))
        else:
            shipping_igst = (shipping_taxable * Decimal("18") / Decimal("100")).quantize(Decimal("0.01"))

    total_amount = (
        item_total + tax_total + shipping_fee + shipping_cgst + shipping_sgst + shipping_igst
        - delivery_discount - coupon
    )
    return {
        "item_total": item_total,
        "tax_total": tax_total,
        "total_amount": total_amount,
    }
