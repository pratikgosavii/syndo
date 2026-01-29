import os
from django.db.models.signals import pre_save, post_delete, post_save
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
from .models import BankTransfer, CashTransfer, Sale, Purchase, Expense, Payment, BankLedger, CustomerLedger,   CashLedger, VendorLedger, ExpenseLedger, vendor_bank, vendor_customers, vendor_vendors, pos_wholesale


from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import logging
from .models import Sale, Purchase, Expense, Payment, BankLedger, CustomerLedger, VendorLedger, vendor_bank, vendor_customers, vendor_vendors

from decimal import Decimal
from django.db.models.signals import post_save, post_delete, pre_delete
from django.db.models import Sum
from django.db import transaction
from django.dispatch import receiver
import logging

# Get logger for signals
logger = logging.getLogger('vendor.signals')

# -------------------------------
# LEDGER CREATION HELPER
# -------------------------------
def create_ledger(parent, ledger_model, transaction_type, reference_id, amount, description="", user=None):
    """
    Generic ledger creation function that ensures all balances and amounts are handled as Decimal.
    """
    logger.debug(f"[CREATE_LEDGER] Called for {ledger_model.__name__}")
    logger.debug(f"[CREATE_LEDGER] Parent: {parent}")
    logger.debug(f"[CREATE_LEDGER] Transaction Type: {transaction_type}")
    logger.debug(f"[CREATE_LEDGER] Reference ID: {reference_id}")
    logger.debug(f"[CREATE_LEDGER] Amount: {amount}")
    logger.debug(f"[CREATE_LEDGER] Description: {description}")
    logger.debug(f"[CREATE_LEDGER] User: {user}")
    
    q2 = Decimal("0.01")

    # Refresh parent from database to get latest balance
    if parent:
        parent.refresh_from_db()
        opening_balance = Decimal(parent.balance or 0).quantize(q2)
        logger.debug(f"[CREATE_LEDGER] Parent balance (from DB): {opening_balance}")
    else:
        opening_balance = Decimal(0).quantize(q2)   # CashLedger has no parent FK
        logger.debug(f"[CREATE_LEDGER] No parent (CashLedger) - opening balance: {opening_balance}")
    
    amount = Decimal(amount or 0).quantize(q2)
    balance_after = (opening_balance + amount).quantize(q2)
    logger.debug(f"[CREATE_LEDGER] Amount (Decimal): {amount}")
    logger.debug(f"[CREATE_LEDGER] Balance After: {balance_after}")

    # >>> NEW : Special case for CashLedger (no FK field)
    if ledger_model.__name__ == "CashLedger":
        logger.debug("[CREATE_LEDGER] Processing CashLedger...")
        # Guard: require user to attribute cash ledger entries
        if user is None:
            logger.warning("[CREATE_LEDGER] User is None - returning without creating CashLedger")
            return
        # Get or create CashBalance for the user
        from .models import CashBalance
        cash_balance, created = CashBalance.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        logger.debug(f"[CREATE_LEDGER] CashBalance {'created' if created else 'retrieved'}: {cash_balance}")
        logger.debug(f"[CREATE_LEDGER] CashBalance balance: {cash_balance.balance}")
        
        # Update opening balance from actual cash balance
        opening_balance = Decimal(cash_balance.balance or 0).quantize(q2)
        balance_after = (opening_balance + amount).quantize(q2)
        logger.debug(f"[CREATE_LEDGER] Updated Opening Balance: {opening_balance}")
        logger.debug(f"[CREATE_LEDGER] Updated Balance After: {balance_after}")
        
        logger.debug(f"[CREATE_LEDGER] Creating CashLedger entry with data:")
        logger.debug(f"[CREATE_LEDGER]   - user: {user} (ID: {user.id})")
        logger.debug(f"[CREATE_LEDGER]   - transaction_type: {transaction_type}")
        logger.debug(f"[CREATE_LEDGER]   - reference_id: {reference_id}")
        logger.debug(f"[CREATE_LEDGER]   - description: {description}")
        logger.debug(f"[CREATE_LEDGER]   - opening_balance: {opening_balance}")
        logger.debug(f"[CREATE_LEDGER]   - amount: {amount}")
        logger.debug(f"[CREATE_LEDGER]   - balance_after: {balance_after}")
        
        try:
            ledger_entry = ledger_model.objects.create(
            user=user,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
            opening_balance=opening_balance,
            amount=amount,
            balance_after=balance_after,
        )
            logger.info("[CREATE_LEDGER] CashLedger entry created successfully")
            logger.info(f"[CREATE_LEDGER] Ledger Entry ID: {ledger_entry.id}")
            logger.debug(f"[CREATE_LEDGER] Ledger Entry: {ledger_entry}")
        except Exception as e:
            logger.error("[CREATE_LEDGER] ERROR creating CashLedger entry")
            logger.error(f"[CREATE_LEDGER] Error: {str(e)}")
            logger.error(f"[CREATE_LEDGER] Error Type: {type(e).__name__}")
            import traceback
            logger.error(f"[CREATE_LEDGER] Traceback: {traceback.format_exc()}")
            raise
        
        # Update cash balance
        cash_balance.balance = balance_after
        cash_balance.save()
        logger.debug(f"[CREATE_LEDGER] CashBalance updated to: {balance_after}")
    else:
        logger.debug(f"[CREATE_LEDGER] Processing {ledger_model.__name__}...")
        parent_field = ledger_model.__name__.replace("Ledger", "").lower()
        logger.debug(f"[CREATE_LEDGER] Parent field name: {parent_field}")
        logger.debug(f"[CREATE_LEDGER] Parent object: {parent}")
        if parent:
            logger.debug(f"[CREATE_LEDGER] Parent ID: {parent.id}")
            if hasattr(parent, 'bank_name'):
                logger.debug(f"[CREATE_LEDGER] Bank Name: {parent.bank_name}")
        
        logger.debug(f"[CREATE_LEDGER] Creating {ledger_model.__name__} with data:")
        logger.debug(f"[CREATE_LEDGER]   - {parent_field}: {parent}")
        logger.debug(f"[CREATE_LEDGER]   - transaction_type: {transaction_type}")
        logger.debug(f"[CREATE_LEDGER]   - reference_id: {reference_id}")
        logger.debug(f"[CREATE_LEDGER]   - description: {description}")
        logger.debug(f"[CREATE_LEDGER]   - opening_balance: {opening_balance}")
        logger.debug(f"[CREATE_LEDGER]   - amount: {amount}")
        logger.debug(f"[CREATE_LEDGER]   - balance_after: {balance_after}")
        
        try:
            ledger_entry = ledger_model.objects.create(
                **{
                    parent_field: parent,
                "transaction_type": transaction_type,
                "reference_id": reference_id,
                "description": description,
                "opening_balance": opening_balance,
                "amount": amount,
                "balance_after": balance_after,
            }
        )
            logger.info(f"[CREATE_LEDGER] {ledger_model.__name__} entry created successfully")
            logger.info(f"[CREATE_LEDGER] Ledger Entry ID: {ledger_entry.id}")
            logger.debug(f"[CREATE_LEDGER] Ledger Entry: {ledger_entry}")
        except Exception as e:
            logger.error(f"[CREATE_LEDGER] ERROR creating {ledger_model.__name__} entry")
            logger.error(f"[CREATE_LEDGER] Error: {str(e)}")
            logger.error(f"[CREATE_LEDGER] Error Type: {type(e).__name__}")
            import traceback
            logger.error(f"[CREATE_LEDGER] Traceback: {traceback.format_exc()}")
            raise

        # Update parent balance (bank, customer, vendor)
        logger.debug(f"[CREATE_LEDGER] Updating parent balance...")
        logger.debug(f"[CREATE_LEDGER] Old balance: {parent.balance}")
        parent.balance = balance_after
        parent.save()
        logger.debug(f"[CREATE_LEDGER] Parent balance updated to: {balance_after}")
        logger.debug(f"[CREATE_LEDGER] New balance (from DB): {parent.balance}")
    
    logger.debug(f"[CREATE_LEDGER] Function completed successfully")


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
        grouped[key] = grouped.get(key, Decimal(0)) + Decimal(entry.amount or 0)
    return grouped


def reset_ledger_for_reference(ledger_model, transaction_type, reference_id):
    """
    Create reversing entries to zero out the net effect for this reference across all parents/users.
    """
    grouped = _group_existing_by_parent(ledger_model, transaction_type, reference_id)
    for parent_or_user, total in grouped.items():
        if not total or Decimal(total) == 0:
            continue
        delta = -Decimal(total)
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

    current_total = Decimal(0)
    for e in qs:
        current_total += Decimal(e.amount or 0)

    target_total = Decimal(target_amount or 0)
    delta = target_total - current_total
    if delta != 0:
        create_ledger(parent, ledger_model, transaction_type, reference_id, delta, description, user=user)

# -------------------------------
# HELPER: Check if sale should create ledgers/update stock
# -------------------------------
def should_process_sale(sale_instance):
    """
    Check if a sale should create ledgers and update stock.
    Rule: Don't process POS sales UNLESS:
      - It is wholesale (is_wholesale_rate=True) AND invoice_type is "invoice"
      - OR wholesale is off (is_wholesale_rate=False)
    Returns: (should_process, reason)
    """
    if sale_instance.is_wholesale_rate:
        # It's a wholesale sale - only process if invoice_type is "invoice"
        wholesale_record = pos_wholesale.objects.filter(sale=sale_instance).first()
        if wholesale_record and wholesale_record.invoice_type == "invoice":
            return True, "wholesale_sale_with_invoice"
        else:
            invoice_type = wholesale_record.invoice_type if wholesale_record else "N/A"
            return False, f"wholesale_sale_with_invoice_type_{invoice_type}"
    else:
        # Wholesale is off (is_wholesale_rate=False) - process it
        return True, "non_wholesale_sale"

