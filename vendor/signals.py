from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from .models import Sale, Expense, Purchase, Payment, BankLedger, CustomerLedger, VendorLedger

# -------------------------------
# HELPER
# -------------------------------
def update_ledger_on_change(instance, old_instance, ledger_model, amount_field, transaction_type):
    """Update ledger entry if amount or reference changes"""
    try:
        ledger = ledger_model.objects.get(reference_id=instance.id)
    except ledger_model.DoesNotExist:
        # ledger entry doesn't exist, create new
        ledger_model.objects.create(
            customer=getattr(instance, "customer", None),
            vendor=getattr(instance, "vendor", None),
            bank=getattr(instance, "advance_bank", None) or getattr(instance, "bank", None),
            transaction_type=transaction_type,
            reference_id=instance.id,
            description=f"{transaction_type.capitalize()} #{instance.id}",
            amount=getattr(instance, amount_field),
        )
        return

    # update ledger if amount changed
    old_amount = getattr(old_instance, amount_field)
    new_amount = getattr(instance, amount_field)
    if old_amount != new_amount:
        ledger.amount = new_amount if transaction_type != "expense" else -new_amount
        ledger.save()

# -------------------------------
# SALE → Customer & Bank Ledger
# -------------------------------
@receiver(post_save, sender=Sale)
def sale_ledger(sender, instance, created, **kwargs):
    if created:
        # Customer Ledger
        if instance.customer:
            CustomerLedger.objects.create(
                customer=instance.customer,
                transaction_type="sale",
                reference_id=instance.id,
                description=f"Sale #{instance.id}",
                amount=Decimal(instance.total_amount),
            )
        # Bank Ledger
        if instance.advance_bank:
            BankLedger.objects.create(
                bank=instance.advance_bank,
                transaction_type="sale",
                reference_id=instance.id,
                description=f"Sale #{instance.id}",
                amount=Decimal(instance.total_amount)
            )
    else:
        # update existing ledger entries
        old_instance = sender.objects.get(pk=instance.pk)
        if instance.customer:
            update_ledger_on_change(instance, old_instance, CustomerLedger, "total_amount", "sale")
        if instance.advance_bank:
            update_ledger_on_change(instance, old_instance, BankLedger, "total_amount", "sale")

@receiver(post_delete, sender=Sale)
def delete_sale_ledger(sender, instance, **kwargs):
    CustomerLedger.objects.filter(reference_id=instance.id).delete()
    BankLedger.objects.filter(reference_id=instance.id).delete()

# -------------------------------
# PURCHASE → Vendor & Bank Ledger
# -------------------------------
@receiver(post_save, sender=Purchase)
def purchase_ledger(sender, instance, created, **kwargs):
    if created:
        if instance.vendor:
            VendorLedger.objects.create(
                vendor=instance.vendor,
                transaction_type="purchase",
                reference_id=instance.id,
                description=f"Purchase #{instance.id}",
                amount=Decimal(instance.discount_amount or 0) + Decimal(instance.advance_amount or 0),
            )
        if instance.advance_bank and instance.advance_amount:
            BankLedger.objects.create(
                bank=instance.advance_bank,
                transaction_type="purchase",
                reference_id=instance.id,
                description=f"Purchase #{instance.id}",
                amount=-Decimal(instance.advance_amount),
            )
    else:
        old_instance = sender.objects.get(pk=instance.pk)
        if instance.vendor:
            update_ledger_on_change(instance, old_instance, VendorLedger, "advance_amount", "purchase")
        if instance.advance_bank and instance.advance_amount:
            update_ledger_on_change(instance, old_instance, BankLedger, "advance_amount", "purchase")

@receiver(post_delete, sender=Purchase)
def delete_purchase_ledger(sender, instance, **kwargs):
    VendorLedger.objects.filter(reference_id=instance.id).delete()
    BankLedger.objects.filter(reference_id=instance.id).delete()

# -------------------------------
# EXPENSE → Bank Ledger
# -------------------------------
@receiver(post_save, sender=Expense)
def expense_ledger(sender, instance, created, **kwargs):
    if created:
        if instance.bank:
            BankLedger.objects.create(
                bank=instance.bank,
                transaction_type="expense",
                reference_id=instance.id,
                description=f"Expense #{instance.id}",
                amount=-Decimal(instance.amount)
            )
    else:
        old_instance = sender.objects.get(pk=instance.pk)
        if instance.bank:
            update_ledger_on_change(instance, old_instance, BankLedger, "amount", "expense")

@receiver(post_delete, sender=Expense)
def delete_expense_ledger(sender, instance, **kwargs):
    BankLedger.objects.filter(reference_id=instance.id).delete()

# -------------------------------
# PAYMENT → Customer / Vendor Ledger
# -------------------------------
@receiver(post_save, sender=Payment)
def payment_ledger(sender, instance, created, **kwargs):
    if created:
        # Customer
        if instance.customer:
            if instance.type == "received":
                CustomerLedger.objects.create(
                    customer=instance.customer,
                    transaction_type="payment_received",
                    reference_id=instance.id,
                    description=f"Payment Received (#{instance.id})",
                    amount=Decimal(instance.amount),
                )
            elif instance.type == "gave":
                CustomerLedger.objects.create(
                    customer=instance.customer,
                    transaction_type="refund_given",
                    reference_id=instance.id,
                    description=f"Refund Given (#{instance.id})",
                    amount=-Decimal(instance.amount),
                )
        # Vendor
        if instance.vendor:
            if instance.type == "gave":
                VendorLedger.objects.create(
                    vendor=instance.vendor,
                    transaction_type="payment_given",
                    reference_id=instance.id,
                    description=f"Payment Given (#{instance.id})",
                    amount=-Decimal(instance.amount),
                )
            elif instance.type == "received":
                VendorLedger.objects.create(
                    vendor=instance.vendor,
                    transaction_type="refund_received",
                    reference_id=instance.id,
                    description=f"Refund Received (#{instance.id})",
                    amount=Decimal(instance.amount),
                )
    else:
        old_instance = sender.objects.get(pk=instance.pk)
        if instance.customer:
            update_ledger_on_change(instance, old_instance, CustomerLedger, "amount", "payment")
        if instance.vendor:
            update_ledger_on_change(instance, old_instance, VendorLedger, "amount", "payment")

@receiver(post_delete, sender=Payment)
def delete_payment_ledger(sender, instance, **kwargs):
    CustomerLedger.objects.filter(reference_id=instance.id).delete()
    VendorLedger.objects.filter(reference_id=instance.id).delete()
