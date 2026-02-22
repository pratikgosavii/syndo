"""
Invoice-style order totals for print online order:
- Per item: if item total < sales_price value → use sales_value + addons as item total.
- If item total >= sales_price → use total only (no addons).
Then item_total, tax_total, total_amount (incl. shipping tax) for consistency with invoice PDF.
"""
from decimal import Decimal
import logging

logger = logging.getLogger("request")


def get_order_invoice_totals(order):
    """
    Compute item_total, tax_total, total_amount for print online order:
    - Per item: if (price*qty) < (sales_price*qty) → taxable = sales_price*qty + addon_total.
    - If (price*qty) >= (sales_price*qty) → taxable = price*qty only (no addons).
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

    for item in order.items.all():
        if not item.product:
            continue
        unit_price = Decimal(item.price or 0)
        quantity = int(item.quantity or 0)
        item_price_total = unit_price * quantity
        sales_price = getattr(item.product, "sales_price", None)
        sales_price_item = (Decimal(str(sales_price)) * quantity) if sales_price is not None else None

        addon_total = Decimal(0)
        try:
            print_job = getattr(item, "print_job", None)
            if print_job and hasattr(print_job, "add_ons"):
                for addon in print_job.add_ons.all():
                    addon_total += Decimal(str(getattr(addon, "price_per_unit", 0) or 0))
        except Exception:
            pass

        if sales_price_item is not None and item_price_total < sales_price_item:
            taxable_val = sales_price_item + addon_total
            msg = (
                f"[order_totals] order_id={getattr(order, 'order_id', order.id)} item_id={item.id} "
                f"product={getattr(item.product, 'name', '')} item_price_total={item_price_total} < "
                f"sales_price_item={sales_price_item} → taxable_val=sales_price+addons={taxable_val} (addon_total={addon_total})"
            )
            print(msg)
            logger.info(msg)
        else:
            # total >= sales price: keep total only (no addons)
            taxable_val = item_price_total
            msg = (
                f"[order_totals] order_id={getattr(order, 'order_id', order.id)} item_id={item.id} "
                f"product={getattr(item.product, 'name', '')} item_price_total={item_price_total} >= "
                f"sales_price_item={sales_price_item} → taxable_val=total_only={taxable_val}"
            )
            print(msg)
            logger.info(msg)
        sum_taxable += taxable_val

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
    if shipping_fee > 0:
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
