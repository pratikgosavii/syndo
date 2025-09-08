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
from .models import *


@receiver(post_save, sender=Sale)
@receiver(post_save, sender=Expense)
@receiver(post_save, sender=Purchase)
def create_bank_ledger(sender, instance, created, **kwargs):
    """
    Creates a BankLedger entry automatically for Sale, Expense, and Purchase.
    Stores the instance.id as reference_id.
    """

    if not created:
        return  # only create entry on new record

    if sender == Sale:
        if instance.advance_bank:
            BankLedger.objects.create(
                bank=instance.advance_bank,
                transaction_type="sale",
                reference_id=instance.id,
                description=f"Sale #{instance.id}",
                amount=Decimal(instance.total_amount)  # inflow (+)
            )

    elif sender == Expense:
        if instance.bank:
            BankLedger.objects.create(
                bank=instance.bank,
                transaction_type="expense",
                reference_id=instance.id,
                description=f"Expense #{instance.id}",
                amount=-Decimal(instance.amount)  # outflow (–)
            )

    elif sender == Purchase:
        if instance.advance_bank and instance.advance_amount:
            BankLedger.objects.create(
                bank=instance.advance_bank,
                transaction_type="purchase",
                reference_id=instance.id,
                description=f"Purchase #{instance.id}",
                amount=-Decimal(instance.advance_amount)  # outflow (–)
            )






# ---- SALE → Customer Ledger ----
@receiver(post_save, sender=Sale)
def create_sale_customer_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.customer:
        CustomerLedger.objects.create(
            customer=instance.customer,
            transaction_type="sale",
            reference_id=instance.id,
            description=f"Sale #{instance.id}",
            amount=Decimal(instance.total_amount),
        )


# ---- PURCHASE → Vendor Ledger ----
@receiver(post_save, sender=Purchase)
def create_purchase_vendor_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.vendor:
        VendorLedger.objects.create(
            vendor=instance.vendor,
            transaction_type="purchase",
            reference_id=instance.id,
            description=f"Purchase #{instance.id}",
            amount=Decimal(instance.discount_amount or 0) + Decimal(instance.advance_amount or 0),
        )


# ---- PAYMENT → Customer Ledger / Vendor Ledger ----
@receiver(post_save, sender=Payment)
def create_payment_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    # Customer Payments
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

    # Vendor Payments
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