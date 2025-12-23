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
from .models import BankTransfer, CashTransfer, Sale, Purchase, Expense, Payment, BankLedger, CustomerLedger,   CashLedger, VendorLedger, vendor_bank, vendor_customers, vendor_vendors, pos_wholesale


from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import logging
from .models import Sale, Purchase, Expense, Payment, BankLedger, CustomerLedger, VendorLedger, vendor_bank, vendor_customers, vendor_vendors

from decimal import Decimal
from django.db.models.signals import post_save, post_delete, pre_delete
from django.db.models import Sum
from django.dispatch import receiver

# -------------------------------
# LEDGER CREATION HELPER
# -------------------------------
def create_ledger(parent, ledger_model, transaction_type, reference_id, amount, description="", user=None):
    """
    Generic ledger creation function that ensures all balances and amounts are handled as Decimal.
    """
    # Refresh parent from database to get latest balance (important after reset operations)
    if parent:
        parent.refresh_from_db()
        opening_balance = Decimal(parent.balance or 0)
    else:
        opening_balance = Decimal(0)   # >>> updated to support CashLedger
    
    amount = Decimal(amount or 0)
    balance_after = opening_balance + amount

    # Convert Decimal to integer for BigIntegerField
    amount_int = int(amount)
    opening_balance_int = int(opening_balance)
    balance_after_int = int(balance_after)

    # >>> NEW : Special case for CashLedger (no FK field)
    if ledger_model.__name__ == "CashLedger":
        # Guard: require user to attribute cash ledger entries
        if user is None:
            return
        # Get or create CashBalance for the user
        from .models import CashBalance
        cash_balance, created = CashBalance.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        
        # Update opening balance from actual cash balance
        opening_balance = Decimal(cash_balance.balance or 0)
        balance_after = opening_balance + amount
        
        # Convert to int for BigIntegerField
        opening_balance_int = int(opening_balance)
        balance_after_int = int(balance_after)
        
        ledger_model.objects.create(
            user=user,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
            opening_balance=opening_balance_int,
            amount=amount_int,
            balance_after=balance_after_int,
        )
        
        # Update cash balance
        cash_balance.balance = balance_after
        cash_balance.save()
    else:
        ledger_model.objects.create(
            **{
                ledger_model.__name__.replace("Ledger", "").lower(): parent,
                "transaction_type": transaction_type,
                "reference_id": reference_id,
                "description": description,
                "opening_balance": opening_balance_int,
                "amount": amount_int,
                "balance_after": balance_after_int,
            }
        )

        # Update parent balance (bank, customer, vendor)
        parent.balance = balance_after_int
        parent.save()


# -------------------------------
# LEDGER ADJUSTMENT HELPERS (for PUT/PATCH/DELETE)
# -------------------------------
def _get_parent_field_name(ledger_model):
    name = ledger_model.__name__
    if name == "CashLedger":
        return None
    return name.replace("Ledger", "").lower()


def _group_existing_by_parent(ledger_model, transaction_type, reference_id):
    """
    Return mapping of { parent_or_user: total_amount } for entries matching transaction & ref.
    For CashLedger, keys are users. For others, keys are parent model instances.
    """
    qs = ledger_model.objects.filter(transaction_type=transaction_type, reference_id=reference_id)
    parent_field = _get_parent_field_name(ledger_model)
    grouped = {}
    for entry in qs:
        key = None
        if parent_field is None:
            key = entry.user
        else:
            key = getattr(entry, parent_field, None)
        if key is None:
            continue
        grouped[key] = grouped.get(key, 0) + int(entry.amount or 0)
    return grouped


def reset_ledger_for_reference(ledger_model, transaction_type, reference_id):
    """
    Create reversing entries to zero out the net effect for this reference across all parents/users.
    """
    grouped = _group_existing_by_parent(ledger_model, transaction_type, reference_id)
    for parent_or_user, total in grouped.items():
        if not total:
            continue
        delta = -int(total)
        if ledger_model.__name__ == "CashLedger":
            create_ledger(
                None,
                ledger_model,
                transaction_type,
                reference_id,
                delta,
                f"Reversal for ref #{reference_id}",
                user=parent_or_user,
            )
        else:
            create_ledger(
                parent_or_user,
                ledger_model,
                transaction_type,
                reference_id,
                delta,
                f"Reversal for ref #{reference_id}",
            )


