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
        Override delete_queryset to ensure all transactions and ledger entries are deleted
        before Django's CASCADE deletion tries to process them.
        This prevents foreign key constraint errors.
        """
        from vendor.models import (
            CashLedger, CashBalance, BankLedger, CustomerLedger, VendorLedger,
            vendor_bank, vendor_customers, vendor_vendors,
            Purchase, Expense, Sale, Payment, BankTransfer, CashTransfer
        )
        
        with transaction.atomic():
            for user in queryset:
                # Get all related object IDs BEFORE any deletions
                bank_ids = list(vendor_bank.objects.filter(user=user).values_list('id', flat=True))
                customer_ids = list(vendor_customers.objects.filter(user=user).values_list('id', flat=True))
                vendor_ids = list(vendor_vendors.objects.filter(user=user).values_list('id', flat=True))
                
                # IMPORTANT: Delete in correct order to avoid constraint errors
                # 1. Delete child items and related objects first
                from vendor.models import PurchaseItem, SaleItem, Reminder, pos_wholesale
                PurchaseItem.objects.filter(purchase__user=user).delete()
                SaleItem.objects.filter(user=user).delete()
                SaleItem.objects.filter(sale__user=user).delete()
                Reminder.objects.filter(user=user).delete()
                Reminder.objects.filter(purchase__user=user).delete()
                Reminder.objects.filter(sale__user=user).delete()
                pos_wholesale.objects.filter(user=user).delete()
                pos_wholesale.objects.filter(sale__user=user).delete()
                
                # 2. Delete transactions that reference banks/customers/vendors
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
                
                # 3. Delete transactions that directly reference User
                Purchase.objects.filter(user=user).delete()
                Sale.objects.filter(user=user).delete()
                Expense.objects.filter(user=user).delete()
                Payment.objects.filter(user=user).delete()
                CashTransfer.objects.filter(user=user).delete()
                BankTransfer.objects.filter(user=user).delete()
                
                # 4. Delete ALL ledger entries (before Django's CASCADE tries to delete them)
                CashLedger.objects.filter(user=user).delete()
                CashBalance.objects.filter(user=user).delete()
                
                if bank_ids:
                    BankLedger.objects.filter(bank_id__in=bank_ids).delete()
                
                if customer_ids:
                    CustomerLedger.objects.filter(customer_id__in=customer_ids).delete()
                
                if vendor_ids:
                    VendorLedger.objects.filter(vendor_id__in=vendor_ids).delete()
            
            # Now call the parent delete_queryset which will handle CASCADE deletion
            super().delete_queryset(request, queryset)

admin.site.register(User, CustomUserAdmin)
admin.site.register(DeviceToken)