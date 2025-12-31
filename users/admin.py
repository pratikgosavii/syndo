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

admin.site.register(User, CustomUserAdmin)
admin.site.register(DeviceToken)