def adjust_ledger_to_target(parent, ledger_model, transaction_type, reference_id, target_amount, description="", user=None):
    """
    Ensure the cumulative amount for (parent/user, type, ref) equals target by adding a delta entry if needed.
    Works for both create/update.
    """
    parent_field = _get_parent_field_name(ledger_model)
    if ledger_model.__name__ == "CashLedger":
        qs = ledger_model.objects.filter(user=user, transaction_type=transaction_type, reference_id=reference_id)
    else:
        qs = ledger_model.objects.filter(**{parent_field: parent, "transaction_type": transaction_type, "reference_id": reference_id})

    current_total = 0
    for e in qs:
        current_total += int(e.amount or 0)

    target_total = int(Decimal(target_amount or 0))
    delta = target_total - current_total
    if delta:
        create_ledger(parent, ledger_model, transaction_type, reference_id, delta, description, user=user)

# -------------------------------
# SALE → Customer & Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Sale)
def sale_ledger(sender, instance, created, **kwargs):
    # Delete old entries for this reference to ensure clean updates
    # This prevents confusion from multiple entries (original + reversals + new)
    CustomerLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()
    BankLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries (not just this transaction)
    # This ensures balances are correct before creating new entries
    if instance.customer:
        customer = vendor_customers.objects.get(pk=instance.customer.pk)
        remaining_total = CustomerLedger.objects.filter(customer=customer).aggregate(
            total=Sum('amount')
        )['total'] or 0
        customer.balance = int(remaining_total)
        customer.save(update_fields=['balance'])

    if instance.advance_bank:
        bank = instance.advance_bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        bank.balance = int(remaining_total)
        bank.save(update_fields=['balance'])

    if instance.user:
        from .models import CashBalance
        cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
        remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        cash_balance.balance = Decimal(remaining_total or 0)
        cash_balance.save()

    # Create new ledger entries (create_ledger will update balances automatically)
    # Customer ledger → for credit sales, use balance_amount; for others, use total_amount
    if instance.customer:
        total_amt = Decimal(instance.total_amount or 0)
        balance_amt = Decimal(instance.balance_amount or 0)
        customer = vendor_customers.objects.get(pk=instance.customer.pk)
        
        if instance.payment_method == 'credit' and balance_amt > 0:
            create_ledger(
                customer,
                CustomerLedger,
                "sale",
                instance.id,
                balance_amt,
                f"Sale #{instance.id} (Credit)"
            )
        else:
            create_ledger(
                customer,
                CustomerLedger,
                "sale",
                instance.id,
                total_amt,
                f"Sale #{instance.id}"
            )

    # Bank ledger → target is advance_amount when bank is set
    if instance.advance_bank:
        target_amt = instance.advance_amount or Decimal(0)
        create_ledger(
            instance.advance_bank,
            BankLedger,
            "sale",
            instance.id,
            target_amt,
            f"Sale #{instance.id}"
        )

    # Cash ledger → handles:
    # 1. Direct cash sales (payment_method == "cash")
    # 2. Credit sales with cash advance (advance_payment_method == "cash")
    cash_amount = Decimal(0)
    if instance.payment_method == "cash":
        cash_amount = instance.total_amount or Decimal(0)
    elif instance.payment_method == "credit" and instance.advance_payment_method == "cash":
        cash_amount = instance.advance_amount or Decimal(0)
    
    if cash_amount > 0 and instance.user is not None:
        create_ledger(
            None,
            CashLedger,
            "sale",
            instance.id,
            cash_amount,
            f"Sale #{instance.id}" + (" (Cash Advance)" if instance.payment_method == "credit" else ""),
            user=instance.user
        )
    