# -------------------------------
# SALE → Customer & Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Sale)
def sale_ledger(sender, instance, created, **kwargs):
    """
    Signal handler for Sale model to create ledger entries.
    Wrapped in transaction.atomic() to prevent database locks in SQLite.
    """
    try:
        # Auto-detect advance_payment_method if not set but advance_amount > 0
        if instance.payment_method == "credit" and not instance.advance_payment_method:
            advance_amt = Decimal(instance.advance_amount or 0)
            if advance_amt > 0:
                if instance.advance_bank:
                    instance.advance_payment_method = "bank"
                    logger.info(f"[SALE_LEDGER] Auto-detected advance_payment_method: bank (advance_bank is set)")
                else:
                    instance.advance_payment_method = "cash"
                    logger.info(f"[SALE_LEDGER] Auto-detected advance_payment_method: cash (advance_bank is not set)")
                instance.save(update_fields=['advance_payment_method'])
        
        logger.info("=" * 80)
        logger.info(f"[SALE_LEDGER] Signal triggered for Sale ID: {instance.id}")
        logger.info(f"[SALE_LEDGER] Created: {created}")
        logger.info(f"[SALE_LEDGER] Payment Method: {instance.payment_method}")
        logger.info(f"[SALE_LEDGER] Advance Payment Method: {instance.advance_payment_method}")
        logger.info(f"[SALE_LEDGER] Advance Amount: {instance.advance_amount}")
        logger.info(f"[SALE_LEDGER] Advance Payment Amount: {instance.advance_payment_amount}")
        logger.info(f"[SALE_LEDGER] Advance Bank: {instance.advance_bank}")
        logger.info(f"[SALE_LEDGER] Total Amount: {instance.total_amount}")
        logger.info(f"[SALE_LEDGER] Balance Amount: {instance.balance_amount}")
        logger.info(f"[SALE_LEDGER] User: {instance.user}")
        logger.info(f"[SALE_LEDGER] Customer: {instance.customer}")
        
        # Check if we should create ledgers for this POS sale
        should_process, reason = should_process_sale(instance)
        
        if not should_process:
            logger.info("=" * 80)
            logger.info(f"[SALE_LEDGER] Skipping ledger creation for Sale ID: {instance.id}")
            logger.info(f"[SALE_LEDGER] Reason: {reason}")
            logger.info("=" * 80)
            return
        
        logger.info(f"[SALE_LEDGER] Will create ledgers - Reason: {reason}")
        
        # Check if this is a credit sale with cash advance
        if instance.payment_method == "credit" and instance.advance_payment_method == "cash":
            logger.info("=" * 80)
            logger.info("[SALE_LEDGER] *** CREDIT SALE WITH CASH ADVANCE DETECTED ***")
            logger.info(f"[SALE_LEDGER] Payment Method: {instance.payment_method}")
            logger.info(f"[SALE_LEDGER] Advance Payment Method: {instance.advance_payment_method}")
            logger.info(f"[SALE_LEDGER] Advance Amount: {instance.advance_amount}")
            logger.info(f"[SALE_LEDGER] Advance Payment Amount: {instance.advance_payment_amount}")
            logger.info(f"[SALE_LEDGER] User: {instance.user}")
            logger.info("=" * 80)
        
        # Check if this is a credit sale with bank advance
        if instance.payment_method == "credit" and instance.advance_payment_method == "bank":
            logger.info("=" * 80)
            logger.info("[SALE_LEDGER] *** CREDIT SALE WITH BANK ADVANCE DETECTED ***")
            logger.info(f"[SALE_LEDGER] Payment Method: {instance.payment_method}")
            logger.info(f"[SALE_LEDGER] Advance Payment Method: {instance.advance_payment_method}")
            logger.info(f"[SALE_LEDGER] Advance Amount: {instance.advance_amount}")
            logger.info(f"[SALE_LEDGER] Advance Payment Amount: {instance.advance_payment_amount}")
            logger.info(f"[SALE_LEDGER] Advance Bank: {instance.advance_bank}")
            logger.info("=" * 80)
        
        # Wrap all database operations in a transaction to reduce lock time
        with transaction.atomic():
            # Refresh instance from database to ensure we have latest values, especially for related fields
            instance.refresh_from_db()
            logger.info("[SALE_LEDGER] Instance refreshed from database")
            
            # Delete old entries for this reference to ensure clean updates
            # This prevents confusion from multiple entries (original + reversals + new)
            logger.debug("[SALE_LEDGER] Deleting old ledger entries...")
            CustomerLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()
            BankLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()
            CashLedger.objects.filter(transaction_type="sale", reference_id=instance.id).delete()
            logger.debug("[SALE_LEDGER] Old ledger entries deleted")

        # Recalculate balances from ALL remaining ledger entries (not just this transaction)
        # This ensures balances are correct before creating new entries
        # Customer balance = opening_balance + sum of all ledger entries
        if instance.customer:
            customer = vendor_customers.objects.get(pk=instance.customer.pk)
            ledger_total = CustomerLedger.objects.filter(customer=customer).aggregate(
                total=Sum('amount')
            )['total'] or 0
            # Customer balance = opening_balance + sum of ledger entries
            customer.balance = Decimal(customer.opening_balance or 0) + Decimal(ledger_total or 0)
            customer.save(update_fields=['balance'])

        if instance.bank:
            bank = instance.bank
            remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
                total=Sum('amount')
            )['total'] or 0
            bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
            bank.save(update_fields=['balance'])

        if instance.advance_bank:
            bank = instance.advance_bank
            remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
                total=Sum('amount')
            )['total'] or 0
            # Bank balance = opening_balance + sum(all bank ledger entries)
            bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
            bank.save(update_fields=['balance'])

        # Recalculate cash balance (independent of bank)
        if instance.user:
            from .models import CashBalance
            cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
            remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
                total=Sum('amount')
            )['total'] or 0
            cash_balance.balance = Decimal(remaining_total or 0)
            cash_balance.save()

        # Create new ledger entries
        # CustomerLedger 'amount' is treated as the customer's OUTSTANDING DUE.
        # So it should change customer credit balance ONLY for credit sales (remaining due),
        # and stay unchanged for fully-paid cash/upi/cheque sales.
        if instance.customer:
            total_amt = Decimal(instance.total_amount or 0)
            balance_amt = Decimal(instance.balance_amount or 0)  # remaining due for credit sales
            customer = vendor_customers.objects.get(pk=instance.customer.pk)
            
            customer.refresh_from_db()
            ledger_total = CustomerLedger.objects.filter(customer=customer).aggregate(
                total=Sum('amount')
            )['total'] or 0
            opening_balance = Decimal(customer.opening_balance or 0) + Decimal(ledger_total)

            if instance.payment_method == 'credit' and balance_amt > 0:
                # Credit sale: add only remaining due to customer balance
                amount_due = balance_amt
                description = f"Sale #{instance.id} (Credit)"
            else:
                # Fully paid sale (cash/upi/cheque): no due, keep credit balance unchanged
                amount_due = Decimal(0)
                description = f"Sale #{instance.id} (Paid)"

            balance_after = opening_balance + amount_due
                
            CustomerLedger.objects.create(
                customer=customer,
                transaction_type="sale",
                reference_id=instance.id,
                description=description,
                opening_balance=opening_balance,
                amount=amount_due,  # due amount only
                balance_after=balance_after,
                total_bill_amount=total_amt,  # always store bill total
            )
                
            customer.balance = balance_after
            customer.save()

            # Bank ledger:
            # 1. UPI/cheque: instance.bank gets +total_amount (sale = money in)
            # 2. Credit + bank advance: instance.advance_bank gets +advance_amount
            logger.debug("[SALE_LEDGER] Checking bank ledger creation...")
            logger.debug(f"[SALE_LEDGER] Payment Method: {instance.payment_method}")
            logger.debug(f"[SALE_LEDGER] Advance Payment Method: {instance.advance_payment_method}")
            logger.debug(f"[SALE_LEDGER] Bank: {instance.bank}")
            logger.debug(f"[SALE_LEDGER] Advance Bank: {instance.advance_bank}")

            if instance.payment_method in ("upi", "cheque") and instance.bank:
                bank_amt = Decimal(instance.total_amount or 0)
                if bank_amt > 0:
                    create_ledger(
                        instance.bank,
                        BankLedger,
                        "sale",
                        instance.id,
                        bank_amt,
                        f"Sale #{instance.id} ({instance.payment_method.upper()})",
                    )
                    logger.info(f"[SALE_LEDGER] Bank ledger created for Sale #{instance.id} using bank: {instance.bank}")
            elif instance.payment_method == "credit" and instance.advance_payment_method == "bank":
                logger.info("[SALE_LEDGER] Credit sale with bank advance detected")
                # Check both advance_amount and advance_payment_amount fields
                advance_amt = Decimal(instance.advance_amount or instance.advance_payment_amount or 0)
                logger.debug(f"[SALE_LEDGER] Advance Amount (from advance_amount): {instance.advance_amount}")
                logger.debug(f"[SALE_LEDGER] Advance Amount (from advance_payment_amount): {instance.advance_payment_amount}")
                logger.debug(f"[SALE_LEDGER] Calculated Advance Amount: {advance_amt}")
                logger.debug(f"[SALE_LEDGER] Advance Amount > 0: {advance_amt > 0}")
                logger.debug(f"[SALE_LEDGER] Advance Bank exists: {instance.advance_bank is not None}")
                
                if advance_amt > 0 and instance.advance_bank:
                    logger.info("=" * 80)
                    logger.info("[SALE_LEDGER] >>>>>> CREATING BANK LEDGER ENTRY <<<<<<")
                    logger.info(f"[SALE_LEDGER] Bank: {instance.advance_bank} (ID: {instance.advance_bank.id})")
                    logger.info(f"[SALE_LEDGER] Bank Name: {instance.advance_bank.bank_name if hasattr(instance.advance_bank, 'bank_name') else 'N/A'}")
                    logger.info(f"[SALE_LEDGER] Amount: {advance_amt}")
                    logger.info(f"[SALE_LEDGER] Transaction Type: sale")
                    logger.info(f"[SALE_LEDGER] Reference ID: {instance.id}")
                    logger.info(f"[SALE_LEDGER] Description: Sale #{instance.id} (Bank Advance)")
                    logger.info("[SALE_LEDGER] Calling create_ledger() for BankLedger...")
                    logger.info("=" * 80)
                    
                    try:
                        create_ledger(
                            instance.advance_bank,
                            BankLedger,
                            "sale",
                            instance.id,
                            advance_amt,
                            f"Sale #{instance.id} (Bank Advance)"
                        )
                        logger.info("=" * 80)
                        logger.info("[SALE_LEDGER] BANK LEDGER ENTRY CREATED SUCCESSFULLY")
                        logger.info(f"[SALE_LEDGER] Bank: {instance.advance_bank}")
                        logger.info(f"[SALE_LEDGER] Amount: {advance_amt}")
                        logger.info("=" * 80)
                    except Exception as e:
                        logger.error("=" * 80)
                        logger.error("[SALE_LEDGER] ERROR CREATING BANK LEDGER")
                        logger.error(f"[SALE_LEDGER] Error: {str(e)}")
                        logger.error(f"[SALE_LEDGER] Error Type: {type(e).__name__}")
                        import traceback
                        logger.error(f"[SALE_LEDGER] Traceback: {traceback.format_exc()}")
                        logger.error("=" * 80)
                else:
                    logger.warning("[SALE_LEDGER] Bank ledger NOT created - conditions not met:")
                    logger.warning(f"[SALE_LEDGER]   - Advance Amount > 0: {advance_amt > 0}")
                    logger.warning(f"[SALE_LEDGER]   - Advance Bank exists: {instance.advance_bank is not None}")
            else:
                logger.debug("[SALE_LEDGER] Not a credit sale with bank advance")
                logger.debug(f"[SALE_LEDGER]   - Payment Method == 'credit': {instance.payment_method == 'credit'}")
                logger.debug(f"[SALE_LEDGER]   - Advance Payment Method == 'bank': {instance.advance_payment_method == 'bank'}")

            # Cash ledger → handles:
            # 1. Direct cash sales (payment_method == "cash")
            # 2. Credit sales with cash advance (advance_payment_method == "cash")
            logger.debug("[SALE_LEDGER] Checking cash ledger creation...")
            logger.debug(f"[SALE_LEDGER] Payment Method: {instance.payment_method}")
            logger.debug(f"[SALE_LEDGER] Advance Payment Method: {instance.advance_payment_method}")
            logger.debug(f"[SALE_LEDGER] User: {instance.user}")
            
            cash_amount = Decimal(0)
            if instance.payment_method == "cash":
                # Full amount goes to cash for direct cash sales
                cash_amount = Decimal(instance.total_amount or 0)
                logger.info(f"[SALE_LEDGER] Direct cash sale detected - Cash Amount: {cash_amount}")
            elif instance.payment_method == "credit" and instance.advance_payment_method == "cash":
                # Only advance amount goes to cash for credit sales with cash advance
                logger.info("[SALE_LEDGER] Credit sale with cash advance detected")
                # Check both advance_amount and advance_payment_amount fields
                advance_amt = Decimal(instance.advance_amount or instance.advance_payment_amount or 0)
                logger.debug(f"[SALE_LEDGER] Advance Amount (from advance_amount): {instance.advance_amount}")
                logger.debug(f"[SALE_LEDGER] Advance Amount (from advance_payment_amount): {instance.advance_payment_amount}")
                logger.debug(f"[SALE_LEDGER] Calculated Advance Amount: {advance_amt}")
                logger.debug(f"[SALE_LEDGER] Advance Amount > 0: {advance_amt > 0}")
                
                if advance_amt > 0:
                    cash_amount = advance_amt
                    logger.info(f"[SALE_LEDGER] Cash amount set to advance amount: {cash_amount}")
                else:
                    logger.warning("[SALE_LEDGER] Advance amount is 0 or None - cash amount not set")
            else:
                logger.debug("[SALE_LEDGER] Not a cash sale or credit sale with cash advance")
                logger.debug(f"[SALE_LEDGER]   - Payment Method: {instance.payment_method}")
                logger.debug(f"[SALE_LEDGER]   - Advance Payment Method: {instance.advance_payment_method}")
            
            logger.debug(f"[SALE_LEDGER] Final Cash Amount: {cash_amount}")
            logger.debug(f"[SALE_LEDGER] Cash Amount > 0: {cash_amount > 0}")
            logger.debug(f"[SALE_LEDGER] User is not None: {instance.user is not None}")
            
            if cash_amount > 0 and instance.user is not None:
                logger.info("=" * 80)
                logger.info("[SALE_LEDGER] >>>>>> CREATING CASH LEDGER ENTRY <<<<<<")
                logger.info(f"[SALE_LEDGER] User: {instance.user} (ID: {instance.user.id})")
                logger.info(f"[SALE_LEDGER] Username: {instance.user.username}")
                logger.info(f"[SALE_LEDGER] Amount: {cash_amount}")
                logger.info(f"[SALE_LEDGER] Transaction Type: sale")
                logger.info(f"[SALE_LEDGER] Reference ID: {instance.id}")
                description = f"Sale #{instance.id}" + (" (Cash Advance)" if instance.payment_method == "credit" else "")
                logger.info(f"[SALE_LEDGER] Description: {description}")
                logger.info(f"[SALE_LEDGER] Payment Method: {instance.payment_method}")
                logger.info("[SALE_LEDGER] Calling create_ledger() for CashLedger...")
                logger.info("=" * 80)
                
                try:
                    create_ledger(
                        None,
                        CashLedger,
                        "sale",
                        instance.id,
                        cash_amount,
                        description,
                        user=instance.user
                    )
                    logger.info("=" * 80)
                    logger.info("[SALE_LEDGER] CASH LEDGER ENTRY CREATED SUCCESSFULLY")
                    logger.info(f"[SALE_LEDGER] User: {instance.user}")
                    logger.info(f"[SALE_LEDGER] Amount: {cash_amount}")
                    logger.info("=" * 80)
                except Exception as e:
                    logger.error("=" * 80)
                    logger.error("[SALE_LEDGER] ERROR CREATING CASH LEDGER")
                    logger.error(f"[SALE_LEDGER] Error: {str(e)}")
                    logger.error(f"[SALE_LEDGER] Error Type: {type(e).__name__}")
                    import traceback
                    logger.error(f"[SALE_LEDGER] Traceback: {traceback.format_exc()}")
                    logger.error("=" * 80)
            else:
                logger.warning("[SALE_LEDGER] Cash ledger NOT created - conditions not met:")
                logger.warning(f"[SALE_LEDGER]   - Cash Amount > 0: {cash_amount > 0}")
                logger.warning(f"[SALE_LEDGER]   - User is not None: {instance.user is not None}")
        
        logger.info("=" * 80)
        logger.info("[SALE_LEDGER] Signal processing completed")
        logger.info("=" * 80)
        # Transaction block ends here - all database operations are atomic
    except Exception as e:
        import traceback
        error_msg = f"[SALE_LEDGER] ERROR IN SIGNAL: {str(e)}"
        logger.error("=" * 80)
        logger.error(error_msg)
        logger.error(f"[SALE_LEDGER] Error Type: {type(e).__name__}")
        logger.error(f"[SALE_LEDGER] Traceback:")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        logger.error("=" * 80)
        # Re-raise to ensure Django knows about the error
        raise
    


