from django import forms

from .models import *
from django.contrib.admin.widgets import  AdminDateWidget, AdminTimeWidget, AdminSplitDateTime






# class product_Form(forms.ModelForm):
#     class Meta:
#         model = product
#         fields = ['name', 'category', 'description', 'image', 'price', 'rating', 'is_popular', 'is_featured', 'is_active']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
#             'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
#             'price': forms.NumberInput(attrs={'class': 'form-control'}),
#             'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '5'}),
#             'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }


class product_Form(forms.ModelForm):
    class Meta:
        model = product
        fields = '__all__'
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'product_type': forms.Select(attrs={'class': 'form-control'}),
            'sale_type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'sub_category': forms.TextInput(attrs={'class': 'form-control'}),

            'wholesale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'sales_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'mrp': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'hsn': forms.TextInput(attrs={'class': 'form-control'}),
            'gst': forms.NumberInput(attrs={'class': 'form-control'}),

            'track_serial_numbers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'opening_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_alert': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'low_stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),

            'brand_name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'gallery_images': forms.ClearableFileInput(attrs={'class': 'form-control'}),

            'instant_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'self_pickup': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'general_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'return_policy': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cod': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'replacement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'shop_exchange': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'shop_warranty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'brand_warranty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'is_popular': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class addon_Form(forms.ModelForm):
    class Meta:
        model = addon
        fields = ['product_category', 'name', 'price_per_unit', 'description', 'image']
        widgets = {
            'product_category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Lee White T shirt XL size', 'class': 'form-control'}),
            'price_per_unit': forms.NumberInput(attrs={'placeholder': 'Enter here', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }



class ProductAddonForm(forms.ModelForm):
    class Meta:
        model = product_addon
        fields = ['addon']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['addon'].queryset = addon.objects.filter(is_active=True)
        self.fields['addon'].label_from_instance = lambda obj: f"{obj.name} (₹{obj.price_per_unit})"



class SpotlightProductForm(forms.ModelForm):
    class Meta:
        model = SpotlightProduct
        fields = ['product', 'discount_tag', 'boost', 'budget', 'user']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'discount_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'boost': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'min': 10}),
        }


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = '__all__'
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'pan': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