# -------------------------------
# PURCHASE → Vendor & Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Purchase)
def purchase_ledger(sender, instance, created, **kwargs):
    # Delete old entries for this reference to ensure clean updates
    VendorLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()
    BankLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.vendor:
        vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
        remaining_total = VendorLedger.objects.filter(vendor=vendor).aggregate(
            total=Sum('amount')
        )['total'] or 0
        vendor.balance = int(remaining_total)
        vendor.save(update_fields=['balance'])

    if instance.advance_bank:
        bank = instance.advance_bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        bank.balance = int(remaining_total)
        bank.save(update_fields=['balance'])

    if instance.user:
        from .models import CashBalance
        cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
        remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        cash_balance.balance = Decimal(remaining_total or 0)
        cash_balance.save()

    # Create new ledger entries
    if instance.vendor:
        total_amt = Decimal(instance.total_amount or 0)
        balance_amt = Decimal(instance.balance_amount or 0)
        vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
        
        if instance.payment_method == 'credit' and balance_amt > 0:
            # For credit purchases, use balance_amount (amount still owed)
            create_ledger(
                vendor,
                VendorLedger,
                "purchase",
                instance.id,
                balance_amt,
                f"Purchase #{instance.id} (Credit)"
            )
        else:
            # For cash/UPI/cheque purchases, use total_amount (includes all charges)
            # total_amount already includes: items + delivery_shipping_charges + packaging_charges
            create_ledger(
                vendor,
                VendorLedger,
                "purchase",
                instance.id,
                total_amt,
                f"Purchase #{instance.id}"
            )

    # Bank entry negative for purchase advance
    if instance.advance_bank:
        target = -(instance.advance_amount or Decimal(0))
        create_ledger(
            instance.advance_bank,
            BankLedger,
            "purchase",
            instance.id,
            target,
            f"Purchase #{instance.id}"
        )

    # Cash ledger for purchase
    # For cash purchases, deduct the full total_amount (includes all charges)
    if instance.payment_method == "cash" and instance.user is not None:
        target = -(instance.total_amount or Decimal(0))
        create_ledger(
            None,
            CashLedger,
            "purchase",
            instance.id,
            target,
            f"Cash Purchase #{instance.id}",
            user=instance.user
        )


