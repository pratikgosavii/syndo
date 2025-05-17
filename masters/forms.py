from django import forms

from .models import *
from django.contrib.admin.widgets import  AdminDateWidget, AdminTimeWidget, AdminSplitDateTime


class coupon_Form(forms.ModelForm):
    class Meta:
        model = coupon
        fields = '__all__'  # Include all fields
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Coupon Code'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Coupon Code'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_purchase': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }




class testimonials_Form(forms.ModelForm):
    class Meta:
        model = testimonials
        fields = '__all__'
        widgets = {
           
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'name'
            }),

            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
          
            'description': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'price'
            }),

        }



class product_category_Form(forms.ModelForm):
    class Meta:
        model = product_category
        fields = '__all__'
        widgets = {
           
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'name'
            }),

            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),


        }

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

class event_Form(forms.ModelForm):
    class Meta:
        model = event
        fields = ['name', 'image', 'description', 'start_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control description-box'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),

        }



class customer_address_Form(forms.ModelForm):
    class Meta:
        model = customer_address
        fields = ['name', 'type', 'address', 'landmark', 'pin_code', 'city', 'state']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'landmark': forms.TextInput(attrs={'class': 'form-control'}),
            'pin_code': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
        }


class home_banner_Form(forms.ModelForm):
    class Meta:
        model = home_banner
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'discription': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),

        }