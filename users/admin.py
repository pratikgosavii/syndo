import json
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import User, DeviceToken
from .forms import *  # Import your custom form
from vendor.models import VendorList

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
    
    def delete_model(self, request, obj):
        """
        Override delete_model to handle single user deletion from admin change page.
        This ensures all related objects are deleted before Django's CASCADE deletion.
        """
        # Use the User model's custom delete method which handles all cascading
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        """
        Override delete_queryset to ensure all transactions and ledger entries are deleted
        before Django's CASCADE deletion tries to process them.
        This prevents foreign key constraint errors.
        """
        # Use the User model's custom delete method for each user in queryset
        with transaction.atomic():
            for user in queryset:
                user.delete()

class VendorListAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "user", "gstin", "is_gstin_verified", "is_bank_verified",
        "gstin_verified_at", "bank_verified_at",
    )
    list_filter = ("is_gstin_verified", "is_bank_verified")
    search_fields = ("name", "user__mobile", "gstin")
    readonly_fields = (
        "user", "name", "storetag", "pan_number", "gstin", "bank_account_number", "bank_ifsc",
        "is_pan_verified", "pan_verified_at",
        "is_gstin_verified", "gstin_verified_at", "gstin_response_preview",
        "is_bank_verified", "bank_verified_at", "bank_response_preview",
        "kyc_last_error",
    )
    fieldsets = (
        (None, {"fields": ("user", "name", "storetag")}),
        ("KYC – PAN", {"fields": ("pan_number", "is_pan_verified", "pan_verified_at")}),
        (
            "KYC – GST",
            {
                "fields": (
                    "gstin",
                    "is_gstin_verified",
                    "gstin_verified_at",
                    "gstin_response_preview",
                )
            },
        ),
        (
            "KYC – Bank",
            {
                "fields": (
                    "bank_account_number",
                    "bank_ifsc",
                    "is_bank_verified",
                    "bank_verified_at",
                    "bank_response_preview",
                )
            },
        ),
        ("KYC error", {"fields": ("kyc_last_error",)}),
    )
    change_form_template = "admin/users/vendorlist/change_form.html"

    def gstin_response_preview(self, obj):
        if not obj.gstin_response_data:
            return "-"
        return format_html(
            '<pre style="max-height:320px;overflow:auto;white-space:pre-wrap;">{}</pre>',
            json.dumps(obj.gstin_response_data, indent=2, default=str),
        )

    gstin_response_preview.short_description = "GSTIN API response (stored)"

    def bank_response_preview(self, obj):
        if not obj.bank_response_data:
            return "-"
        return format_html(
            '<pre style="max-height:320px;overflow:auto;white-space:pre-wrap;">{}</pre>',
            json.dumps(obj.bank_response_data, indent=2, default=str),
        )

    bank_response_preview.short_description = "Bank API response (stored)"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/verify-gst/",
                self.admin_site.admin_view(self.verify_gst_view),
                name="users_vendorlist_verify_gst",
            ),
            path(
                "<path:object_id>/verify-bank/",
                self.admin_site.admin_view(self.verify_bank_view),
                name="users_vendorlist_verify_bank",
            ),
        ]
        return custom + urls

    def verify_gst_view(self, request, object_id):
        from vendor.models import vendor_store
        store = vendor_store.objects.filter(pk=object_id).first()
        if not store:
            messages.error(request, "Vendor store not found.")
            return redirect("admin:users_vendorlist_changelist")
        store.is_gstin_verified = True
        store.gstin_verified_at = timezone.now()
        store.save(update_fields=["is_gstin_verified", "gstin_verified_at"])
        messages.success(request, "GST verified manually for this vendor.")
        return redirect("admin:users_vendorlist_change", object_id=object_id)

    def verify_bank_view(self, request, object_id):
        from vendor.models import vendor_store
        store = vendor_store.objects.filter(pk=object_id).first()
        if not store:
            messages.error(request, "Vendor store not found.")
            return redirect("admin:users_vendorlist_changelist")
        store.is_bank_verified = True
        store.bank_verified_at = timezone.now()
        store.save(update_fields=["is_bank_verified", "bank_verified_at"])
        messages.success(request, "Bank verified manually for this vendor.")
        return redirect("admin:users_vendorlist_change", object_id=object_id)


admin.site.register(User, CustomUserAdmin)
admin.site.register(DeviceToken)
admin.site.register(VendorList, VendorListAdmin)