# -------------------------------
# EXPENSE → Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Expense)
def expense_ledger(sender, instance, created, **kwargs):
    # Delete old entries for this reference to ensure clean updates
    BankLedger.objects.filter(transaction_type="expense", reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type="expense", reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.bank:
        bank = instance.bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        bank.balance = int(remaining_total)
        bank.save(update_fields=['balance'])

    if instance.user:
        from .models import CashBalance
        cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
        remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        cash_balance.balance = Decimal(remaining_total or 0)
        cash_balance.save()

    # Create new ledger entries
    if instance.bank:
        create_ledger(
            instance.bank,
            BankLedger,
            "expense",
            instance.id,
            -(instance.amount or Decimal(0)),
            f"Expense #{instance.id}"
        )

    # Cash ledger
    if instance.payment_method == "cash" and instance.user is not None:
        create_ledger(
            None,
            CashLedger,
            "expense",
            instance.id,
            -(instance.amount or Decimal(0)),
            f"Cash Expense #{instance.id}",
            user=instance.user
        )


# -------------------------------
# PAYMENT → Customer / Vendor Ledger
# -------------------------------
@receiver(post_save, sender=Payment)
def payment_ledger(sender, instance, created, **kwargs):
    amt = Decimal(instance.amount or 0)
    
    # Get payment_type display name (Cash, UPI, Cheque) - calculate once for reuse
    payment_type_display = instance.get_payment_type_display() if hasattr(instance, 'get_payment_type_display') else instance.payment_type.upper()

    # Delete old entries for this reference to ensure clean updates
    CustomerLedger.objects.filter(transaction_type__in=["payment", "refund"], reference_id=instance.id).delete()
    VendorLedger.objects.filter(transaction_type__in=["payment", "refund"], reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type__in=["deposit", "withdrawal"], reference_id=instance.id).delete()
    BankLedger.objects.filter(transaction_type__in=["deposit", "withdrawal", "payment"], reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.customer:
        customer = vendor_customers.objects.get(pk=instance.customer.pk)
        remaining_total = CustomerLedger.objects.filter(customer=customer).aggregate(
            total=Sum('amount')
        )['total'] or 0
        customer.balance = int(remaining_total)
        customer.save(update_fields=['balance'])

    if instance.vendor:
        vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
        remaining_total = VendorLedger.objects.filter(vendor=vendor).aggregate(
            total=Sum('amount')
        )['total'] or 0
        vendor.balance = int(remaining_total)
        vendor.save(update_fields=['balance'])

    # Note: Payment logic is inverted - ledger amounts don't match balance changes
    # This is intentional to maintain backward compatibility
    if instance.customer:
        customer = vendor_customers.objects.get(pk=instance.customer.pk)
        
        if instance.type == "received":
            # Customer received payment (paid vendor) - balance decreases
            # Ledger adds amt, then we manually subtract from balance
            create_ledger(
                customer,
                CustomerLedger,
                "payment",
                instance.id,
                amt,
                f"Payment Received ({payment_type_display}) #{instance.id}"
            )
            customer.refresh_from_db()
            customer.balance = int(Decimal(customer.balance or 0) - amt)
            customer.save(update_fields=['balance'])
        elif instance.type == "gave":
            # Customer gave refund - balance increases
            # Ledger subtracts amt, then we manually add to balance
            create_ledger(
                customer,
                CustomerLedger,
                "refund",
                instance.id,
                -amt,
                f"Refund Given ({payment_type_display}) #{instance.id}"
            )
            customer.refresh_from_db()
            customer.balance = int(Decimal(customer.balance or 0) + amt)
            customer.save(update_fields=['balance'])

    if instance.vendor:
        vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
        
        if instance.type == "gave":
            # Vendor gave payment - balance increases
            create_ledger(
                vendor,
                VendorLedger,
                "payment",
                instance.id,
                -amt,
                f"Payment Given ({payment_type_display}) #{instance.id}"
            )
            vendor.refresh_from_db()
            vendor.balance = int(Decimal(vendor.balance or 0) + amt)
            vendor.save(update_fields=['balance'])
        elif instance.type == "received":
            # Vendor received payment - balance decreases
            create_ledger(
                vendor,
                VendorLedger,
                "refund",
                instance.id,
                amt,
                f"Refund Received ({payment_type_display}) #{instance.id}"
            )
            vendor.refresh_from_db()
            vendor.balance = int(Decimal(vendor.balance or 0) - amt)
            vendor.save(update_fields=['balance'])

    # Cash/Bank ledger for payments
    # If "gave" → balance should INCREASE (add amount) - you gave payment, cash/bank balance increases
    # If "received" → balance should DECREASE (subtract amount) - you received payment, cash/bank balance decreases
    
    # Cash ledger for cash payments
    if instance.payment_type == "cash" and instance.user is not None:
        if instance.type == "gave":
            # You gave payment → cash balance increases (add/plus)
            adjust_ledger_to_target(
                None,
                CashLedger,
                "deposit",
                instance.id,
                amt,  # Positive amount to increase balance
                f"Cash Payment Given #{instance.id}",
                user=instance.user
            )
        elif instance.type == "received":
            # You received payment → cash balance decreases (minus/subtract)
            adjust_ledger_to_target(
                None,
                CashLedger,
                "withdrawal",
                instance.id,
                -amt,  # Negative amount to decrease balance
                f"Cash Payment Received #{instance.id}",
                user=instance.user
            )
    
    # Bank ledger for bank payments (upi/cheque)
    if instance.bank and instance.payment_type in ["upi", "cheque"]:
        if instance.type == "gave":
            # You gave payment → bank balance increases (add/plus)
            adjust_ledger_to_target(
                instance.bank,
                BankLedger,
                "deposit",
                instance.id,
                amt,  # Positive amount to increase balance
                f"Bank Payment Given #{instance.id}"
            )
        elif instance.type == "received":
            # You received payment → bank balance decreases (minus/subtract)
            adjust_ledger_to_target(
                instance.bank,
                BankLedger,
                "withdrawal",
                instance.id,
                -amt,  # Negative amount to decrease balance
                f"Bank Payment Received #{instance.id}"
            )


# -------------------------------
# CASH TRANSFER → Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=CashTransfer)
def cash_transfer_ledger(sender, instance, created, **kwargs):
    if instance.bank_account and instance.amount:
        # Adjust cash
        adjust_ledger_to_target(
            None,
            CashLedger,
            "withdrawal",
            instance.id,
            -(instance.amount or Decimal(0)),
            f"Cash to {instance.bank_account.name}",
            user=instance.user
        )

        # Adjust bank
        adjust_ledger_to_target(
            instance.bank_account,
            BankLedger,
            "deposit",
            instance.id,
            (instance.amount or Decimal(0)),
            f"Cash deposited to {instance.bank_account.name}"
        )


# -------------------------------
# BANK TRANSFER → Bank Ledger
# -------------------------------
@receiver(post_save, sender=BankTransfer)
def bank_transfer_ledger(sender, instance, created, **kwargs):
    # Delete old entries for this reference to ensure clean updates
    # This prevents confusion from multiple entries for the same transaction
    BankLedger.objects.filter(
        transaction_type__in=["transfered", "deposit"],
        reference_id=instance.id
    ).delete()

    amt = Decimal(instance.amount or 0)

    # Deduct from source bank
    if instance.from_bank:
        to_name = instance.to_bank.name if getattr(instance, 'to_bank', None) else 'destination bank'
        create_ledger(
            instance.from_bank,
            BankLedger,
            "transfered",
            instance.id,
            -amt,
            f"Transfer to {to_name}"
        )

    # Add to destination bank
    if instance.to_bank:
        from_name = instance.from_bank.name if getattr(instance, 'from_bank', None) else 'source bank'
        create_ledger(
            instance.to_bank,
            BankLedger,
            "deposit",
            instance.id,
            amt,
            f"Transfer from {from_name}"
        )


# -------------------------------
# DELETE HANDLERS: reverse previous effect fully
# -------------------------------
@receiver(post_delete, sender=Sale)
def sale_delete_ledger(sender, instance, **kwargs):
    # Delete ledger entries directly (consistent with save handler)
    CustomerLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()
    BankLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.customer:
        customer = vendor_customers.objects.get(pk=instance.customer.pk)
        remaining_total = CustomerLedger.objects.filter(customer=customer).aggregate(
            total=Sum('amount')
        )['total'] or 0
        customer.balance = int(remaining_total)
        customer.save(update_fields=['balance'])

    if instance.advance_bank:
        bank = instance.advance_bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        bank.balance = int(remaining_total)
        bank.save(update_fields=['balance'])

    if instance.user:
        from .models import CashBalance
        cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
        remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        cash_balance.balance = Decimal(remaining_total or 0)
        cash_balance.save()


@receiver(post_delete, sender=Purchase)
def purchase_delete_ledger(sender, instance, **kwargs):
    # Delete ledger entries directly (consistent with save handler)
    VendorLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()
    BankLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.vendor:
        vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
        remaining_total = VendorLedger.objects.filter(vendor=vendor).aggregate(
            total=Sum('amount')
        )['total'] or 0
        vendor.balance = int(remaining_total)
        vendor.save(update_fields=['balance'])

    if instance.advance_bank:
        bank = instance.advance_bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        bank.balance = int(remaining_total)
        bank.save(update_fields=['balance'])

    if instance.user:
        from .models import CashBalance
        cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
        remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        cash_balance.balance = Decimal(remaining_total or 0)
        cash_balance.save()


@receiver(post_delete, sender=Expense)
def expense_delete_ledger(sender, instance, **kwargs):
    # Delete ledger entries directly (consistent with save handler)
    BankLedger.objects.filter(transaction_type="expense", reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type="expense", reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.bank:
        bank = instance.bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        bank.balance = int(remaining_total)
        bank.save(update_fields=['balance'])

    if instance.user:
        from .models import CashBalance
        cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
        remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        cash_balance.balance = Decimal(remaining_total or 0)
        cash_balance.save()


@receiver(post_delete, sender=Payment)
def payment_delete_ledger(sender, instance, **kwargs):
    # Delete ledger entries directly (consistent with save handler)
    CustomerLedger.objects.filter(transaction_type__in=["payment", "refund"], reference_id=instance.id).delete()
    VendorLedger.objects.filter(transaction_type__in=["payment", "refund"], reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type__in=["deposit", "withdrawal"], reference_id=instance.id).delete()
    BankLedger.objects.filter(transaction_type__in=["deposit", "withdrawal", "payment"], reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.customer:
        customer = vendor_customers.objects.get(pk=instance.customer.pk)
        remaining_total = CustomerLedger.objects.filter(customer=customer).aggregate(
            total=Sum('amount')
        )['total'] or 0
        customer.balance = int(remaining_total)
        customer.save(update_fields=['balance'])

    if instance.vendor:
        vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
        remaining_total = VendorLedger.objects.filter(vendor=vendor).aggregate(
            total=Sum('amount')
        )['total'] or 0
        vendor.balance = int(remaining_total)
        vendor.save(update_fields=['balance'])

    if instance.user:
        from .models import CashBalance
        cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
        remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        cash_balance.balance = Decimal(remaining_total or 0)
        cash_balance.save()

    if hasattr(instance, 'bank_account') and instance.bank_account:
        bank = instance.bank_account
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        bank.balance = int(remaining_total)
        bank.save(update_fields=['balance'])


@receiver(post_delete, sender=CashTransfer)
def cash_transfer_delete_ledger(sender, instance, **kwargs):
    reset_ledger_for_reference(CashLedger, "withdrawal", instance.id)
    reset_ledger_for_reference(BankLedger, "deposit", instance.id)


@receiver(post_delete, sender=BankTransfer)
def bank_transfer_delete_ledger(sender, instance, **kwargs):
    # Use reset_ledger_for_reference to create reversing entries
    # This ensures bank balances are correctly updated when transfer is deleted
    # Note: This creates reversal entries, but on delete it's acceptable for audit trail
    reset_ledger_for_reference(BankLedger, "transfered", instance.id)
    reset_ledger_for_reference(BankLedger, "deposit", instance.id)


# -------------------------------
# POS WHOLESALE → Send SMS
# -------------------------------
@receiver(post_save, sender=pos_wholesale)
def pos_wholesale_sms(sender, instance, created, **kwargs):
    """
    Send SMS when a wholesale invoice is created or updated.
    This ensures SMS is sent after the invoice is actually created.
    """
    try:
        import logging
        signal_logger = logging.getLogger(__name__)
        from .sms_utils import send_sale_sms
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        signal_logger.info(f"[SMS SIGNAL] [{timestamp}] pos_wholesale post_save signal triggered for Invoice #{instance.id}")
        signal_logger.info(f"[SMS SIGNAL] Invoice Type: {instance.invoice_type}")
        signal_logger.info(f"[SMS SIGNAL] Sale ID: {instance.sale.id if instance.sale else 'N/A'}")
        
        # Only send SMS when invoice is created (not on every update)
        if created and instance.sale:
            signal_logger.info(f"[SMS SIGNAL] New wholesale invoice created, calling send_sale_sms()...")
            # Send SMS based on invoice type and SMS settings
            send_sale_sms(instance.sale, instance.invoice_type)
        else:
            signal_logger.info(f"[SMS SIGNAL] Skipping SMS (created={created}, has_sale={bool(instance.sale)})")
    except Exception as e:
        # Don't fail the invoice if SMS sending fails - just log the error
        import logging
        logger = logging.getLogger(__name__)
        error_msg = f"Failed to send SMS for wholesale invoice {instance.id}: {str(e)}"
        logger.error(f"[SMS SIGNAL] ❌ EXCEPTION: {error_msg}")
        logger.exception("SMS signal exception details")


#-------------------------------------------------------



# signals.py
from django.db.models.signals import post_save
from django.db.models import F
from django.dispatch import receiver
from vendor.models import product
from .models import PurchaseItem, StockTransaction, SaleItem, OnlineOrderLedger
from customer.models import OrderItem, ReturnExchange 




def log_stock_transaction(product_obj, txn_type, qty, ref_id=None):
    """Create a stock transaction record."""
    StockTransaction.objects.create(
        product=product_obj,
        transaction_type=txn_type,
        quantity=qty,
        reference_id=ref_id,
    )


# -----------------------------------------------------------------------------
# 🟢 PURCHASE (+ stock)
# -----------------------------------------------------------------------------
@receiver(post_save, sender=PurchaseItem)
def increase_stock_on_purchase_create(sender, instance, created, **kwargs):
    """Handle stock increase when a new PurchaseItem is created."""
    if created:
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + instance.quantity)
        log_stock_transaction(instance.product, "purchase", instance.quantity, ref_id=instance.pk)

@receiver(pre_save, sender=PurchaseItem)
def update_stock_on_purchase_edit(sender, instance, **kwargs):
    """Handle stock updates when an existing PurchaseItem is modified."""
    # Skip if this is a new item (handled by post_save)
    if instance.pk is None:
        return
    
    try:
        old = PurchaseItem.objects.get(pk=instance.pk)
        old_qty = old.quantity
        old_product = old.product
    except PurchaseItem.DoesNotExist:
        return

    qty_diff = instance.quantity - old_qty

    # If product changed, restore old product stock and increase new product stock
    if old_product and old_product != instance.product:
        product.objects.filter(id=old_product.id).update(stock_cached=F('stock_cached') - old_qty)
        log_stock_transaction(old_product, "purchase", -old_qty, ref_id=instance.pk)

        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + instance.quantity)
        log_stock_transaction(instance.product, "purchase", instance.quantity, ref_id=instance.pk)
        return

    # If quantity changed, adjust stock accordingly
    if qty_diff > 0:
        # Quantity increased, increase stock
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + qty_diff)
        log_stock_transaction(instance.product, "purchase", qty_diff, ref_id=instance.pk)
    elif qty_diff < 0:
        # Quantity decreased, reduce stock
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') - abs(qty_diff))
        log_stock_transaction(instance.product, "purchase", -abs(qty_diff), ref_id=instance.pk)


@receiver(post_delete, sender=PurchaseItem)
def restore_stock_on_purchase_delete(sender, instance, **kwargs):
    product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') - instance.quantity)
    log_stock_transaction(instance.product, "purchase", -instance.quantity, ref_id=instance.pk)




# -----------------------------------------------------------------------------
# 🔵 SALE (POS)
# -----------------------------------------------------------------------------
@receiver(post_save, sender=SaleItem)
def reduce_stock_on_sale_create(sender, instance, created, **kwargs):
    """Handle stock reduction when a new SaleItem is created."""
    if created:
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') - instance.quantity)
        log_stock_transaction(instance.product, "sale", -instance.quantity, ref_id=instance.pk)

@receiver(pre_save, sender=SaleItem)
def update_stock_on_sale_edit(sender, instance, **kwargs):
    """Handle stock updates when an existing SaleItem is modified."""
    # Skip if this is a new item (handled by post_save)
    if instance.pk is None:
        return
    
    try:
        old = SaleItem.objects.get(pk=instance.pk)
        old_qty = old.quantity
        old_product = old.product
    except SaleItem.DoesNotExist:
        return

    qty_diff = instance.quantity - old_qty

    # If product changed, restore old product stock and reduce new product stock
    if old_product and old_product != instance.product:
        product.objects.filter(id=old_product.id).update(stock_cached=F('stock_cached') + old_qty)
        log_stock_transaction(old_product, "sale", old_qty, ref_id=instance.pk)

        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') - instance.quantity)
        log_stock_transaction(instance.product, "sale", -instance.quantity, ref_id=instance.pk)
        return

    # If quantity changed, adjust stock accordingly
    if qty_diff > 0:
        # Quantity increased, reduce stock
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') - qty_diff)
        log_stock_transaction(instance.product, "sale", -qty_diff, ref_id=instance.pk)
    elif qty_diff < 0:
        # Quantity decreased, restore stock
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + abs(qty_diff))
        log_stock_transaction(instance.product, "sale", abs(qty_diff), ref_id=instance.pk)


