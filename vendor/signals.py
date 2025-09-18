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
from .models import BankTransfer, CashTransfer, Sale, Purchase, Expense, Payment, BankLedger, CustomerLedger,   CashLedger, VendorLedger, vendor_bank, vendor_customers, vendor_vendors


from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Sale, Purchase, Expense, Payment, BankLedger, CustomerLedger, VendorLedger, vendor_bank, vendor_customers, vendor_vendors

from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

# -------------------------------
# LEDGER CREATION HELPER
# -------------------------------
def create_ledger(parent, ledger_model, transaction_type, reference_id, amount, description="", user=None):
    """
    Generic ledger creation function that ensures all balances and amounts are handled as Decimal.
    """
    opening_balance = Decimal(parent.balance or 0) if parent else Decimal(0)   # >>> updated to support CashLedger
    amount = Decimal(amount or 0)
    balance_after = opening_balance + amount

    # >>> NEW : Special case for CashLedger (no FK field)
    if ledger_model.__name__ == "CashLedger":
        ledger_model.objects.create(
            user=user,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
            opening_balance=opening_balance,
            amount=amount,
            balance_after=balance_after,
        )
    else:
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

        # Update parent balance (bank, customer, vendor)
        parent.balance = balance_after
        parent.save()


# -------------------------------
# SALE → Customer & Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Sale)
def sale_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    # Customer ledger
    if instance.customer:
        create_ledger(
            instance.customer,
            CustomerLedger,
            "sale",
            instance.id,
            instance.total_amount,
            f"Sale #{instance.id}"
        )

    # Bank ledger
    if instance.advance_bank:
        create_ledger(
            instance.advance_bank,
            BankLedger,
            "sale",
            instance.id,
            instance.total_amount,
            f"Sale #{instance.id}"
        )

    # >>> NEW : Cash ledger
    if getattr(instance, "is_cash", False):
        create_ledger(
            None,
            CashLedger,
            "sale",
            instance.id,
            instance.total_amount,
            f"Cash Sale #{instance.id}",
            user=instance.user  # >>> NEW
        )


# -------------------------------
# PURCHASE → Vendor & Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Purchase)
def purchase_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.vendor:
        amt = (instance.discount_amount or Decimal(0)) + (instance.advance_amount or Decimal(0))
        create_ledger(
            instance.vendor,
            VendorLedger,
            "purchase",
            instance.id,
            amt,
            f"Purchase #{instance.id}"
        )

    if instance.advance_bank and instance.advance_amount:
        create_ledger(
            instance.advance_bank,
            BankLedger,
            "purchase",
            instance.id,
            -(instance.advance_amount or Decimal(0)),
            f"Purchase #{instance.id}"
        )

    # >>> NEW : Cash ledger
    if getattr(instance, "is_cash", False) and instance.advance_amount:
        create_ledger(
            None,
            CashLedger,
            "purchase",
            instance.id,
            -(instance.advance_amount or Decimal(0)),
            f"Cash Purchase #{instance.id}",
            user=instance.user  # >>> NEW
        )


# -------------------------------
# EXPENSE → Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Expense)
def expense_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.bank:
        create_ledger(
            instance.bank,
            BankLedger,
            "expense",
            instance.id,
            -(instance.amount or Decimal(0)),
            f"Expense #{instance.id}"
        )

    # >>> NEW : Cash ledger
    if getattr(instance, "is_cash", False):
        create_ledger(
            None,
            CashLedger,
            "expense",
            instance.id,
            -(instance.amount or Decimal(0)),
            f"Cash Expense #{instance.id}",
            user=instance.user  # >>> NEW
        )


# -------------------------------
# PAYMENT → Customer / Vendor Ledger
# -------------------------------
@receiver(post_save, sender=Payment)
def payment_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    amt = Decimal(instance.amount or 0)

    if instance.customer:
        if instance.type == "received":
            create_ledger(
                instance.customer,
                CustomerLedger,
                "payment",
                instance.id,
                amt,
                f"Payment Received #{instance.id}"
            )
        elif instance.type == "gave":
            create_ledger(
                instance.customer,
                CustomerLedger,
                "payment",
                instance.id,
                -amt,
                f"Refund Given #{instance.id}"
            )

    if instance.vendor:
        if instance.type == "gave":
            create_ledger(
                instance.vendor,
                VendorLedger,
                "payment",
                instance.id,
                -amt,
                f"Payment Given #{instance.id}"
            )
        elif instance.type == "received":
            create_ledger(
                instance.vendor,
                VendorLedger,
                "payment",
                instance.id,
                amt,
                f"Refund Received #{instance.id}"
            )


# -------------------------------
# CASH TRANSFER → Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=CashTransfer)
def cash_transfer_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.bank_account and instance.amount:
        # >>> NEW : Deduct from Cash
        create_ledger(
            None,
            CashLedger,
            "withdrawal",
            instance.id,
            -(instance.amount or Decimal(0)),
            f"Cash to {instance.bank_account.bank_name}"
        )

        # Bank ledger (already in your code)
        create_ledger(
            instance.bank_account,
            BankLedger,
            "cash_transfer",
            instance.id,
            instance.amount,
            f"Cash deposited to {instance.bank_account.bank_name}"
        )


# -------------------------------
# BANK TRANSFER → Bank Ledger
# -------------------------------
@receiver(post_save, sender=BankTransfer)
def bank_transfer_ledger(sender, instance, created, **kwargs):
    if not created:
        return

    amt = Decimal(instance.amount or 0)

    # Deduct from source bank
    if instance.from_bank:
        create_ledger(
            instance.from_bank,
            BankLedger,
            "bank_transfer_out",
            instance.id,
            -amt,
            f"Transfer to {instance.to_bank.name}"
        )

    # Add to destination bank
    if instance.to_bank:
        create_ledger(
            instance.to_bank,
            BankLedger,
            "bank_transfer_in",
            instance.id,
            amt,
            f"Transfer from {instance.from_bank.name}"
        )