import os
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.db.models import FileField, ImageField


def delete_file(path):
    """Delete file from filesystem."""
    if path and os.path.isfile(path):
        os.remove(path)


@receiver(pre_save)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem when updating with new file.
    Applies to all models with FileField/ImageField.
    """
    if not instance.pk:  # new object, skip
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    for field in sender._meta.get_fields():
        if isinstance(field, (FileField, ImageField)):
            old_file = getattr(old_instance, field.name)
            new_file = getattr(instance, field.name)
            if old_file and old_file != new_file:
                delete_file(old_file.path)


@receiver(post_delete)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem when model is deleted.
    Applies to all models with FileField/ImageField.
    """
    for field in sender._meta.get_fields():
        if isinstance(field, (FileField, ImageField)):
            file_field = getattr(instance, field.name)
            if file_field:
                delete_file(file_field.path)





from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Sale, Purchase, Expense, Payment, BankLedger, CustomerLedger, VendorLedger, vendor_bank, vendor_customers, vendor_vendors


from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Sale, Purchase, Expense, Payment, BankLedger, CustomerLedger, VendorLedger, vendor_bank, vendor_customers, vendor_vendors

def create_ledger(parent, ledger_model, transaction_type, reference_id, amount, description=""):
    opening_balance = parent.balance or 0
    balance_after = opening_balance + amount
    ledger_model.objects.create(
        **{
            ledger_model.__name__.replace("Ledger", "").lower(): parent,
            "transaction_type": transaction_type,
            "reference_id": reference_id,
            "description": description,
            "opening_balance": opening_balance,
            "amount": amount,
            "balance_after": balance_after,
        }
    )
    # Update parent balance
    parent.balance = balance_after
    parent.save()


# -------------------------------
# SALE → Customer & Bank Ledger
# -------------------------------
@receiver(post_save, sender=Sale)
def sale_ledger(sender, instance, created, **kwargs):
    if not created:
        return
    # Customer ledger
    if instance.customer:
        create_ledger(instance.customer, CustomerLedger, "sale", instance.id, int(instance.total_amount), f"Sale #{instance.id}")
    # Bank ledger
    if instance.advance_bank:
        create_ledger(instance.advance_bank, BankLedger, "sale", instance.id, int(instance.total_amount), f"Sale #{instance.id}")


# -------------------------------
# PURCHASE → Vendor & Bank Ledger
# -------------------------------
@receiver(post_save, sender=Purchase)
def purchase_ledger(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.vendor:
        amt = int(instance.discount_amount or 0) + int(instance.advance_amount or 0)
        create_ledger(instance.vendor, VendorLedger, "purchase", instance.id, amt, f"Purchase #{instance.id}")
    if instance.advance_bank and instance.advance_amount:
        create_ledger(instance.advance_bank, BankLedger, "purchase", instance.id, -int(instance.advance_amount), f"Purchase #{instance.id}")


# -------------------------------
# EXPENSE → Bank Ledger
# -------------------------------
@receiver(post_save, sender=Expense)
def expense_ledger(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.bank:
        create_ledger(instance.bank, BankLedger, "expense", instance.id, -int(instance.amount), f"Expense #{instance.id}")


# -------------------------------
# PAYMENT → Customer / Vendor Ledger
# -------------------------------
@receiver(post_save, sender=Payment)
def payment_ledger(sender, instance, created, **kwargs):
    if not created:
        return
    amt = int(instance.amount)
    if instance.customer:
        if instance.type == "received":
            create_ledger(instance.customer, CustomerLedger, "payment", instance.id, amt, f"Payment Received #{instance.id}")
        elif instance.type == "gave":
            create_ledger(instance.customer, CustomerLedger, "payment", instance.id, -amt, f"Refund Given #{instance.id}")
    if instance.vendor:
        if instance.type == "gave":
            create_ledger(instance.vendor, VendorLedger, "payment", instance.id, -amt, f"Payment Given #{instance.id}")
        elif instance.type == "received":
            create_ledger(instance.vendor, VendorLedger, "payment", instance.id, amt, f"Refund Received #{instance.id}")