@receiver(post_delete, sender=SaleItem)
def restore_stock_on_sale_delete(sender, instance, **kwargs):
    product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + instance.quantity)
    log_stock_transaction(instance.product, "sale", instance.quantity, ref_id=instance.pk)


# -----------------------------------------------------------------------------
# 🟠 ORDER
# -----------------------------------------------------------------------------
@receiver(post_save, sender=OrderItem)
def reduce_stock_on_order_create(sender, instance, created, **kwargs):
    if created:
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') - instance.quantity)
        log_stock_transaction(instance.product, "sale", -instance.quantity, ref_id=instance.pk)

@receiver(pre_save, sender=OrderItem)
def update_stock_on_order_edit(sender, instance, **kwargs):
    try:
        old = OrderItem.objects.get(pk=instance.pk)
        old_qty = old.quantity
        old_product = old.product
    except OrderItem.DoesNotExist:
        old_qty = 0
        old_product = None

    if instance.pk is None:
        return

    qty_diff = instance.quantity - old_qty

    if old_product and old_product != instance.product:
        product.objects.filter(id=old_product.id).update(stock_cached=F('stock_cached') + old_qty)
        log_stock_transaction(old_product, "sale", old_qty, ref_id=instance.pk)

        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') - instance.quantity)
        log_stock_transaction(instance.product, "sale", -instance.quantity, ref_id=instance.pk)
        return

    if qty_diff > 0:
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') - qty_diff)
        log_stock_transaction(instance.product, "sale", -qty_diff, ref_id=instance.pk)
    elif qty_diff < 0:
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + abs(qty_diff))
        log_stock_transaction(instance.product, "sale", abs(qty_diff), ref_id=instance.pk)


