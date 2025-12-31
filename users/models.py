from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        """Create and return a regular user with a mobile number and password."""
        if not mobile:
            raise ValueError("The Mobile field must be set")
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(mobile, password, **extra_fields)


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)

    is_customer = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_subuser = models.BooleanField(default=False)

    pincode = models.IntegerField(null=True, blank=True)
    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True)

    username = None
    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    
    def delete(self, using=None, keep_parents=False):
        """
        Override delete method to ensure all ledger entries and related transactions
        are deleted before Django's CASCADE deletion tries to process them.
        This prevents foreign key constraint errors.
        """
        from django.db import transaction
        from vendor.models import (
            CashLedger, CashBalance, BankLedger, CustomerLedger, VendorLedger,
            vendor_bank, vendor_customers, vendor_vendors,
            Purchase, Expense, Sale, Payment, BankTransfer, CashTransfer
        )
        
        with transaction.atomic():
            # Clear ManyToMany relationships first (groups, user_permissions)
            # Django will handle these, but clearing explicitly can help avoid issues
            self.groups.clear()
            self.user_permissions.clear()
            
            # Get all related object IDs BEFORE any deletions
            bank_ids = list(vendor_bank.objects.filter(user=self).values_list('id', flat=True))
            customer_ids = list(vendor_customers.objects.filter(user=self).values_list('id', flat=True))
            vendor_ids = list(vendor_vendors.objects.filter(user=self).values_list('id', flat=True))
            
            # IMPORTANT: Delete in the correct order to avoid constraint errors
            # 1. Get product IDs first (needed for deleting items that reference products)
            from vendor.models import product
            product_ids = list(product.objects.filter(user=self).values_list('id', flat=True))
            
            # 2. Delete ledgers that reference transactions (must be deleted before transactions)
            try:
                from vendor.models import ExpenseLedger, OnlineOrderLedger
                # ExpenseLedger references Expense, so delete it before Expense
                ExpenseLedger.objects.filter(user=self).delete()
                # OnlineOrderLedger references OrderItem, so delete it early (both vendor and customer cases)
                OnlineOrderLedger.objects.filter(user=self).delete()
                # Also delete OnlineOrderLedgers for orders placed by this user (if user is a customer)
                try:
                    from customer.models import OrderItem
                    OnlineOrderLedger.objects.filter(order_item__order__user=self).delete()
                except ImportError:
                    pass
            except ImportError:
                pass
            
            # 3. Delete child items and related objects first (they have FK to transactions and products)
            from vendor.models import PurchaseItem, SaleItem, Reminder, pos_wholesale, StockTransaction
            # Delete items in user's purchases/sales
            PurchaseItem.objects.filter(purchase__user=self).delete()
            SaleItem.objects.filter(user=self).delete()
            SaleItem.objects.filter(sale__user=self).delete()
            # Also delete items that reference products owned by this user (in case other users created purchases/sales with these products)
            if product_ids:
                PurchaseItem.objects.filter(product__in=product_ids).delete()
                SaleItem.objects.filter(product__in=product_ids).delete()
                # StockTransaction references product, so delete before products
                StockTransaction.objects.filter(product__in=product_ids).delete()
            
            Reminder.objects.filter(user=self).delete()
            Reminder.objects.filter(purchase__user=self).delete()
            Reminder.objects.filter(sale__user=self).delete()
            pos_wholesale.objects.filter(user=self).delete()
            pos_wholesale.objects.filter(sale__user=self).delete()
            
            # 4. Delete transactions that reference banks/customers/vendors
            # These will trigger their own delete signals which will clean up ledger entries
            if bank_ids:
                BankTransfer.objects.filter(from_bank_id__in=bank_ids).delete()
                BankTransfer.objects.filter(to_bank_id__in=bank_ids).delete()
                Purchase.objects.filter(advance_bank_id__in=bank_ids).delete()
                Expense.objects.filter(bank_id__in=bank_ids).delete()
                Sale.objects.filter(advance_bank_id__in=bank_ids).delete()
                Payment.objects.filter(bank_account_id__in=bank_ids).delete()
            
            if customer_ids:
                Sale.objects.filter(customer_id__in=customer_ids).delete()
                Payment.objects.filter(customer_id__in=customer_ids).delete()
            
            if vendor_ids:
                Purchase.objects.filter(vendor_id__in=vendor_ids).delete()
                Payment.objects.filter(vendor_id__in=vendor_ids).delete()
            
            # 5. Delete transactions that directly reference User
            Purchase.objects.filter(user=self).delete()
            Sale.objects.filter(user=self).delete()
            Expense.objects.filter(user=self).delete()
            Payment.objects.filter(user=self).delete()
            CashTransfer.objects.filter(user=self).delete()
            BankTransfer.objects.filter(user=self).delete()
            
            # 6. Delete product-related models (products are already identified above)
            try:
                from vendor.models import (
                    ProductSerial, PrintVariant, CustomizePrintVariant, 
                    product_addon, SpotlightProduct, serial_imei_no
                )
                
                # Delete product-related child models
                if product_ids:
                    ProductSerial.objects.filter(product__in=product_ids).delete()
                    serial_imei_no.objects.filter(product__in=product_ids).delete()
                    PrintVariant.objects.filter(product__in=product_ids).delete()
                    CustomizePrintVariant.objects.filter(product__in=product_ids).delete()
                    product_addon.objects.filter(product__in=product_ids).delete()
                    SpotlightProduct.objects.filter(product__in=product_ids).delete()
                    # Note: Offer.product is a CharField, not ForeignKey, so we filter by seller later
                
                # Delete products (this will cascade delete any remaining PurchaseItems/SaleItems)
                product.objects.filter(user=self).delete()
                SpotlightProduct.objects.filter(user=self).delete()
            except ImportError:
                pass
            
            # 7. Delete store and related models
            try:
                from vendor.models import vendor_store, StoreWorkingHour, StoreVisit
                store_ids = list(vendor_store.objects.filter(user=self).values_list('id', flat=True))
                
                # Delete store visits (references both store and visitor)
                if store_ids:
                    StoreVisit.objects.filter(store__in=store_ids).delete()
                StoreVisit.objects.filter(visitor=self).delete()
                
                # Delete working hours
                StoreWorkingHour.objects.filter(user=self).delete()
                
                # Delete stores (will cascade to related models)
                vendor_store.objects.filter(user=self).delete()
            except ImportError:
                pass
            
            # 8. Delete settings and profile models (OneToOne and FK relationships)
            try:
                from vendor.models import (
                    OnlineStoreSetting, ProductSettings, CompanyProfile, DeliveryDiscount,
                    DeliveryMode, TaxSettings, InvoiceSettings, BarcodeSettings,
                    SMSSetting, ReminderSetting, OrderNotificationMessage
                )
                OnlineStoreSetting.objects.filter(user=self).delete()
                ProductSettings.objects.filter(user=self).delete()
                CompanyProfile.objects.filter(user=self).delete()
                DeliveryDiscount.objects.filter(user=self).delete()
                DeliveryMode.objects.filter(user=self).delete()
                TaxSettings.objects.filter(user=self).delete()
                InvoiceSettings.objects.filter(user=self).delete()
                BarcodeSettings.objects.filter(user=self).delete()
                SMSSetting.objects.filter(user=self).delete()
                ReminderSetting.objects.filter(user=self).delete()
                OrderNotificationMessage.objects.filter(user=self).delete()
            except ImportError:
                pass
            
            # 9. Delete other vendor models
            try:
                from vendor.models import (
                    coupon, Post, Reel, BannerCampaign, Party, Wallet, WalletTransaction,
                    DeliveryBoy, DeliverySettings, DeliveryEarnings, VendorCoverage,
                    NotificationCampaign, Offer, OfferMedia
                )
                # Coupons
                coupon.objects.filter(user=self).delete()
                
                # Posts and reels
                Post.objects.filter(user=self).delete()
                Reel.objects.filter(user=self).delete()
                BannerCampaign.objects.filter(user=self).delete()
                
                # Party
                Party.objects.filter(user=self).delete()
                
                # Wallet (delete transactions first)
                wallet_ids = list(Wallet.objects.filter(user=self).values_list('id', flat=True))
                if wallet_ids:
                    WalletTransaction.objects.filter(wallet_id__in=wallet_ids).delete()
                Wallet.objects.filter(user=self).delete()
                
                # Delivery-related
                DeliveryBoy.objects.filter(user=self).delete()
                DeliverySettings.objects.filter(user=self).delete()
                DeliveryEarnings.objects.filter(user=self).delete()
                
                # Coverage
                VendorCoverage.objects.filter(user=self).delete()
                
                # Notification campaigns
                NotificationCampaign.objects.filter(user=self).delete()
                
                # Offers (seller) - delete OfferMedia first, then Offers (though OfferMedia will cascade, being explicit is safer)
                OfferMedia.objects.filter(offer__seller=self).delete()
                Offer.objects.filter(seller=self).delete()
            except ImportError:
                pass
            
            # 10. Delete ledger entries (before Django's CASCADE tries to delete them)
            CashLedger.objects.filter(user=self).delete()
            CashBalance.objects.filter(user=self).delete()
            
            if bank_ids:
                BankLedger.objects.filter(bank_id__in=bank_ids).delete()
            
            if customer_ids:
                CustomerLedger.objects.filter(customer_id__in=customer_ids).delete()
            
            if vendor_ids:
                VendorLedger.objects.filter(vendor_id__in=vendor_ids).delete()
            
            # 11. Delete customer-related models (Order, Cart, Address, etc.)
            # These need to be deleted in order to avoid foreign key constraint errors
            try:
                from customer.models import (
                    Order, OrderItem, OrderPrintJob, OrderPrintFile,
                    Cart, PrintJob, PrintFile, Address,
                    ReturnExchange, Favourite, FavouriteStore, Follower,
                    Review, ProductRequest, SupportTicket, TicketMessage
                )
                from users.models import DeviceToken
                
                # Delete in order (children before parents where applicable)
                # Order-related: Delete print files/jobs before order items, order items before orders
                OrderPrintFile.objects.filter(print_job__order_item__order__user=self).delete()
                OrderPrintJob.objects.filter(order_item__order__user=self).delete()
                ReturnExchange.objects.filter(user=self).delete()  # Also references order_item
                OrderItem.objects.filter(order__user=self).delete()
                Order.objects.filter(user=self).delete()
                
                # Cart-related: Delete print files/jobs before cart
                PrintFile.objects.filter(print_job__cart__user=self).delete()
                PrintJob.objects.filter(cart__user=self).delete()
                Cart.objects.filter(user=self).delete()
                
                # Other customer models
                Address.objects.filter(user=self).delete()
                Favourite.objects.filter(user=self).delete()
                FavouriteStore.objects.filter(user=self).delete()
                Follower.objects.filter(user=self).delete()
                Follower.objects.filter(follower=self).delete()  # Also when user is being followed
                Review.objects.filter(user=self).delete()
                ProductRequest.objects.filter(user=self).delete()
                TicketMessage.objects.filter(sender=self).delete()
                SupportTicket.objects.filter(user=self).delete()
                
                # User token
                DeviceToken.objects.filter(user=self).delete()
            except ImportError:
                # If customer models are not available, Django's CASCADE will handle it
                pass
            
            # 11. Delete UserRole relationships (Django CASCADE will handle this, but being explicit)
            # Note: UserRole is defined later in this file, but Django CASCADE should handle it automatically
            
            # 12. Delete vendor banks, customers, and vendors (these should be last as many things reference them)
            if bank_ids:
                vendor_bank.objects.filter(id__in=bank_ids).delete()
            if customer_ids:
                vendor_customers.objects.filter(id__in=customer_ids).delete()
            if vendor_ids:
                vendor_vendors.objects.filter(id__in=vendor_ids).delete()
            
            # Now call the parent delete method which will handle remaining CASCADE deletion
            # This will handle AbstractUser's built-in relationships (groups, user_permissions, etc.)
            return super().delete(using=using, keep_parents=keep_parents)


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user} - {self.role}"


class MenuModule(models.Model):
    title = models.CharField(max_length=100)
    url_name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=100, blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    def __str__(self):
        return self.title


class RoleMenuPermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    menu_module = models.ForeignKey(MenuModule, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'menu_module')



class DeviceToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_token")
    token = models.CharField(max_length=255)  # FCM token
    updated_at = models.DateTimeField(auto_now=True)
