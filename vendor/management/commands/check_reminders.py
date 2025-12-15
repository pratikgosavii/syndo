"""
Management command to check and create reminders based on ReminderSetting for each vendor/user.
Run: python manage.py check_reminders
"""
from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from vendor.models import ReminderSetting, Reminder, Purchase, Sale, product
from users.models import User


class Command(BaseCommand):
    help = 'Check and create reminders based on ReminderSetting for each vendor/user'

    def handle(self, *args, **options):
        self.stdout.write('Starting reminder checks...')
        
        # Get all users with ReminderSetting
        users_with_settings = User.objects.filter(remindersetting__isnull=False).distinct()
        
        if not users_with_settings.exists():
            self.stdout.write(self.style.WARNING('No users with reminder settings found.'))
            return
        
        total_reminders = 0
        
        for user in users_with_settings:
            try:
                settings = ReminderSetting.objects.get(user=user)
                reminders_created = self.check_user_reminders(user, settings)
                total_reminders += reminders_created
            except ReminderSetting.DoesNotExist:
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed reminders. Total reminders created: {total_reminders}')
        )

    def check_user_reminders(self, user, settings):
        """Check and create reminders for a specific user based on their settings."""
        reminders_created = 0
        today = timezone.now().date()
        
        # 1. Credit Bill Reminders (Purchase module)
        if settings.credit_bill_reminder:
            reminders_created += self.check_credit_bills(user, settings, today)
        
        # 2. Pending Invoice Reminders (POS/Sale module)
        if settings.pending_invoice_reminder:
            reminders_created += self.check_pending_invoices(user, settings, today)
        
        # 3. Low Stock Reminders (Product module)
        if settings.low_stock_reminder:
            reminders_created += self.check_low_stock(user, today)
        
        # 4. Expiry Stock Reminders (Product module)
        if settings.expiry_stock_reminder:
            reminders_created += self.check_expiry_stock(user, settings, today)
        
        return reminders_created

    def check_credit_bills(self, user, settings, today):
        """Check for overdue or due credit purchases (bills)."""
        reminders_created = 0
        days_threshold = settings.credit_bill_days
        
        # Calculate the date threshold - bills due within X days or overdue
        threshold_date = today + timedelta(days=days_threshold)
        
        # Get credit purchases with balance_amount > 0
        credit_purchases = Purchase.objects.filter(
            user=user,
            payment_method='credit',
            balance_amount__gt=0
        ).select_related('vendor')
        
        for purchase in credit_purchases:
            # Skip if due_date is not set
            if not purchase.due_date:
                continue
            
            # Check if due within threshold or overdue
            if purchase.due_date <= threshold_date:
                # Check if reminder already exists for this purchase
                existing = Reminder.objects.filter(
                    user=user,
                    reminder_type='credit_bill',
                    purchase=purchase,
                    is_read=False
                ).exists()
                
                if not existing:
                    vendor_name = purchase.vendor.name if purchase.vendor else 'Unknown Vendor'
                    days_overdue = (today - purchase.due_date).days if purchase.due_date < today else 0
                    
                    title = f"Credit Bill Due: {purchase.purchase_code}"
                    if days_overdue > 0:
                        message = f"Credit bill from {vendor_name} is {days_overdue} day(s) overdue. Amount: ₹{purchase.balance_amount}"
                    else:
                        days_until_due = (purchase.due_date - today).days
                        message = f"Credit bill from {vendor_name} is due in {days_until_due} day(s). Amount: ₹{purchase.balance_amount}"
                    
                    Reminder.objects.create(
                        user=user,
                        reminder_type='credit_bill',
                        title=title,
                        message=message,
                        purchase=purchase,
                        due_date=purchase.due_date,
                        amount=purchase.balance_amount
                    )
                    reminders_created += 1
        
        return reminders_created

    def check_pending_invoices(self, user, settings, today):
        """Check for overdue or due credit sales (pending invoices)."""
        reminders_created = 0
        days_threshold = settings.pending_invoice_days
        
        # Calculate the date threshold - invoices due within X days or overdue
        threshold_date = today + timedelta(days=days_threshold)
        
        # Get credit sales with balance_amount > 0
        credit_sales = Sale.objects.filter(
            user=user,
            payment_method='credit',
            balance_amount__gt=0
        ).select_related('customer')
        
        for sale in credit_sales:
            # Skip if due_date is not set
            if not sale.due_date:
                continue
            
            # Check if due within threshold or overdue
            if sale.due_date <= threshold_date:
                # Check if reminder already exists for this sale
                existing = Reminder.objects.filter(
                    user=user,
                    reminder_type='pending_invoice',
                    sale=sale,
                    is_read=False
                ).exists()
                
                if not existing:
                    customer_name = sale.customer.name if sale.customer else 'Unknown Customer'
                    days_overdue = (today - sale.due_date).days if sale.due_date < today else 0
                    
                    title = f"Pending Invoice: {sale.invoice_number or f'Sale #{sale.id}'}"
                    if days_overdue > 0:
                        message = f"Invoice from {customer_name} is {days_overdue} day(s) overdue. Amount: ₹{sale.balance_amount}"
                    else:
                        days_until_due = (sale.due_date - today).days
                        message = f"Invoice from {customer_name} is due in {days_until_due} day(s). Amount: ₹{sale.balance_amount}"
                    
                    Reminder.objects.create(
                        user=user,
                        reminder_type='pending_invoice',
                        title=title,
                        message=message,
                        sale=sale,
                        due_date=sale.due_date,
                        amount=sale.balance_amount
                    )
                    reminders_created += 1
        
        return reminders_created

    def check_low_stock(self, user, today):
        """Check for products with low stock."""
        reminders_created = 0
        
        # Get products owned by user with low stock alert enabled
        low_stock_products = product.objects.filter(
            user=user,
            low_stock_alert=True,
            track_stock=True,
            stock__isnull=False,
            low_stock_quantity__isnull=False
        ).filter(
            stock__lte=F('low_stock_quantity')
        )
        
        for prod in low_stock_products:
            # Check if reminder already exists for this product (unread)
            existing = Reminder.objects.filter(
                user=user,
                reminder_type='low_stock',
                product=prod,
                is_read=False
            ).exists()
            
            if not existing:
                title = f"Low Stock Alert: {prod.name}"
                message = f"Product '{prod.name}' has low stock. Current: {prod.stock}, Threshold: {prod.low_stock_quantity}"
                
                Reminder.objects.create(
                    user=user,
                    reminder_type='low_stock',
                    title=title,
                    message=message,
                    product=prod,
                    stock_quantity=prod.stock
                )
                reminders_created += 1
        
        return reminders_created

    def check_expiry_stock(self, user, settings, today):
        """Check for products expiring soon."""
        reminders_created = 0
        
        # Calculate expiry threshold - products expiring within X days
        days_threshold = getattr(settings, 'expiry_stock_days', 30)
        expiry_threshold = today + timedelta(days=days_threshold)
        
        # Get products with expiry dates
        expiring_products = product.objects.filter(
            user=user,
            expiry_date__isnull=False,
            expiry_date__gte=today,
            expiry_date__lte=expiry_threshold
        )
        
        for prod in expiring_products:
            # Check if reminder already exists for this product (unread)
            existing = Reminder.objects.filter(
                user=user,
                reminder_type='expiry_stock',
                product=prod,
                expiry_date=prod.expiry_date,
                is_read=False
            ).exists()
            
            if not existing:
                days_until_expiry = (prod.expiry_date - today).days
                title = f"Expiry Alert: {prod.name}"
                message = f"Product '{prod.name}' expires in {days_until_expiry} day(s) on {prod.expiry_date}"
                
                Reminder.objects.create(
                    user=user,
                    reminder_type='expiry_stock',
                    title=title,
                    message=message,
                    product=prod,
                    expiry_date=prod.expiry_date,
                    stock_quantity=prod.stock
                )
                reminders_created += 1
        
        return reminders_created