@receiver(post_save, sender=ReturnExchange)
def update_stock_on_return_exchange(sender, instance, created, **kwargs):
    # ReturnExchange no longer has status; handled via OrderItem.status elsewhere
    return

@receiver(post_save, sender=OrderItem)
def add_stock_on_return_completed(sender, instance, created, **kwargs):
    # When OrderItem status transitions to returned/replaced_completed, add stock back for returns
    if created:
        return
    try:
        new_status = instance.status
    except Exception:
        return
    if new_status == 'returned/replaced_completed':
        try:
            from customer.models import ReturnExchange
            req = ReturnExchange.objects.filter(order_item=instance).order_by('-created_at').first()
        except Exception:
            req = None
        if req and req.type == 'return':
            product.objects.filter(id=instance.product.id).update(
                stock_cached=F('stock_cached') + instance.quantity
            )


# -----------------------------------------------------------------------------
# Online Order Ledger entries per vendor for online orders
# -----------------------------------------------------------------------------
@receiver(post_save, sender=OrderItem)
def create_online_order_ledger_on_create(sender, instance, created, **kwargs):
    # Create a ledger entry when an order item is created (treated as online order)
    if created:
        try:
            OnlineOrderLedger.objects.create(
                user=instance.product.user,
                order_item=instance,
                product=instance.product,
                order_id=getattr(instance.order, 'id', None),
                quantity=instance.quantity,
                amount=getattr(instance, 'price', 0) * instance.quantity,
                status='recorded',
                note='Online order recorded'
            )
        except Exception:
            pass


