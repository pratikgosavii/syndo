from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from .models import User
from .forms import *  # Import your custom form

class CustomUserAdmin(UserAdmin):
   
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ('mobile', 'email', 'is_staff', 'is_active', 'is_customer', 'is_vendor', 'is_subuser')
    list_filter = ('is_staff', 'is_active', 'is_customer', 'is_vendor', 'is_subuser')

    fieldsets = (
        (None, {'fields': ('mobile', 'email', 'password', 'firebase_uid')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser')}),
        ('Roles', {'fields': ('is_customer', 'is_vendor', 'is_subuser')}),
        ('Groups & Permissions', {'fields': ('groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('mobile', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    search_fields = ('mobile',)
    ordering = ('mobile',)
    
    def delete_queryset(self, request, queryset):
        """
        Override delete_queryset to ensure all ledger entries are deleted
        before Django's CASCADE deletion tries to process them.
        This prevents foreign key constraint errors.
        """
        from vendor.models import CashLedger, CashBalance, BankLedger, CustomerLedger, VendorLedger
        from vendor.models import vendor_bank, vendor_customers, vendor_vendors
        
        with transaction.atomic():
            for user in queryset:
                # Get all related object IDs BEFORE any deletions
                bank_ids = list(vendor_bank.objects.filter(user=user).values_list('id', flat=True))
                customer_ids = list(vendor_customers.objects.filter(user=user).values_list('id', flat=True))
                vendor_ids = list(vendor_vendors.objects.filter(user=user).values_list('id', flat=True))
                
                # Delete ALL ledger entries FIRST (before Django's CASCADE tries to delete them)
                # This prevents foreign key constraint errors
                
                # 1. Delete CashLedger entries (direct FK to User)
                CashLedger.objects.filter(user=user).delete()
                
                # 2. Delete CashBalance (direct FK to User)
                CashBalance.objects.filter(user=user).delete()
                
                # 3. Delete BankLedger entries (FK to vendor_bank which will be CASCADE deleted)
                if bank_ids:
                    BankLedger.objects.filter(bank_id__in=bank_ids).delete()
                
                # 4. Delete CustomerLedger entries (FK to vendor_customers which will be CASCADE deleted)
                if customer_ids:
                    CustomerLedger.objects.filter(customer_id__in=customer_ids).delete()
                
                # 5. Delete VendorLedger entries (FK to vendor_vendors which will be CASCADE deleted)
                if vendor_ids:
                    VendorLedger.objects.filter(vendor_id__in=vendor_ids).delete()
            
            # Now call the parent delete_queryset which will handle CASCADE deletion
            super().delete_queryset(request, queryset)

admin.site.register(User, CustomUserAdmin)
admin.site.register(DeviceToken)