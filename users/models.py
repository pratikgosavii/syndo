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
            # Get all related object IDs BEFORE any deletions
            bank_ids = list(vendor_bank.objects.filter(user=self).values_list('id', flat=True))
            customer_ids = list(vendor_customers.objects.filter(user=self).values_list('id', flat=True))
            vendor_ids = list(vendor_vendors.objects.filter(user=self).values_list('id', flat=True))
            
            # IMPORTANT: Delete transactions FIRST, then ledger entries
            # This ensures transaction delete signals run first and clean up their own ledger entries
            
            # 1. Delete transactions that reference banks/customers/vendors
            # These will trigger their own delete signals which will clean up ledger entries
            if bank_ids:
                # Delete transactions that reference these banks
                BankTransfer.objects.filter(from_bank_id__in=bank_ids).delete()
                BankTransfer.objects.filter(to_bank_id__in=bank_ids).delete()
                Purchase.objects.filter(advance_bank_id__in=bank_ids).delete()
                Expense.objects.filter(bank_id__in=bank_ids).delete()
                Sale.objects.filter(advance_bank_id__in=bank_ids).delete()
                Payment.objects.filter(bank_account_id__in=bank_ids).delete()
            
            if customer_ids:
                # Delete transactions that reference these customers
                Sale.objects.filter(customer_id__in=customer_ids).delete()
                Payment.objects.filter(customer_id__in=customer_ids).delete()
            
            if vendor_ids:
                # Delete transactions that reference these vendors
                Purchase.objects.filter(vendor_id__in=vendor_ids).delete()
                Payment.objects.filter(vendor_id__in=vendor_ids).delete()
            
            # 2. Delete CashTransfer entries for this user
            CashTransfer.objects.filter(user=self).delete()
            
            # 3. Now delete any remaining ledger entries (in case some weren't cleaned up by signals)
            # Delete ALL ledger entries (before Django's CASCADE tries to delete them)
            
            # Delete CashLedger entries (direct FK to User)
            CashLedger.objects.filter(user=self).delete()
            
            # Delete CashBalance (direct FK to User)
            CashBalance.objects.filter(user=self).delete()
            
            # Delete BankLedger entries (FK to vendor_bank which will be CASCADE deleted)
            if bank_ids:
                BankLedger.objects.filter(bank_id__in=bank_ids).delete()
            
            # Delete CustomerLedger entries (FK to vendor_customers which will be CASCADE deleted)
            if customer_ids:
                CustomerLedger.objects.filter(customer_id__in=customer_ids).delete()
            
            # Delete VendorLedger entries (FK to vendor_vendors which will be CASCADE deleted)
            if vendor_ids:
                VendorLedger.objects.filter(vendor_id__in=vendor_ids).delete()
            
            # Now call the parent delete method which will handle CASCADE deletion
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