@receiver(post_save, sender=OrderItem)
def update_online_order_ledger_on_return(sender, instance, created, **kwargs):
    # When order item is completed as returned/replaced, update the previous ledger note/status
    if created:
        return
    try:
        new_status = instance.status
    except Exception:
        return
    if new_status == 'returned/replaced_completed':
        try:
            req = ReturnExchange.objects.filter(order_item=instance).order_by('-created_at').first()
        except Exception:
            req = None

        try:
            entry = OnlineOrderLedger.objects.filter(order_item=instance).order_by('-created_at').first()
        except OnlineOrderLedger.DoesNotExist:
            entry = None

        if entry:
            if req and req.type == 'return':
                entry.status = 'returned'
                entry.note = (entry.note or '') + ' | Marked returned'
            elif req and req.type == 'exchange':
                entry.status = 'replaced'
                entry.note = (entry.note or '') + ' | Marked replaced'
            else:
                entry.note = (entry.note or '') + ' | Marked completed'
            entry.save(update_fields=['status', 'note', 'updated_at'])
            # Avoid duplicate transaction per request id
            from django.db.models import Q
            if not StockTransaction.objects.filter(
                product=instance.product,
                transaction_type='return',
                reference_id=req.pk
            ).exists():
                log_stock_transaction(
                        instance.product,
                        'return',
                        instance.quantity,
                        ref_id=req.pk
                    )