# -------------------------------
# PURCHASE → Vendor & Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Purchase)
def purchase_ledger(sender, instance, created, **kwargs):
    """
    Signal handler for Purchase model to create ledger entries.
    Similar to sale_ledger - uses instance.total_amount directly after refresh.
    """
    try:
        logger.info("=" * 80)
        logger.info(f"[PURCHASE_LEDGER] Signal triggered for Purchase ID: {instance.id}")
        logger.info(f"[PURCHASE_LEDGER] Created: {created}")
        logger.info(f"[PURCHASE_LEDGER] Payment Method: {instance.payment_method}")
        logger.info(f"[PURCHASE_LEDGER] Advance Mode: {instance.advance_mode}")
        logger.info(f"[PURCHASE_LEDGER] Advance Amount: {instance.advance_amount}")
        logger.info(f"[PURCHASE_LEDGER] Advance Bank: {instance.advance_bank}")
        logger.info(f"[PURCHASE_LEDGER] Total Amount: {instance.total_amount}")
        logger.info(f"[PURCHASE_LEDGER] Balance Amount: {instance.balance_amount}")
        logger.info(f"[PURCHASE_LEDGER] User: {instance.user}")
        logger.info(f"[PURCHASE_LEDGER] Vendor: {instance.vendor}")

        # Wrap all database operations in a transaction
        with transaction.atomic():
            # Ensure we work with fresh values
            instance.refresh_from_db()
            
            # IMPORTANT (same as POS):
            # CashLedger/CashBalance must be created for the user who created the purchase (Purchase.user).
            # Signals don't have request.user, so NEVER guess/fallback to vendor.user (that can create ledgers
            # under the selected vendor/owner instead of the actual creator).
            if instance.user is None:
                logger.warning(
                    f"[PURCHASE_LEDGER] Purchase.user is None for Purchase #{instance.id}. "
                    f"Skipping cash/bank ledger adjustments for this purchase."
                )
            
            # Always recompute totals when items exist so delivery/packaging charges are included
            items_count = instance.items.count()
            logger.debug(f"[PURCHASE_LEDGER] Items count: {items_count}, total_amount after refresh: {instance.total_amount}")

            if items_count > 0:
                prev_total = Decimal(instance.total_amount or 0)
                instance.calculate_total()
                new_total = Decimal(instance.total_amount or 0)
                if new_total != prev_total:
                    Purchase.objects.filter(pk=instance.pk).update(
                        total_amount=instance.total_amount,
                        total_taxable_amount=instance.total_taxable_amount,
                        total_gst_amount=instance.total_gst_amount,
                    )
                    instance.refresh_from_db(fields=["total_amount", "total_taxable_amount", "total_gst_amount"])
                    logger.info(f"[PURCHASE_LEDGER] Totals updated: {prev_total} -> {instance.total_amount}")
            else:
                logger.warning("[PURCHASE_LEDGER] ⚠️ Purchase has no items yet - total_amount will be 0")
        
        # Delete old entries for this reference to ensure clean updates
        logger.debug("[PURCHASE_LEDGER] Deleting old ledger entries...")
        VendorLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()
        BankLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()
        CashLedger.objects.filter(transaction_type="purchase", reference_id=instance.id).delete()
        logger.debug("[PURCHASE_LEDGER] Old ledger entries deleted")

        # Recalculate cash balance (from remaining CashLedger entries)
        if instance.user:
            from .models import CashBalance
            cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
            remaining_total = (
                CashLedger.objects.filter(user=instance.user).aggregate(total=Sum("amount"))["total"] or 0
            )
            cash_balance.balance = Decimal(remaining_total or 0)
            cash_balance.save()
            logger.debug(f"[PURCHASE_LEDGER] Cash balance recalculated: {cash_balance.balance}")

        # Recalculate bank balance (from remaining BankLedger entries) if needed
        # Handle both bank (for UPI/cheque payments) and advance_bank (for credit advance payments)
        if instance.bank:
            bank = instance.bank
            remaining_total = (
                BankLedger.objects.filter(bank=bank).aggregate(total=Sum("amount"))["total"] or 0
            )
            # Bank balance = opening_balance + sum(all bank ledger entries)
            bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
            bank.save(update_fields=["balance"])
            logger.debug(f"[PURCHASE_LEDGER] Bank balance recalculated: {bank.balance}")
        
        if instance.advance_bank:
            bank = instance.advance_bank
            remaining_total = (
                BankLedger.objects.filter(bank=bank).aggregate(total=Sum("amount"))["total"] or 0
            )
            # Bank balance = opening_balance + sum(all bank ledger entries)
            bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
            bank.save(update_fields=["balance"])
            logger.debug(f"[PURCHASE_LEDGER] Advance bank balance recalculated: {bank.balance}")

        # Create vendor ledger entries
        if instance.vendor:
            vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
            total_amt = Decimal(instance.total_amount or 0)
            balance_amt = Decimal(instance.balance_amount or 0)
            advance_amt_effective = Decimal(instance.advance_amount or instance.advance_payment_amount or 0)

            # For CREDIT purchases, ensure balance_amount represents remaining due:
            # remaining = total - advance (best-effort) if not already set.
            if instance.payment_method == "credit" and total_amt > 0:
                computed_remaining = total_amt - advance_amt_effective
                if computed_remaining < 0:
                    computed_remaining = Decimal(0)
                # If balance_amount is missing/0 or mismatched, persist the computed value
                if balance_amt != computed_remaining:
                    Purchase.objects.filter(pk=instance.pk).update(balance_amount=computed_remaining)
                    instance.refresh_from_db(fields=["balance_amount"])
            balance_amt = Decimal(instance.balance_amount or 0)
            
            # Create vendor ledger entries for ALL purchases (for audit/tracking)
            # Vendor ledger:
            # - For CREDIT purchases, record ONLY remaining due (balance_amount = total - advance)
            # - For non-credit purchases, record full total_amount (for tracking, but won't affect balance)
            if instance.payment_method == "credit":
                if balance_amt > 0:
                    create_ledger(
                        vendor,
                        VendorLedger,
                        "purchase",
                        instance.id,
                        balance_amt,
                        f"Purchase #{instance.id} (Credit)",
                    )
            else:
                if total_amt > 0:
                    create_ledger(
                        vendor,
                        VendorLedger,
                        "purchase",
                        instance.id,
                        total_amt,
                        f"Purchase #{instance.id}",
                    )
            
            # Reset vendor running balance from opening + sum(ONLY credit purchase ledger entries)
            # Only credit purchases affect vendor balance - non-credit purchases are already paid
            # Credit entries are identified by description containing "(Credit)"
            credit_ledger_total = (
                VendorLedger.objects.filter(
                    vendor=vendor,
                    description__contains="(Credit)"
                ).aggregate(total=Sum("amount"))["total"] or 0
            )
            # Also include payment entries (which reduce credit balance)
            payment_ledger_total = (
                VendorLedger.objects.filter(
                    vendor=vendor,
                    transaction_type="payment"
                ).aggregate(total=Sum("amount"))["total"] or 0
            )
            # Total credit balance = opening_balance + credit purchases - payments
            opening_balance = Decimal(vendor.opening_balance or 0) + Decimal(credit_ledger_total or 0) + Decimal(payment_ledger_total or 0)
            vendor.balance = opening_balance
            vendor.save(update_fields=["balance"])

        # Cash/Bank ledger for purchases
        # LOGIC:
        # 1. If payment_method == "cash" → deduct full total_amount from cash
        # 2. If payment_method in ("upi","cheque") → deduct full total_amount from bank (bank field, similar to Expense)
        # 3. If payment_method == "credit":
        #    - If advance_mode == "cash" → deduct advance_amount from cash
        #    - If advance_mode == "bank" → deduct advance_amount from bank (advance_bank)
        
        if instance.payment_method == "cash" and instance.user is not None:
            cash_amount = Decimal(instance.total_amount or 0)
            adjust_ledger_to_target(
                None,
                CashLedger,
                "purchase",
                instance.id,
                -cash_amount,  # Negative amount to DECREASE cash balance
                f"Purchase #{instance.id} (Cash)",
                user=instance.user,
            )
        
        elif instance.payment_method in ["upi", "cheque"]:
            # Use bank field (similar to Expense) - fallback to advance_bank for backward compatibility
            bank_to_use = instance.bank or instance.advance_bank
            if bank_to_use:
                bank_amount = Decimal(instance.total_amount or 0)
                create_ledger(
                    bank_to_use,
                    BankLedger,
                    "purchase",
                    instance.id,
                    -bank_amount,  # Negative amount to DECREASE bank balance
                    f"Purchase #{instance.id} ({instance.payment_method.upper()})",
                )
                logger.info(f"[PURCHASE_LEDGER] Bank ledger created for Purchase #{instance.id} using bank: {bank_to_use.name}")
            else:
                logger.warning(
                    f"[PURCHASE_LEDGER] ⚠️ {instance.payment_method.upper()} payment selected but bank/advance_bank is not set! Bank ledger not created."
                )
        
        elif instance.payment_method == "credit":
            advance_amt = Decimal(instance.advance_amount or instance.advance_payment_amount or 0)
            
            if advance_amt > 0:
                if instance.advance_mode == "cash" and instance.user is not None:
                    adjust_ledger_to_target(
                        None,
                        CashLedger,
                        "purchase",
                        instance.id,
                        -advance_amt,  # Negative amount to DECREASE cash balance
                        f"Purchase #{instance.id} (Credit - Cash Advance)",
                            user=instance.user,
                    )
                elif instance.advance_mode == "bank" and instance.advance_bank:
                    adjust_ledger_to_target(
                        instance.advance_bank,
                        BankLedger,
                        "purchase",
                        instance.id,
                        -advance_amt,  # Negative amount to DECREASE bank balance
                            f"Purchase #{instance.id} (Credit - Bank Advance)",
                    )
                else:
                        logger.warning(
                            "[PURCHASE_LEDGER] Credit purchase with advance but advance_mode/advance_bank not set correctly"
                        )
        
        logger.info("=" * 80)
        logger.info("[PURCHASE_LEDGER] Signal processing completed")
        logger.info("=" * 80)

    except Exception as e:
        import traceback

        error_msg = f"[PURCHASE_LEDGER] ERROR IN SIGNAL: {str(e)}"
        logger.error("=" * 80)
        logger.error(error_msg)
        logger.error(f"[PURCHASE_LEDGER] Error Type: {type(e).__name__}")
        logger.error("[PURCHASE_LEDGER] Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        raise


# -------------------------------
# EXPENSE → ExpenseLedger + Bank Ledger (+ CashLedger)
# -------------------------------
@receiver(post_save, sender=Expense)
def expense_ledger(sender, instance, created, **kwargs):
    # Delete old entries for this reference to ensure clean updates
    ExpenseLedger.objects.filter(expense=instance).delete()
    BankLedger.objects.filter(transaction_type="expense", reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type="expense", reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.bank:
        bank = instance.bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        # Bank balance = opening_balance + sum(all bank ledger entries)
        bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
        bank.save(update_fields=['balance'])

    if instance.user:
        from .models import CashBalance
        cash_balance, _ = CashBalance.objects.get_or_create(user=instance.user)
        remaining_total = CashLedger.objects.filter(user=instance.user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        cash_balance.balance = Decimal(remaining_total or 0)
        cash_balance.save()

    # Create ExpenseLedger entry (dedicated expense ledger with category)
    if instance.user and instance.category:
        ExpenseLedger.objects.create(
            user=instance.user,
            expense=instance,
            category=instance.category,
            amount=instance.amount or Decimal(0),
            payment_method=instance.payment_method,
            bank=instance.bank,
            expense_date=instance.expense_date,
            description=instance.description or ''
        )

    # Create BankLedger entry (for bank balance tracking)
    if instance.bank:
        create_ledger(
            instance.bank,
            BankLedger,
            "expense",
            instance.id,
            -(instance.amount or Decimal(0)),
            f"Expense #{instance.id} - {instance.category}" if instance.category else f"Expense #{instance.id}"
        )

    # Create CashLedger entry (for cash balance tracking)
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

    logger.info("=" * 80)
    logger.info(f"[PAYMENT_LEDGER] Signal triggered for Payment ID: {instance.id}")
    logger.info(f"[PAYMENT_LEDGER] Type: {instance.type}")
    logger.info(f"[PAYMENT_LEDGER] Payment Type: {instance.payment_type}")
    logger.info(f"[PAYMENT_LEDGER] Amount: {amt}")
    logger.info(f"[PAYMENT_LEDGER] Customer: {instance.customer}")
    logger.info(f"[PAYMENT_LEDGER] Vendor: {instance.vendor}")
    logger.info(f"[PAYMENT_LEDGER] Bank: {instance.bank}")
    logger.info("=" * 80)

    # Wrap all database operations in a transaction
    with transaction.atomic():
        # Refresh instance from database to ensure we have latest values
        instance.refresh_from_db()
        logger.debug("[PAYMENT_LEDGER] Instance refreshed from database")
        
        # Delete old entries for this reference to ensure clean updates
        logger.debug("[PAYMENT_LEDGER] Deleting old ledger entries...")
        CustomerLedger.objects.filter(transaction_type__in=["payment", "refund"], reference_id=instance.id).delete()
        VendorLedger.objects.filter(transaction_type__in=["payment", "refund"], reference_id=instance.id).delete()
        CashLedger.objects.filter(transaction_type__in=["deposit", "withdrawal", "payment", "cash_transfer"], reference_id=instance.id).delete()
        BankLedger.objects.filter(transaction_type__in=["deposit", "withdrawal", "payment"], reference_id=instance.id).delete()
        logger.debug("[PAYMENT_LEDGER] Old ledger entries deleted")

        # Recalculate balances from ALL remaining ledger entries (not just this transaction)
        # This ensures balances are correct before creating new entries
        # Customer balance = opening_balance + sum of all ledger entries
        if instance.customer:
            customer = vendor_customers.objects.get(pk=instance.customer.pk)
            ledger_total = CustomerLedger.objects.filter(customer=customer).aggregate(
                total=Sum('amount')
            )['total'] or 0
            # Customer balance = opening_balance + sum of ledger entries
            customer.balance = Decimal(customer.opening_balance or 0) + Decimal(ledger_total or 0)
            customer.save(update_fields=['balance'])
            logger.debug(f"[PAYMENT_LEDGER] Customer balance recalculated: {customer.balance} (opening: {customer.opening_balance}, ledger: {ledger_total})")

        if instance.vendor:
            vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
            ledger_total = VendorLedger.objects.filter(vendor=vendor).aggregate(
                total=Sum('amount')
            )['total'] or 0
            # Vendor balance = opening_balance + sum of ledger entries
            vendor.balance = Decimal(vendor.opening_balance or 0) + Decimal(ledger_total or 0)
            vendor.save(update_fields=['balance'])
            logger.debug(f"[PAYMENT_LEDGER] Vendor balance recalculated: {vendor.balance} (opening: {vendor.opening_balance}, ledger: {ledger_total})")

        # Customer ledger
        if instance.customer:
            customer = vendor_customers.objects.get(pk=instance.customer.pk)
            customer.refresh_from_db()
            
            # Get existing ledger entries to check if this is the first one
            existing_ledgers = CustomerLedger.objects.filter(customer=customer)
            is_first_ledger = not existing_ledgers.exists()
            
            if instance.type == "received":
                # Customer paid you (received payment) - customer balance DECREASES
                # Ledger entry should be negative to decrease balance
                logger.info(f"[PAYMENT_LEDGER] Creating customer ledger for RECEIVED payment")
                logger.info(f"[PAYMENT_LEDGER] Is first ledger: {is_first_ledger}")
                logger.info(f"[PAYMENT_LEDGER] Customer opening_balance: {customer.opening_balance}")
                
                # Calculate opening balance for this ledger entry
                ledger_total_before = CustomerLedger.objects.filter(customer=customer).aggregate(
                    total=Sum('amount')
                )['total'] or 0
                opening_balance_for_entry = Decimal(customer.opening_balance or 0) + Decimal(ledger_total_before)
                
                create_ledger(
                    customer,
                    CustomerLedger,
                    "payment",
                    instance.id,
                    -amt,  # Negative amount to decrease customer balance
                    f"Payment Received ({payment_type_display}) #{instance.id}"
                )
                logger.info(f"[PAYMENT_LEDGER] Customer ledger created with amount: -{amt}")
            elif instance.type == "gave":
                # You gave refund to customer - customer balance INCREASES
                # Ledger entry should be positive to increase balance
                logger.info(f"[PAYMENT_LEDGER] Creating customer ledger for GAVE payment (refund)")
                logger.info(f"[PAYMENT_LEDGER] Is first ledger: {is_first_ledger}")
                logger.info(f"[PAYMENT_LEDGER] Customer opening_balance: {customer.opening_balance}")
                
                create_ledger(
                    customer,
                    CustomerLedger,
                    "refund",
                    instance.id,
                    amt,  # Positive amount to increase customer balance
                    f"Refund Given ({payment_type_display}) #{instance.id}"
                )
                logger.info(f"[PAYMENT_LEDGER] Customer ledger created with amount: {amt}")

        # Vendor ledger
        if instance.vendor:
            vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
            vendor.refresh_from_db()
            
            # Get existing ledger entries to check if this is the first one
            existing_ledgers = VendorLedger.objects.filter(vendor=vendor)
            is_first_ledger = not existing_ledgers.exists()
            
            if instance.type == "gave":
                # You gave payment to vendor - vendor balance INCREASES
                # Ledger entry should be negative to decrease what you owe (vendor balance increases)
                logger.info(f"[PAYMENT_LEDGER] Creating vendor ledger for GAVE payment")
                logger.info(f"[PAYMENT_LEDGER] Is first ledger: {is_first_ledger}")
                logger.info(f"[PAYMENT_LEDGER] Vendor opening_balance: {vendor.opening_balance}")
                
                # Calculate opening balance for this ledger entry
                ledger_total_before = VendorLedger.objects.filter(vendor=vendor).aggregate(
                    total=Sum('amount')
                )['total'] or 0
                opening_balance_for_entry = Decimal(vendor.opening_balance or 0) + Decimal(ledger_total_before)
                
                create_ledger(
                    vendor,
                    VendorLedger,
                    "payment",
                    instance.id,
                    -amt,  # Negative amount in vendor ledger means you owe less (vendor balance increases)
                    f"Payment Given ({payment_type_display}) #{instance.id}"
                )
                logger.info(f"[PAYMENT_LEDGER] Vendor ledger created with amount: -{amt}")
            elif instance.type == "received":
                # Vendor gave you refund - vendor balance DECREASES
                # Ledger entry should be positive to increase what you owe (vendor balance decreases)
                logger.info(f"[PAYMENT_LEDGER] Creating vendor ledger for RECEIVED payment (refund)")
                logger.info(f"[PAYMENT_LEDGER] Is first ledger: {is_first_ledger}")
                logger.info(f"[PAYMENT_LEDGER] Vendor opening_balance: {vendor.opening_balance}")
                
                create_ledger(
                    vendor,
                    VendorLedger,
                    "refund",
                    instance.id,
                    amt,  # Positive amount in vendor ledger means you owe more (vendor balance decreases)
                    f"Refund Received ({payment_type_display}) #{instance.id}"
                )
                logger.info(f"[PAYMENT_LEDGER] Vendor ledger created with amount: {amt}")

        # Cash/Bank ledger for payments
        # CORRECTED LOGIC:
        # If "received" → you received money, so cash/bank balance should INCREASE (positive amount)
        # If "gave" → you gave money, so cash/bank balance should DECREASE (negative amount)
        
        # Cash ledger for cash payments
        if instance.payment_type == "cash" and instance.user is not None:
            if instance.type == "received":
                # You received payment → cash balance INCREASES (add/plus)
                logger.info(f"[PAYMENT_LEDGER] Creating cash ledger for RECEIVED payment (cash)")
                adjust_ledger_to_target(
                    None,
                    CashLedger,
                    "deposit",
                    instance.id,
                    amt,  # Positive amount to INCREASE balance
                    f"Cash Payment Received #{instance.id}",
                    user=instance.user
                )
                logger.info(f"[PAYMENT_LEDGER] Cash ledger created with amount: {amt} (INCREASE)")
            elif instance.type == "gave":
                # You gave payment → cash balance DECREASES (minus/subtract)
                logger.info(f"[PAYMENT_LEDGER] Creating cash ledger for GAVE payment (cash)")
                adjust_ledger_to_target(
                    None,
                    CashLedger,
                    "payment",
                    instance.id,
                    -amt,  # Negative amount to DECREASE balance
                    f"Cash Payment Given #{instance.id}",
                    user=instance.user
                )
                logger.info(f"[PAYMENT_LEDGER] Cash ledger created with amount: -{amt} (DECREASE)")
        
        # Bank ledger for bank payments (upi/cheque/bank)
        # Create bank ledger if bank is set AND payment_type is one of the bank payment types
        logger.debug(f"[PAYMENT_LEDGER] Checking bank ledger creation...")
        logger.debug(f"[PAYMENT_LEDGER] Bank: {instance.bank}")
        logger.debug(f"[PAYMENT_LEDGER] Payment Type: {instance.payment_type}")
        logger.debug(f"[PAYMENT_LEDGER] Bank is set: {instance.bank is not None}")
        logger.debug(f"[PAYMENT_LEDGER] Payment type in ['upi', 'cheque', 'bank']: {instance.payment_type in ['upi', 'cheque', 'bank']}")
        
        if instance.bank and instance.payment_type in ["upi", "cheque", "bank"]:
            logger.info(f"[PAYMENT_LEDGER] Bank payment detected - Bank: {instance.bank}, Payment Type: {instance.payment_type}")
            if instance.type == "received":
                # You received payment → bank balance INCREASES (add/plus)
                logger.info(f"[PAYMENT_LEDGER] Creating bank ledger for RECEIVED payment (bank)")
                logger.info(f"[PAYMENT_LEDGER] Bank: {instance.bank} (ID: {instance.bank.id})")
                logger.info(f"[PAYMENT_LEDGER] Amount: {amt}")
                adjust_ledger_to_target(
                    instance.bank,
                    BankLedger,
                    "deposit",
                    instance.id,
                    amt,  # Positive amount to INCREASE balance
                    f"Bank Payment Received ({instance.payment_type}) #{instance.id}"
                )
                logger.info(f"[PAYMENT_LEDGER] Bank ledger created with amount: {amt} (INCREASE)")
            elif instance.type == "gave":
                # You gave payment → bank balance DECREASES (minus/subtract)
                logger.info(f"[PAYMENT_LEDGER] Creating bank ledger for GAVE payment (bank)")
                logger.info(f"[PAYMENT_LEDGER] Bank: {instance.bank} (ID: {instance.bank.id})")
                logger.info(f"[PAYMENT_LEDGER] Amount: {amt}")
                adjust_ledger_to_target(
                    instance.bank,
                    BankLedger,
                    "withdrawal",
                    instance.id,
                    -amt,  # Negative amount to DECREASE balance
                    f"Bank Payment Given ({instance.payment_type}) #{instance.id}"
                )
                logger.info(f"[PAYMENT_LEDGER] Bank ledger created with amount: -{amt} (DECREASE)")
        else:
            if not instance.bank:
                logger.warning("[PAYMENT_LEDGER] Bank is not set - bank ledger not created")
            elif instance.payment_type == "cash":
                logger.debug("[PAYMENT_LEDGER] Payment type is 'cash' - bank ledger not created (cash ledger will be created instead)")
            else:
                logger.warning("[PAYMENT_LEDGER] Bank ledger not created - unknown reason")
        
        logger.info("=" * 80)
        logger.info("[PAYMENT_LEDGER] Signal processing completed")
        logger.info("=" * 80)


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
            "cash_transfer",
            instance.id,
            -(instance.amount or Decimal(0)),
            f"Cash Transfer to {instance.bank_account.name}",
            user=instance.user
        )

        # Adjust bank
        adjust_ledger_to_target(
            instance.bank_account,
            BankLedger,
            "deposit",
            instance.id,
            (instance.amount or Decimal(0)),
            f"Cash Transfer from Cash"
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
        customer.balance = Decimal(customer.opening_balance or 0) + Decimal(remaining_total or 0)
        customer.save(update_fields=['balance'])

    if instance.bank:
        bank = instance.bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
        bank.save(update_fields=['balance'])

    if instance.advance_bank:
        bank = instance.advance_bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        # Bank balance = opening_balance + sum(all bank ledger entries)
        bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
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
        # Vendor balance = opening_balance + sum(all vendor ledger entries)
        vendor.balance = Decimal(vendor.opening_balance or 0) + Decimal(remaining_total or 0)
        vendor.save(update_fields=['balance'])

    # Handle both bank (for UPI/cheque payments) and advance_bank (for credit advance payments)
    if instance.bank:
        bank = instance.bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        # Bank balance = opening_balance + sum(all bank ledger entries)
        bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
        bank.save(update_fields=['balance'])
    
    if instance.advance_bank:
        bank = instance.advance_bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        # Bank balance = opening_balance + sum(all bank ledger entries)
        bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
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
    ExpenseLedger.objects.filter(expense=instance).delete()
    BankLedger.objects.filter(transaction_type="expense", reference_id=instance.id).delete()
    CashLedger.objects.filter(transaction_type="expense", reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.bank:
        bank = instance.bank
        remaining_total = BankLedger.objects.filter(bank=bank).aggregate(
            total=Sum('amount')
        )['total'] or 0
        # Bank balance = opening_balance + sum(all bank ledger entries)
        bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
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
    CashLedger.objects.filter(transaction_type__in=["deposit", "withdrawal", "cash_transfer"], reference_id=instance.id).delete()
    BankLedger.objects.filter(transaction_type__in=["deposit", "withdrawal", "payment"], reference_id=instance.id).delete()

    # Recalculate balances from ALL remaining ledger entries
    if instance.customer:
        customer = vendor_customers.objects.get(pk=instance.customer.pk)
        remaining_total = CustomerLedger.objects.filter(customer=customer).aggregate(
            total=Sum('amount')
        )['total'] or 0
        customer.balance = Decimal(customer.opening_balance or 0) + Decimal(remaining_total or 0)
        customer.save(update_fields=['balance'])

    if instance.vendor:
        vendor = vendor_vendors.objects.get(pk=instance.vendor.pk)
        remaining_total = VendorLedger.objects.filter(vendor=vendor).aggregate(
            total=Sum('amount')
        )['total'] or 0
        vendor.balance = Decimal(vendor.opening_balance or 0) + Decimal(remaining_total or 0)
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
        # Bank balance = opening_balance + sum(all bank ledger entries)
        bank.balance = Decimal(bank.opening_balance or 0) + Decimal(remaining_total or 0)
        bank.save(update_fields=['balance'])


@receiver(post_delete, sender=CashTransfer)
def cash_transfer_delete_ledger(sender, instance, **kwargs):
    reset_ledger_for_reference(CashLedger, "cash_transfer", instance.id)
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
        
        sale = instance.sale
        customer = getattr(sale, "customer", None) if sale else None
        phone = getattr(customer, "contact", None) if customer else None
        customer_name = getattr(customer, "name", None) if customer else None
        
        # Only send SMS when invoice is created (not on every update)
        if created and sale:
            signal_logger.info("[SMS SIGNAL] New wholesale invoice created, scheduling send_sale_sms() on commit...")

            # IMPORTANT:
            # In API create flow, Sale totals are recalculated AFTER the wholesale invoice is saved.
            # If we send SMS inside this signal immediately, we often pick up stale totals (amount=0).
            # Using transaction.on_commit ensures totals have been finalized.
            def _send_sms_after_commit():
                try:
                    sale.refresh_from_db()
                except Exception:
                    pass
                success, msg = send_sale_sms(sale, instance.invoice_type)
                # Summary line (easy to grep) goes to signals.log + terminal
                signal_logger.info(
                    f"[SMS SUMMARY] sale_id={sale.id} invoice_id={instance.id} invoice_type={instance.invoice_type} "
                    f"customer={customer_name} phone={phone} result={'SENT' if success else 'NOT_SENT'} reason={msg}"
                )

            transaction.on_commit(_send_sms_after_commit)
        else:
            reason = f"created={created}, has_sale={bool(sale)}"
            signal_logger.info(f"[SMS SIGNAL] Skipping SMS ({reason})")
            signal_logger.info(
                f"[SMS SUMMARY] sale_id={getattr(sale, 'id', None)} invoice_id={instance.id} invoice_type={instance.invoice_type} "
                f"customer={customer_name} phone={phone} result=SKIPPED reason={reason}"
            )
    except Exception as e:
        # Don't fail the invoice if SMS sending fails - just log the error
        import logging
        logger = logging.getLogger(__name__)
        error_msg = f"Failed to send SMS for wholesale invoice {instance.id}: {str(e)}"
        logger.error(f"[SMS SIGNAL] EXCEPTION: {error_msg}")
        logger.exception("SMS signal exception details")


#-------------------------------------------------------

# -------------------------------
# POS (NON-WHOLESALE) → Send SMS
# -------------------------------
@receiver(pre_save, sender=Sale)
def _capture_sale_sms_state(sender, instance, **kwargs):
    """
    Capture previous Sale total to avoid re-sending SMS on every update.
    We send SMS when:
      - Sale is created (and total > 0), OR
      - total_amount transitions from 0 -> >0 (common when items are added after create)
    """
    try:
        from decimal import Decimal
        if instance.pk is None:
            instance._sms_old_total_amount = Decimal("0")
            return
        old = Sale.objects.filter(pk=instance.pk).only("total_amount").first()
        instance._sms_old_total_amount = Decimal(getattr(old, "total_amount", 0) or 0) if old else Decimal("0")
    except Exception:
        return


@receiver(post_save, sender=Sale)
def pos_sale_sms_any(sender, instance, created, **kwargs):
    """
    Send SMS for ANY POS sale (non-wholesale).
    Wholesale invoice SMS is handled by pos_wholesale_sms.
    """
    try:
        import logging
        from decimal import Decimal
        from datetime import datetime
        from django.db import transaction
        from .sms_utils import send_sale_sms

        # Wholesale sales are handled via pos_wholesale invoices
        if bool(getattr(instance, "is_wholesale_rate", False)):
            return

        # Must have a customer + creator user for SMS settings
        if not getattr(instance, "customer", None) or not getattr(instance, "user", None):
            return

        signal_logger = logging.getLogger(__name__)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_total = Decimal(getattr(instance, "total_amount", 0) or 0)
        old_total = getattr(instance, "_sms_old_total_amount", Decimal("0"))

        should_send = False
        if created and new_total > 0:
            should_send = True
            reason = "created_with_total"
        elif (old_total == 0) and (new_total > 0):
            should_send = True
            reason = "total_transition_0_to_positive"
        else:
            reason = f"created={created}, old_total={old_total}, new_total={new_total}"

        if not should_send:
            signal_logger.info(f"[SMS SIGNAL] [{timestamp}] POS sale SMS skipped (Sale #{instance.id}) reason={reason}")
            return

        def _send_sms_after_commit():
            try:
                instance.refresh_from_db()
            except Exception:
                pass
            success, msg = send_sale_sms(instance, "invoice")
            signal_logger.info(
                f"[SMS SUMMARY] sale_id={instance.id} invoice_id=None invoice_type=invoice "
                f"customer={getattr(getattr(instance, 'customer', None), 'name', None)} "
                f"phone={getattr(getattr(instance, 'customer', None), 'contact', None)} "
                f"result={'SENT' if success else 'NOT_SENT'} reason={msg} trigger={reason}"
            )

        transaction.on_commit(_send_sms_after_commit)
    except Exception:
        return


# -------------------------------
# PURCHASE → Send SMS (to user + vendor)
# -------------------------------
@receiver(pre_save, sender=Purchase)
def _capture_purchase_sms_state(sender, instance, **kwargs):
    try:
        from decimal import Decimal
        if instance.pk is None:
            instance._sms_old_total_amount = Decimal("0")
            return
        old = Purchase.objects.filter(pk=instance.pk).only("total_amount").first()
        instance._sms_old_total_amount = Decimal(getattr(old, "total_amount", 0) or 0) if old else Decimal("0")
    except Exception:
        return


@receiver(post_save, sender=Purchase)
def purchase_sms_to_customer_and_vendor(sender, instance, created, **kwargs):
    """
    Send Purchase SMS to:
      - Purchase.user.mobile (creator / "customer" side)
      - Purchase.vendor.contact (supplier / vendor)

    Trigger when created (and total > 0) OR when total becomes >0 after items are added.
    """
    try:
        import logging
        from decimal import Decimal
        from datetime import datetime
        from django.db import transaction
        from .sms_utils import send_purchase_sms

        if not getattr(instance, "user", None):
            return

        signal_logger = logging.getLogger(__name__)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_total = Decimal(getattr(instance, "total_amount", 0) or 0)
        old_total = getattr(instance, "_sms_old_total_amount", Decimal("0"))

        should_send = False
        if created and new_total > 0:
            should_send = True
            reason = "created_with_total"
        elif (old_total == 0) and (new_total > 0):
            should_send = True
            reason = "total_transition_0_to_positive"
        else:
            reason = f"created={created}, old_total={old_total}, new_total={new_total}"

        if not should_send:
            signal_logger.info(f"[SMS SIGNAL] [{timestamp}] Purchase SMS skipped (Purchase #{instance.id}) reason={reason}")
            return

        def _send_sms_after_commit():
            try:
                instance.refresh_from_db()
            except Exception:
                pass
            success, msg = send_purchase_sms(instance, send_to_user=True, send_to_vendor=True)
            signal_logger.info(
                f"[SMS SUMMARY] purchase_id={instance.id} result={'SENT' if success else 'NOT_SENT'} reason={msg} trigger={reason}"
            )

        transaction.on_commit(_send_sms_after_commit)
    except Exception:
        return



# signals.py
from django.db.models.signals import post_save
from django.db.models import F
from django.dispatch import receiver
from vendor.models import product
from .models import PurchaseItem, StockTransaction, SaleItem, OnlineOrderLedger
from customer.models import OrderItem, ReturnExchange, Order




def log_stock_transaction(product_obj, txn_type, qty, ref_id=None):
    """Create a stock transaction record."""
    StockTransaction.objects.create(
        product=product_obj,
        transaction_type=txn_type,
        quantity=qty,
        reference_id=ref_id,
    )


def _recalculate_purchase_totals_and_trigger_ledger(purchase_obj):
    """
    Recalculate purchase totals (including delivery/packaging) whenever items change,
    and save the Purchase so the Purchase post_save ledger signal runs with correct totals.
    """
    if not purchase_obj:
        return
    try:
        purchase_obj.refresh_from_db()
        purchase_obj.calculate_total()
        # Persist only totals fields; this triggers Purchase post_save -> purchase_ledger
        purchase_obj.save(update_fields=["total_amount", "total_taxable_amount", "total_gst_amount"])
    except Exception:
        # Never break stock updates if totals/ledger fails; logging is handled by purchase_ledger
        return


# -----------------------------------------------------------------------------
# 🟢 PURCHASE (+ stock)
# -----------------------------------------------------------------------------
@receiver(post_save, sender=PurchaseItem)
def increase_stock_on_purchase_create(sender, instance, created, **kwargs):
    """Handle stock increase when a new PurchaseItem is created."""
    if created:
        product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + instance.quantity)
        log_stock_transaction(instance.product, "purchase", instance.quantity, ref_id=instance.pk)
    # Recalculate purchase totals & ledgers for both create and update
    _recalculate_purchase_totals_and_trigger_ledger(getattr(instance, "purchase", None))

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
    _recalculate_purchase_totals_and_trigger_ledger(getattr(instance, "purchase", None))




# -----------------------------------------------------------------------------
# 🔵 SALE (POS)
# -----------------------------------------------------------------------------
@receiver(post_save, sender=SaleItem)
def reduce_stock_on_sale_create(sender, instance, created, **kwargs):
    """Handle stock reduction when a new SaleItem is created."""
    if created:
        # Check if we should process this sale (ledger/stock operations)
        should_process, reason = should_process_sale(instance.sale)
        if not should_process:
            logger.debug(f"[STOCK] Skipping stock reduction for SaleItem ID: {instance.id}, Sale ID: {instance.sale.id}, Reason: {reason}")
            return
        
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

    # Check if we should process this sale (ledger/stock operations)
    should_process, reason = should_process_sale(instance.sale)
    if not should_process:
        logger.debug(f"[STOCK] Skipping stock update for SaleItem ID: {instance.id}, Sale ID: {instance.sale.id}, Reason: {reason}")
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
    # Check if we should process this sale (ledger/stock operations)
    # Note: For delete, we still need to restore stock if it was previously reduced
    # So we check if the sale was processed (had stock reduced) before deciding to restore
    should_process, reason = should_process_sale(instance.sale)
    if not should_process:
        logger.debug(f"[STOCK] Skipping stock restoration for SaleItem ID: {instance.id}, Sale ID: {instance.sale.id}, Reason: {reason}")
        return
    
    product.objects.filter(id=instance.product.id).update(stock_cached=F('stock_cached') + instance.quantity)
    log_stock_transaction(instance.product, "sale", instance.quantity, ref_id=instance.pk)


# -----------------------------------------------------------------------------
# 🔵 SERIAL/IMEI NUMBER TRACKING FOR SALES
# -----------------------------------------------------------------------------
@receiver(pre_save, sender=SaleItem)
def store_old_serial_imei_before_save(sender, instance, **kwargs):
    """
    Store old serial/IMEI number ID before save for comparison.
    This runs before save, so we can check what changed.
    """
    # Skip if this is a new item
    if instance.pk is None:
        instance._old_serial_id = None
        return
    
    try:
        old_instance = SaleItem.objects.get(pk=instance.pk)
        # Get old serial/IMEI number that was linked (OneToOne)
        instance._old_serial_id = old_instance.serial_imei_number.id if old_instance.serial_imei_number else None
    except SaleItem.DoesNotExist:
        instance._old_serial_id = None


@receiver(post_save, sender=SaleItem)
def track_serial_imei_on_sale_item_save(sender, instance, created, **kwargs):
    """
    Handle serial/IMEI number tracking when a SaleItem is created or updated.
    - For new items: Mark linked serial as sold
    - For updated items: Restore removed serial, mark new one as sold
    
    This signal runs AFTER the SaleItem is saved, so the serial_imei_number relationship
    should be established if it was set in the serializer.
    """
    from .models import serial_imei_no
    
    # Check if we should process this sale
    should_process, reason = should_process_sale(instance.sale)
    if not should_process:
        logger.debug(f"[SERIAL_TRACK] Skipping serial tracking for SaleItem ID: {instance.id}, Reason: {reason}")
        return
    
    # Refresh from DB to ensure we have the latest serial_imei_number relationship
    instance.refresh_from_db(fields=['serial_imei_number'])
    
    # Get current serial/IMEI number linked to this sale item (OneToOne)
    current_serial = instance.serial_imei_number
    current_serial_id = current_serial.id if current_serial else None
    
    if created:
        # For new items, mark linked serial as sold (if it exists)
        # Note: Serial might be set after first save in serializer, so this handles both cases
        if current_serial_id:
            serial_imei_no.objects.filter(id=current_serial_id).update(is_sold=True)
            logger.info(f"[SERIAL_TRACK] ✅ Marked serial/IMEI number (ID: {current_serial_id}, Value: {current_serial.value}) as sold for new SaleItem ID: {instance.id}")
        else:
            logger.debug(f"[SERIAL_TRACK] No serial/IMEI number linked to new SaleItem ID: {instance.id} (may be set in subsequent save)")
    else:
        # For updated items, handle changes
        old_serial_id = getattr(instance, '_old_serial_id', None)
        
        # If serial was removed (old exists but current doesn't)
        if old_serial_id and not current_serial_id:
            # Restore removed serial (mark as not sold)
            serial_imei_no.objects.filter(id=old_serial_id).update(is_sold=False)
            logger.info(f"[SERIAL_TRACK] ✅ Restored serial/IMEI number (ID: {old_serial_id}) - marked as not sold for SaleItem ID: {instance.id}")
        
        # If serial was added or changed (current exists and is different from old)
        if current_serial_id and current_serial_id != old_serial_id:
            # Mark new serial as sold
            serial_imei_no.objects.filter(id=current_serial_id).update(is_sold=True)
            logger.info(f"[SERIAL_TRACK] ✅ Marked serial/IMEI number (ID: {current_serial_id}, Value: {current_serial.value}) as sold for SaleItem ID: {instance.id}")
            
            # If old serial exists and is different, restore it
            if old_serial_id and old_serial_id != current_serial_id:
                serial_imei_no.objects.filter(id=old_serial_id).update(is_sold=False)
                logger.info(f"[SERIAL_TRACK] ✅ Restored old serial/IMEI number (ID: {old_serial_id}) - marked as not sold for SaleItem ID: {instance.id}")


@receiver(post_delete, sender=SaleItem)
def restore_serial_imei_on_sale_item_delete(sender, instance, **kwargs):
    """
    Restore serial/IMEI number (mark as not sold) when a SaleItem is deleted.
    """
    from .models import serial_imei_no
    
    # Check if we should process this sale
    should_process, reason = should_process_sale(instance.sale)
    if not should_process:
        logger.debug(f"[SERIAL_TRACK] Skipping serial restoration for SaleItem ID: {instance.id}, Reason: {reason}")
        return
    
    # Get serial/IMEI number that was linked to this sale item (OneToOne)
    # Note: We need to get it before the relationship is cleared
    linked_serial = instance.serial_imei_number
    
    if linked_serial:
        # Restore linked serial (mark as not sold)
        serial_imei_no.objects.filter(id=linked_serial.id).update(is_sold=False)
        logger.info(f"[SERIAL_TRACK] Restored serial/IMEI number (ID: {linked_serial.id}) - marked as not sold for deleted SaleItem ID: {instance.id}")


# -----------------------------------------------------------------------------
# 🟢 ONLINE ORDER SERIAL/IMEI NUMBER TRACKING
# -----------------------------------------------------------------------------
@receiver(post_delete, sender=OrderItem)
def restore_serial_imei_on_order_item_delete(sender, instance, **kwargs):
    """
    Restore serial/IMEI number (mark as not sold) when an OrderItem is deleted.
    """
    from .models import serial_imei_no
    
    # Get serial/IMEI number that was linked to this order item (OneToOne)
    # Note: We need to get it before the relationship is cleared
    linked_serial = instance.serial_imei_number
    
    if linked_serial:
        # Restore linked serial (mark as not sold)
        serial_imei_no.objects.filter(id=linked_serial.id).update(is_sold=False)
        logger.info(f"[ORDER_SERIAL_TRACK] ✅ Restored serial/IMEI number (ID: {linked_serial.id}, Value: {linked_serial.value}) - marked as not sold for deleted OrderItem ID: {instance.id}")


@receiver(pre_save, sender=OrderItem)
def restore_serial_on_order_item_cancelled(sender, instance, **kwargs):
    """
    Restore serial/IMEI number when OrderItem status changes to 'cancelled'.
    """
    # Skip if this is a new item
    if instance.pk is None:
        return
    
    from .models import serial_imei_no
    
    try:
        old_instance = OrderItem.objects.get(pk=instance.pk)
        old_status = old_instance.status
        new_status = instance.status
        
        # If status changed to 'cancelled', restore the serial
        if old_status != 'cancelled' and new_status == 'cancelled':
            linked_serial = instance.serial_imei_number
            if linked_serial:
                serial_imei_no.objects.filter(id=linked_serial.id).update(is_sold=False)
                logger.info(f"[ORDER_SERIAL_TRACK] ✅ Restored serial/IMEI number (ID: {linked_serial.id}, Value: {linked_serial.value}) - marked as not sold for cancelled OrderItem ID: {instance.id}")
    except OrderItem.DoesNotExist:
        pass


# -----------------------------------------------------------------------------
# 🟠 ORDER
# -----------------------------------------------------------------------------
@receiver(post_save, sender=OrderItem)
def reduce_stock_on_order_create(sender, instance, created, **kwargs):
    """Only reduce stock when order is accepted. Ledger/stock are done in on_order_accepted on accept."""
    if not created:
        return
    order = getattr(instance, "order", None)
    if order is None and hasattr(instance, "order_id") and instance.order_id:
        try:
            order = instance.order
        except Exception:
            order = None
    if order is None or getattr(order, "status", None) != "accepted":
        return
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
    # When OrderItem status transitions to return_completed (or legacy returned/replaced_completed),
    # add stock back for RETURNS only.
    if created:
        return
    try:
        new_status = instance.status
    except Exception:
        return
    if new_status in ('return_completed', 'returned/replaced_completed'):
        try:
            from customer.models import ReturnExchange
            req = ReturnExchange.objects.filter(order_item=instance).order_by('-created_at').first()
        except Exception:
            req = None
        if req and req.type == 'return':
            product.objects.filter(id=instance.product.id).update(
                stock_cached=F('stock_cached') + instance.quantity
            )
            log_stock_transaction(instance.product, "return", instance.quantity, ref_id=instance.pk)


@receiver(pre_save, sender=OrderItem)
def restore_stock_on_cancelled(sender, instance, **kwargs):
    """
    Restore stock when OrderItem status changes to 'cancelled'.
    Uses pre_save to check old status and new status, and only restores if transitioning TO cancelled.
    """
    if instance.pk is None:
        return
    
    try:
        old_instance = OrderItem.objects.get(pk=instance.pk)
        old_status = old_instance.status
        new_status = instance.status
    except OrderItem.DoesNotExist:
        return
    
    # Only restore stock when transitioning TO 'cancelled' and we had reduced (order was accepted: ledger exists)
    if old_status != 'cancelled' and new_status == 'cancelled':
        if not OnlineOrderLedger.objects.filter(order_item=instance).exists():
            return  # Order was never accepted; we never reduced stock
        product.objects.filter(id=instance.product.id).update(
            stock_cached=F('stock_cached') + instance.quantity
        )
        log_stock_transaction(instance.product, "cancel", instance.quantity, ref_id=instance.pk)


# -----------------------------------------------------------------------------
# Online Order Ledger entries per vendor for online orders
# -----------------------------------------------------------------------------
@receiver(post_save, sender=OrderItem)
def create_online_order_ledger_on_create(sender, instance, created, **kwargs):
    """
    Create a ledger entry when an order item is created (treated as online order).
    
    CONDITIONS FOR CREATION:
    1. OrderItem must be newly created (created=True)
    2. OrderItem must have a product with a user (vendor)
    3. OrderItem must have an order
    4. OrderItem must have quantity > 0
    5. OrderItem must have a valid price
    
    NOTE: This signal will NOT fire if OrderItems are created via bulk_create().
    Ledger (and stock, serial) are created in on_order_accepted() when the vendor accepts.
    """
    logger.info("=" * 80)
    logger.info("[ONLINE_ORDER_LEDGER] Signal triggered for OrderItem")
    logger.info(f"[ONLINE_ORDER_LEDGER] OrderItem ID: {getattr(instance, 'id', 'NEW')}")
    logger.info(f"[ONLINE_ORDER_LEDGER] Created: {created}")
    
    # Condition 1: Must be a new OrderItem (not an update)
    if not created:
        logger.info("[ONLINE_ORDER_LEDGER] SKIPPED: OrderItem is not newly created (this is an update)")
        logger.info("=" * 80)
        return
    
    logger.info("[ONLINE_ORDER_LEDGER] OrderItem is newly created - proceeding with ledger creation")
    
    # Condition 2: Must have a product
    product_obj = getattr(instance, 'product', None)
    if not product_obj:
        logger.warning("[ONLINE_ORDER_LEDGER] SKIPPED: OrderItem has no product")
        logger.info("=" * 80)
        return
    
    logger.info(f"[ONLINE_ORDER_LEDGER] Product ID: {product_obj.id}, Name: {getattr(product_obj, 'name', 'N/A')}")
    
    # Condition 3: Product must have a user (vendor)
    vendor_user = getattr(product_obj, 'user', None)
    if not vendor_user:
        logger.warning("[ONLINE_ORDER_LEDGER] SKIPPED: Product has no user (vendor)")
        logger.info("=" * 80)
        return
    
    logger.info(f"[ONLINE_ORDER_LEDGER] Vendor User: {vendor_user.username} (ID: {vendor_user.id})")
    
    # Condition 4: Must have an order
    order_obj = getattr(instance, 'order', None)
    if not order_obj:
        logger.warning("[ONLINE_ORDER_LEDGER] SKIPPED: OrderItem has no order")
        logger.info("=" * 80)
        return

    # Ledger/stock are created in on_order_accepted when vendor accepts; skip if order not yet accepted
    if getattr(order_obj, "status", None) != "accepted":
        logger.info("[ONLINE_ORDER_LEDGER] SKIPPED: Order not yet accepted (ledger created on accept)")
        logger.info("=" * 80)
        return
    
    order_id = getattr(order_obj, 'id', None)
    order_order_id = getattr(order_obj, 'order_id', None)
    logger.info(f"[ONLINE_ORDER_LEDGER] Order ID: {order_id}, Order Order ID: {order_order_id}")
    
    # Condition 5: Must have quantity > 0
    quantity = getattr(instance, 'quantity', 0) or 0
    if quantity <= 0:
        logger.warning(f"[ONLINE_ORDER_LEDGER] SKIPPED: OrderItem quantity is {quantity} (must be > 0)")
        logger.info("=" * 80)
        return
    
    logger.info(f"[ONLINE_ORDER_LEDGER] Quantity: {quantity}")
    
    # Condition 6: Must have a valid price
    price = getattr(instance, 'price', 0) or 0
    if price <= 0:
        logger.warning(f"[ONLINE_ORDER_LEDGER] SKIPPED: OrderItem price is {price} (must be > 0)")
        logger.info("=" * 80)
        return
    
    logger.info(f"[ONLINE_ORDER_LEDGER] Price: {price}")
    
    # Calculate amount
    amount = price * quantity
    logger.info(f"[ONLINE_ORDER_LEDGER] Calculated Amount: {amount}")
    
    # Check if ledger entry already exists (idempotency check)
    existing = OnlineOrderLedger.objects.filter(order_item=instance).exists()
    if existing:
        logger.warning("[ONLINE_ORDER_LEDGER] SKIPPED: OnlineOrderLedger entry already exists for this OrderItem")
        logger.info("=" * 80)
        return
    
    # All conditions met - create the ledger entry
    try:
        logger.info("[ONLINE_ORDER_LEDGER] All conditions met - creating OnlineOrderLedger entry...")
        ledger_entry = OnlineOrderLedger.objects.create(
            user=vendor_user,
                order_item=instance,
            product=product_obj,
            order_id=order_id,
            quantity=quantity,
            amount=amount,
                status='recorded',
                note='Online order recorded'
            )
        logger.info("=" * 80)
        logger.info("[ONLINE_ORDER_LEDGER] ✅ SUCCESS: OnlineOrderLedger entry created")
        logger.info(f"[ONLINE_ORDER_LEDGER] Ledger Entry ID: {ledger_entry.id}")
        logger.info(f"[ONLINE_ORDER_LEDGER] User: {vendor_user.username} (ID: {vendor_user.id})")
        logger.info(f"[ONLINE_ORDER_LEDGER] Order Item ID: {instance.id}")
        logger.info(f"[ONLINE_ORDER_LEDGER] Product ID: {product_obj.id}")
        logger.info(f"[ONLINE_ORDER_LEDGER] Order ID: {order_id}")
        logger.info(f"[ONLINE_ORDER_LEDGER] Quantity: {quantity}")
        logger.info(f"[ONLINE_ORDER_LEDGER] Amount: {amount}")
        logger.info(f"[ONLINE_ORDER_LEDGER] Status: recorded")
        logger.info("=" * 80)
    except Exception as e:
        logger.error("=" * 80)
        logger.error("[ONLINE_ORDER_LEDGER] ❌ ERROR: Failed to create OnlineOrderLedger entry")
        logger.error(f"[ONLINE_ORDER_LEDGER] Error Type: {type(e).__name__}")
        logger.error(f"[ONLINE_ORDER_LEDGER] Error Message: {str(e)}")
        import traceback
        logger.error(f"[ONLINE_ORDER_LEDGER] Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)



@receiver(post_save, sender=OrderItem)
def update_online_order_ledger_on_return(sender, instance, created, **kwargs):
    # Update OnlineOrderLedger only when RETURN is marked as completed. No ledger update for exchange (replace).
    if created:
        return
    try:
        new_status = instance.status
    except Exception:
        return
    if new_status not in ('return_completed', 'returned/replaced_completed'):
        return
    try:
        req = ReturnExchange.objects.filter(order_item=instance).order_by('-created_at').first()
    except Exception:
        req = None
    # Only update ledger for return type; do nothing for exchange (no ledger for replace)
    if not req or req.type != 'return':
        return
    try:
        entry = OnlineOrderLedger.objects.filter(order_item=instance).order_by('-created_at').first()
    except OnlineOrderLedger.DoesNotExist:
        entry = None
    if not entry:
        return
    entry.status = 'returned'
    entry.note = (entry.note or '') + ' | Marked returned'
    entry.save(update_fields=['status', 'note', 'updated_at'])
    # Stock for return only: avoid duplicate StockTransaction per request
    if not StockTransaction.objects.filter(
        product=instance.product,
        transaction_type='return',
        reference_id=req.pk
    ).exists():
        log_stock_transaction(instance.product, 'return', instance.quantity, ref_id=req.pk)

# -----------------------------------------------------------------------------
# COD / Cash Online Orders -> CashLedger credit when OrderItem is delivered
# -----------------------------------------------------------------------------
@receiver(post_save, sender=OrderItem)
def credit_vendor_cash_on_order_item_delivered(sender, instance, created, **kwargs):
    """
    When an OrderItem is marked as "delivered":
    - If order.is_auto_managed = True: credit vendor's online_order_bank (BankLedger)
    - If order.is_auto_managed = False and payment_mode is COD/cash: credit CashLedger

    Idempotent: will not create duplicate ledger entries for the same order item.
    """
    try:
        logger.info("=" * 80)
        logger.info("[ORDER_DELIVERY_CREDIT] Signal triggered for OrderItem")
        logger.info(f"[ORDER_DELIVERY_CREDIT] OrderItem ID: {getattr(instance, 'id', 'NEW')}")
        logger.info(f"[ORDER_DELIVERY_CREDIT] Created: {created}")
        logger.info(f"[ORDER_DELIVERY_CREDIT] Status: {getattr(instance, 'status', None)}")
        
        # Only process updates, not creation
        if created:
            logger.info("[ORDER_DELIVERY_CREDIT] SKIPPED: OrderItem is newly created (not an update)")
            logger.info("=" * 80)
            return
        
        # Only process when status is "delivered"
        if getattr(instance, "status", None) != "delivered":
            logger.info(f"[ORDER_DELIVERY_CREDIT] SKIPPED: Status is not 'delivered' (status: {getattr(instance, 'status', None)})")
            logger.info("=" * 80)
            return

        # Get order
        order = getattr(instance, "order", None)
        if not order:
            logger.warning("[ORDER_DELIVERY_CREDIT] SKIPPED: OrderItem has no order")
            logger.info("=" * 80)
            return
        
        logger.info(f"[ORDER_DELIVERY_CREDIT] Order ID: {order.id}, Order Order ID: {getattr(order, 'order_id', None)}")
        logger.info(f"[ORDER_DELIVERY_CREDIT] Order is_auto_managed: {getattr(order, 'is_auto_managed', False)}")
        logger.info(f"[ORDER_DELIVERY_CREDIT] Order payment_mode: {getattr(order, 'payment_mode', None)}")

        # Get vendor from product
        vendor_user = getattr(instance.product, "user", None)
        if not vendor_user:
            logger.warning("[ORDER_DELIVERY_CREDIT] SKIPPED: Product has no user (vendor)")
            logger.info("=" * 80)
            return
        
        logger.info(f"[ORDER_DELIVERY_CREDIT] Vendor User: {vendor_user.username} (ID: {vendor_user.id})")

        # Calculate amount for this item
        from decimal import Decimal
        q2 = Decimal("0.01")
        item_price = Decimal(getattr(instance, "price", 0) or 0)
        item_quantity = Decimal(getattr(instance, "quantity", 0) or 0)
        amount = (item_price * item_quantity).quantize(q2)
        
        logger.info(f"[ORDER_DELIVERY_CREDIT] Amount: {amount} (Price: {item_price}, Quantity: {item_quantity})")
        
        if amount == 0:
            logger.warning("[ORDER_DELIVERY_CREDIT] SKIPPED: Amount is 0")
            logger.info("=" * 80)
            return

        # Check if order is auto-managed
        is_auto_managed = getattr(order, "is_auto_managed", False)
        
        if is_auto_managed:
            logger.info("[ORDER_DELIVERY_CREDIT] Order is auto-managed - will credit online_order_bank")
            # For auto-managed orders, credit the online_order_bank
            online_bank = vendor_bank.objects.filter(
                user=vendor_user,
                online_order_bank=True,
                is_active=True
            ).first()
            
            if online_bank:
                logger.info(f"[ORDER_DELIVERY_CREDIT] Found online_order_bank: {online_bank.name} (ID: {online_bank.id})")
                logger.info(f"[ORDER_DELIVERY_CREDIT] Bank Account Number: {online_bank.account_number}")
                
                # Avoid duplicates - check if we already created a bank ledger entry for this order item
                existing = BankLedger.objects.filter(
                    bank=online_bank,
                    transaction_type="sale",
                    reference_id=instance.id,
                    description__icontains="Online Order Auto",
                ).exists()
                
                if existing:
                    logger.warning(f"[ORDER_DELIVERY_CREDIT] SKIPPED: BankLedger entry already exists for OrderItem {instance.id}")
                    logger.info("=" * 80)
                    return
                
                logger.info(f"[ORDER_DELIVERY_CREDIT] Creating BankLedger entry...")
                # Create bank ledger entry for this delivered item
                create_ledger(
                    online_bank,
                    BankLedger,
                    transaction_type="sale",
                    reference_id=instance.id,
                    amount=amount,
                    description=f"Online Order Auto-Managed (Order #{getattr(order, 'order_id', order.id)}, Item #{instance.id})",
                )
                logger.info(f"[ORDER_DELIVERY_CREDIT] ✅ SUCCESS: BankLedger entry created for OrderItem {instance.id}")
                logger.info(f"[ORDER_DELIVERY_CREDIT] Amount credited: {amount}")
            else:
                logger.warning(f"[ORDER_DELIVERY_CREDIT] ⚠️ WARNING: No online_order_bank found for vendor {vendor_user.username}")
                logger.warning(f"[ORDER_DELIVERY_CREDIT] Banks for this vendor:")
                all_banks = vendor_bank.objects.filter(user=vendor_user, is_active=True)
                for b in all_banks:
                    logger.warning(f"[ORDER_DELIVERY_CREDIT]   - {b.name} (ID: {b.id}), online_order_bank: {b.online_order_bank}")
        else:
            logger.info("[ORDER_DELIVERY_CREDIT] Order is NOT auto-managed - checking for COD/cash payment")
            # For non-auto-managed orders with COD/cash, credit CashLedger (existing logic)
            payment_mode = str(getattr(order, "payment_mode", "") or "").strip().lower()
            logger.info(f"[ORDER_DELIVERY_CREDIT] Payment mode: {payment_mode}")
            
            if payment_mode not in ("cod", "cash"):
                logger.info(f"[ORDER_DELIVERY_CREDIT] SKIPPED: Payment mode is not COD/cash (payment_mode: {payment_mode})")
                logger.info("=" * 80)
                return

            # Avoid duplicates - check if we already created a cash ledger entry for this order item
            existing_cash = CashLedger.objects.filter(
                user=vendor_user,
                transaction_type="sale",
                reference_id=instance.id,
                description__icontains="Online Order COD",
            ).exists()
            
            if existing_cash:
                logger.warning(f"[ORDER_DELIVERY_CREDIT] SKIPPED: CashLedger entry already exists for OrderItem {instance.id}")
                logger.info("=" * 80)
                return

            logger.info(f"[ORDER_DELIVERY_CREDIT] Creating CashLedger entry...")
            # Create cash ledger entry for this delivered item
            create_ledger(
                None,
                CashLedger,
                transaction_type="sale",
                reference_id=instance.id,
                amount=amount,
                description=f"Online Order COD Received (Order #{getattr(order, 'order_id', order.id)}, Item #{instance.id})",
                user=vendor_user,
            )
            logger.info(f"[ORDER_DELIVERY_CREDIT] ✅ SUCCESS: CashLedger entry created for OrderItem {instance.id}")
            logger.info(f"[ORDER_DELIVERY_CREDIT] Amount credited: {amount}")
        
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"[ORDER_DELIVERY_CREDIT] ❌ ERROR: Exception occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("=" * 80)
        # Never break save flow on logging/ledger issues
        return

# --- Ensure stock logs on create have proper reference ids ---
@receiver(post_delete, sender=OrderItem)
def restore_stock_on_order_delete(sender, instance, **kwargs):
    # Only restore if we had reduced (order was accepted). Ledger may be cascade-deleted; check order.
    try:
        order = Order.objects.filter(id=instance.order_id).first()
        if not order or getattr(order, "status", None) != "accepted":
            return
    except Exception:
        return
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


def send_reminder_push_notification_to_user(user):
    """
    Send a single push notification to user when reminders are created.
    This should be called after all reminders for a user are created in a batch.
    Returns True if notification was sent successfully, False otherwise.
    """
    from django.utils import timezone
    import logging
    
    logger = logging.getLogger(__name__)
    current_time = timezone.now()
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        from firebase_admin import messaging
        from users.models import DeviceToken
        
        logger.info(f"[REMINDER NOTIFICATION] [{timestamp}] Starting notification process for user {user.id} ({user.username or user.mobile})")
        
        # Get user's device token (OneToOneField relationship)
        try:
            device_token_obj = DeviceToken.objects.get(user=user)
            token = device_token_obj.token
            logger.info(f"[REMINDER NOTIFICATION] [{timestamp}] Device token found for user {user.id}")
        except DeviceToken.DoesNotExist:
            logger.warning(f"[REMINDER NOTIFICATION] [{timestamp}] ❌ No device token found for user {user.id} ({user.username or user.mobile}), skipping push notification")
            return False
        
        if not token or not token.strip():
            logger.warning(f"[REMINDER NOTIFICATION] [{timestamp}] ❌ Empty or invalid device token for user {user.id} ({user.username or user.mobile}), skipping push notification")
            return False
        
        # Prepare notification message
        title = "New Reminder"
        body = "New reminder for you, please visit app"
        
        logger.info(f"[REMINDER NOTIFICATION] [{timestamp}] Preparing FCM message for user {user.id}")
        
        # Create and send FCM message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={
                "type": "reminder",
                "user_id": str(user.id),
            },
            token=token.strip(),
        )
        
        logger.info(f"[REMINDER NOTIFICATION] [{timestamp}] Sending FCM message to user {user.id}...")
        response = messaging.send(message)
        
        success_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"[REMINDER NOTIFICATION] [{success_time}] ✅ SUCCESS: Push notification sent to user {user.id} ({user.username or user.mobile})")
        logger.info(f"[REMINDER NOTIFICATION] [{success_time}] FCM Response: {response}")
        return True
        
    except Exception as e:
        error_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        import traceback
        logger.error(f"[REMINDER NOTIFICATION] [{error_time}] ❌ ERROR: Failed to send push notification to user {user.id} ({user.username or user.mobile})")
        logger.error(f"[REMINDER NOTIFICATION] [{error_time}] Error: {str(e)}")
        logger.error(f"[REMINDER NOTIFICATION] [{error_time}] Traceback: {traceback.format_exc()}")
        return False


