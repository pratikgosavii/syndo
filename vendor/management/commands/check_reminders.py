"""
Management command to check and create reminders based on ReminderSetting for each vendor/user.
Run: python manage.py check_reminders
"""
from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone
from datetime import timedelta, date, datetime, time as dt_time
from decimal import Decimal
from vendor.models import ReminderSetting, Reminder, Purchase, Sale, product
from users.models import User


class Command(BaseCommand):
    help = 'Check and create reminders based on ReminderSetting for each vendor/user'

    def handle(self, *args, **options):
        self.stdout.write('Starting reminder checks...')
        
        # Get all users with ReminderSetting
        users_with_settings = User.objects.filter(remindersetting__isnull=False).distinct()
        
        user_count = users_with_settings.count()
        self.stdout.write(f'Found {user_count} user(s) with reminder settings configured')
        
        if not users_with_settings.exists():
            self.stdout.write(self.style.WARNING('No users with reminder settings found.'))
            return
        
        total_reminders = 0
        users_processed = 0
        notifications_sent = 0
        notifications_failed = 0
        notifications_skipped = 0
        
        for user in users_with_settings:
            try:
                settings = ReminderSetting.objects.get(user=user)
                user_display = user.username or user.mobile or f"User {user.id}"
                self.stdout.write(f'\n--- Processing user: {user_display} (ID: {user.id}) ---')
                self.stdout.write(f'  Credit Bill Reminder: {settings.credit_bill_reminder}')
                self.stdout.write(f'  Pending Invoice Reminder: {settings.pending_invoice_reminder}')
                self.stdout.write(f'  Low Stock Reminder: {settings.low_stock_reminder}')
                self.stdout.write(f'  Expiry Stock Reminder: {settings.expiry_stock_reminder}')
                
                reminders_created = self.check_user_reminders(user, settings)
                total_reminders += reminders_created
                users_processed += 1
                self.stdout.write(f'  → Created {reminders_created} reminder(s) for this user')
                
                # Send push notification if reminders were created
                if reminders_created > 0:
                    current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.stdout.write(f'  [NOTIFICATION] Attempting to send push notification at {current_time}')
                    try:
                        from vendor.signals import send_reminder_push_notification_to_user
                        result = send_reminder_push_notification_to_user(user)
                        user_display = user.username or user.mobile or f"User {user.id}"
                        if result:
                            self.stdout.write(self.style.SUCCESS(f'  [NOTIFICATION] ✅ SUCCESS: Push notification sent to user {user_display} (ID: {user.id}) at {current_time}'))
                            notifications_sent += 1
                        else:
                            self.stdout.write(self.style.WARNING(f'  [NOTIFICATION] ⚠️  SKIPPED: No device token found for user {user_display} (ID: {user.id}) at {current_time}'))
                            notifications_skipped += 1
                    except Exception as e:
                        error_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                        user_display = user.username or user.mobile or f"User {user.id}"
                        self.stdout.write(self.style.ERROR(f'  [NOTIFICATION] ❌ FAILED: Error sending push notification to user {user_display} (ID: {user.id}) at {error_time}'))
                        self.stdout.write(self.style.ERROR(f'  [NOTIFICATION] Error details: {str(e)}'))
                        notifications_failed += 1
                else:
                    self.stdout.write(f'  [NOTIFICATION] ⏭️  SKIPPED: No reminders created, notification not sent')
                    notifications_skipped += 1
            except ReminderSetting.DoesNotExist:
                user_display = user.username or user.mobile or f"User {user.id}"
                self.stdout.write(self.style.WARNING(f'  ReminderSetting not found for user {user_display} (ID: {user.id}), skipping'))
                continue
        
        end_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        self.stdout.write(f'\n--- Summary ---')
        self.stdout.write(f'Completed at: {end_time}')
        self.stdout.write(f'Users processed: {users_processed}/{user_count}')
        self.stdout.write(
            self.style.SUCCESS(f'Total reminders created: {total_reminders}')
        )
        self.stdout.write(f'\n--- Notification Summary ---')
        self.stdout.write(self.style.SUCCESS(f'✅ Notifications sent successfully: {notifications_sent}'))
        self.stdout.write(self.style.WARNING(f'⚠️  Notifications skipped (no token/no reminders): {notifications_skipped}'))
        self.stdout.write(self.style.ERROR(f'❌ Notifications failed: {notifications_failed}'))
        self.stdout.write(f'Total notification attempts: {notifications_sent + notifications_skipped + notifications_failed}')

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
        
        self.stdout.write(f"[CREDIT BILL REMINDER] Checking credit bill reminders for user {user.username} (ID: {user.id})")
        self.stdout.write(f"[CREDIT BILL REMINDER] Today: {today}")
        self.stdout.write(f"[CREDIT BILL REMINDER] Threshold: {threshold_date} (within {days_threshold} days)")
        
        # Get credit purchases with balance_amount > 0
        credit_purchases = Purchase.objects.filter(
            user=user,
            payment_method='credit',
            balance_amount__gt=0
        ).select_related('vendor')
        
        total_credit_purchases = credit_purchases.count()
        self.stdout.write(f"[CREDIT BILL REMINDER] Total credit purchases with balance > 0: {total_credit_purchases}")
        
        skipped_no_due_date = 0
        skipped_not_in_threshold = 0
        skipped_existing_reminder = 0
        
        for purchase in credit_purchases:
            # Skip if due_date is not set
            if not purchase.due_date:
                skipped_no_due_date += 1
                self.stdout.write(f"[CREDIT BILL REMINDER] Skipping {purchase.purchase_code} - no due_date set")
                continue
            
            # Check if due within threshold or overdue
            if purchase.due_date <= threshold_date:
                # Check if reminder already exists for this purchase (unread)
                existing = Reminder.objects.filter(
                    user=user,
                    reminder_type='credit_bill',
                    purchase=purchase,
                    is_read=False
                ).exists()
                
                if existing:
                    skipped_existing_reminder += 1
                    self.stdout.write(f"[CREDIT BILL REMINDER] Skipping {purchase.purchase_code} (due: {purchase.due_date}) - reminder already exists")
                else:
                    vendor_name = purchase.vendor.name if purchase.vendor else 'Unknown Vendor'
                    days_overdue = (today - purchase.due_date).days if purchase.due_date < today else 0
                    
                    title = f"Credit Bill Due: {purchase.purchase_code}"
                    if days_overdue > 0:
                        message = f"Credit bill from {vendor_name} is {days_overdue} day(s) overdue. Amount: ₹{purchase.balance_amount}"
                    else:
                        days_until_due = (purchase.due_date - today).days
                        message = f"Credit bill from {vendor_name} is due in {days_until_due} day(s). Amount: ₹{purchase.balance_amount}"
                    
                    current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.stdout.write(f"[CREDIT BILL REMINDER] [{current_time}] Creating reminder for {purchase.purchase_code} (due: {purchase.due_date}, amount: ₹{purchase.balance_amount})")
                    
                    reminder = Reminder.objects.create(
                        user=user,
                        reminder_type='credit_bill',
                        title=title,
                        message=message,
                        purchase=purchase,
                        due_date=purchase.due_date,
                        amount=purchase.balance_amount
                    )
                    created_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.stdout.write(f"[CREDIT BILL REMINDER] [{created_time}] ✅ Reminder ID {reminder.id} created successfully")
                    reminders_created += 1
            else:
                skipped_not_in_threshold += 1
                days_until_due = (purchase.due_date - today).days
                self.stdout.write(f"[CREDIT BILL REMINDER] Skipping {purchase.purchase_code} (due: {purchase.due_date}, {days_until_due} days away) - not within threshold")
        
        if reminders_created == 0 and total_credit_purchases > 0:
            self.stdout.write(f"[CREDIT BILL REMINDER] Summary: {skipped_no_due_date} skipped (no due_date), {skipped_not_in_threshold} skipped (not in threshold), {skipped_existing_reminder} skipped (reminder exists)")
        
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
                    
                    current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.stdout.write(f"[PENDING INVOICE REMINDER] [{current_time}] Creating reminder for sale {sale.invoice_number or sale.id}")
                    
                    reminder = Reminder.objects.create(
                        user=user,
                        reminder_type='pending_invoice',
                        title=title,
                        message=message,
                        sale=sale,
                        due_date=sale.due_date,
                        amount=sale.balance_amount
                    )
                    created_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.stdout.write(f"[PENDING INVOICE REMINDER] [{created_time}] ✅ Reminder ID {reminder.id} created successfully")
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
                
                current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                self.stdout.write(f"[LOW STOCK REMINDER] [{current_time}] Creating reminder for product {prod.name} (ID: {prod.id})")
                
                reminder = Reminder.objects.create(
                    user=user,
                    reminder_type='low_stock',
                    title=title,
                    message=message,
                    product=prod,
                    stock_quantity=prod.stock
                )
                created_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                self.stdout.write(f"[LOW STOCK REMINDER] [{created_time}] ✅ Reminder ID {reminder.id} created successfully")
                reminders_created += 1
        
        return reminders_created

    def check_expiry_stock(self, user, settings, today):
        """Check for products expiring today (on the exact expiry date)."""
        reminders_created = 0
        
        # Validate user
        if not user:
            self.stdout.write(self.style.ERROR("[EXPIRY REMINDER] User is None, skipping expiry check"))
            return 0
        
        self.stdout.write(f"[EXPIRY REMINDER] Checking expiry reminders for user {user.username} (ID: {user.id})")
        self.stdout.write(f"[EXPIRY REMINDER] Today: {today}")
        self.stdout.write(f"[EXPIRY REMINDER] Looking for products expiring TODAY (exact date match)")
        
        # Debug: Count all products with expiry dates for this user
        all_with_expiry = product.objects.filter(user=user, expiry_date__isnull=False).count()
        self.stdout.write(f"[EXPIRY REMINDER] Total products with expiry_date: {all_with_expiry}")
        
        # Get products that expire TODAY (exact date match)
        expiring_products = product.objects.filter(
            user=user,
            expiry_date__isnull=False,
            expiry_date=today  # Exact date match - expires today
        )
        
        self.stdout.write(f"[EXPIRY REMINDER] Products expiring today: {expiring_products.count()}")
        
        # Debug: Show products that will get reminders
        if expiring_products.exists():
            for p in expiring_products:
                self.stdout.write(f"  - {p.name} (ID: {p.id}): expires today ({p.expiry_date})")
        
        for prod in expiring_products:
            # Check if reminder already exists for this product today (created today, regardless of read status)
            today_start = timezone.make_aware(datetime.combine(today, dt_time.min))
            today_end = timezone.make_aware(datetime.combine(today, dt_time.max))
            
            existing_today = Reminder.objects.filter(
                user=user,
                reminder_type='expiry_stock',
                product=prod,
                expiry_date=prod.expiry_date,
                created_at__gte=today_start,
                created_at__lte=today_end
            ).exists()
            
            # Also check ALL existing reminders for debugging
            all_existing = Reminder.objects.filter(
                user=user,
                reminder_type='expiry_stock',
                product=prod,
                expiry_date=prod.expiry_date
            )
            if all_existing.exists():
                self.stdout.write(f"[EXPIRY REMINDER] Found {all_existing.count()} existing reminder(s) for {prod.name}:")
                for rem in all_existing:
                    self.stdout.write(f"  - Reminder ID: {rem.id}, created: {rem.created_at}, is_read: {rem.is_read}, title: {rem.title}")
            
            if existing_today:
                self.stdout.write(f"[EXPIRY REMINDER] Skipping {prod.name} (ID: {prod.id}) - reminder already created today")
            else:
                title = f"Expiry Alert: {prod.name}"
                message = f"Product '{prod.name}' expires today on {prod.expiry_date}"
                
                current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                self.stdout.write(f"[EXPIRY REMINDER] [{current_time}] Creating reminder for {prod.name} (ID: {prod.id}, expires: {prod.expiry_date})")
                self.stdout.write(f"[EXPIRY REMINDER] [{current_time}] User: {user} (ID: {user.id if user else 'None'})")
                
                try:
                    reminder = Reminder.objects.create(
                        user=user,
                        reminder_type='expiry_stock',
                        title=title,
                        message=message,
                        product=prod,
                        expiry_date=prod.expiry_date,
                        stock_quantity=prod.stock
                    )
                    created_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.stdout.write(f"[EXPIRY REMINDER] [{created_time}] ✅ Successfully created reminder ID: {reminder.id}")
                    reminders_created += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"[EXPIRY REMINDER] ✗ Failed to create reminder: {str(e)}"))
                    import traceback
                    self.stdout.write(self.style.ERROR(f"[EXPIRY REMINDER] Traceback: {traceback.format_exc()}"))
        
        if reminders_created == 0 and expiring_products.count() > 0:
            self.stdout.write(self.style.WARNING(f"[EXPIRY REMINDER] Found {expiring_products.count()} products expiring today but created 0 reminders (all may have existing reminders)"))
        
        return reminders_created