# --- Ensure stock logs on create have proper reference ids ---
@receiver(post_delete, sender=OrderItem)
def restore_stock_on_order_delete(sender, instance, **kwargs):
    product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + instance.quantity)
    log_stock_transaction(instance.product, "sale", instance.quantity, ref_id=instance.pk)


# -------------------------------
# USER DELETE → Cleanup related ledger entries
# -------------------------------
@receiver(pre_delete, sender='users.User')
def user_delete_cleanup(sender, instance, **kwargs):
    """
    Cleanup ledger entries and related objects before User deletion.
    This prevents foreign key constraint errors by ensuring all related
    ledger entries are deleted before Django's CASCADE deletion processes them.
    
    The issue: When User is deleted, Django CASCADE deletes:
    - vendor_bank -> which CASCADE deletes BankLedger
    - vendor_customers -> which CASCADE deletes CustomerLedger  
    - vendor_vendors -> which CASCADE deletes VendorLedger
    
    But if there are other constraints or the deletion order is wrong, it fails.
    Solution: Delete all ledger entries FIRST, before Django processes CASCADE.
    """
    from .models import CashLedger, CashBalance, BankLedger, CustomerLedger, VendorLedger
    from .models import vendor_bank, vendor_customers, vendor_vendors
    from django.db import transaction
    
    # Use a transaction to ensure atomicity
    with transaction.atomic():
        # Get all related object IDs BEFORE any deletions
        bank_ids = list(vendor_bank.objects.filter(user=instance).values_list('id', flat=True))
        customer_ids = list(vendor_customers.objects.filter(user=instance).values_list('id', flat=True))
        vendor_ids = list(vendor_vendors.objects.filter(user=instance).values_list('id', flat=True))
        
        # Delete ALL ledger entries FIRST (before Django's CASCADE tries to delete them)
        # This prevents foreign key constraint errors
        
        # 1. Delete CashLedger entries (direct FK to User)
        CashLedger.objects.filter(user=instance).delete()
        
        # 2. Delete CashBalance (direct FK to User)
        CashBalance.objects.filter(user=instance).delete()
        
        # 3. Delete BankLedger entries (FK to vendor_bank which will be CASCADE deleted)
        if bank_ids:
            BankLedger.objects.filter(bank_id__in=bank_ids).delete()
        
        # 4. Delete CustomerLedger entries (FK to vendor_customers which will be CASCADE deleted)
        if customer_ids:
            CustomerLedger.objects.filter(customer_id__in=customer_ids).delete()
        
        # 5. Delete VendorLedger entries (FK to vendor_vendors which will be CASCADE deleted)
        if vendor_ids:
            VendorLedger.objects.filter(vendor_id__in=vendor_ids).delete()
        
        # Note: We don't update balances here because the banks/customers/vendors
        # will be deleted by CASCADE anyway. Updating them might cause additional
        # constraint issues during the deletion process.


