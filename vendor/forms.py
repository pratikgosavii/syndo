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



class coupon_Form(forms.ModelForm):
    class Meta:
        model = coupon
        fields = '__all__'  # Include all fields
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Coupon Code'}),
            'coupon_type': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'customer_id': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Coupon Code'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_purchase': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'only_followers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OnlineStoreSettingForm(forms.ModelForm):
    class Meta:
        model = OnlineStoreSetting
        fields = [
            'store_page_visible',
            'store_location_visible',
            'display_as_catalog',
            'private_catalog'
        ]
        widgets = {
            'store_page_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'store_location_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_as_catalog': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'private_catalog': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class super_catalogue_Form(forms.ModelForm):
    class Meta:
        model = super_catalogue
        fields = '__all__'
        widgets = {
            'product_type': forms.Select(attrs={'class': 'form-control'}),
            'sale_type': forms.Select(attrs={'class': 'form-control'}),

            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'sub_category': forms.TextInput(attrs={'class': 'form-control'}),

            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'hsn': forms.TextInput(attrs={'class': 'form-control'}),

            'track_serial_numbers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'brand_name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gst': forms.NumberInput(attrs={'class': 'form-control'}),

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


class product_Form(forms.ModelForm):
    class Meta:
        model = product
        fields = '__all__'
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'product_type': forms.Select(attrs={'id': 'productType', 'class': 'form-control'}),
            'sale_type': forms.Select(attrs={'id': 'saleType', 'class': 'form-control'}),
            'food_type': forms.Select(attrs={'id': 'foodType', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'sub_category': forms.Select(attrs={'class': 'form-control'}),

            'wholesale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'sales_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'mrp': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'hsn': forms.TextInput(attrs={'class': 'form-control'}),
            'gst': forms.NumberInput(attrs={'class': 'form-control'}),

            'track_serial_numbers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'opening_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_alert': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'low_stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),

            'brand_name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={
                'id': 'color_value',
                'readonly': 'readonly',
                'placeholder': '#ffffff',
                'style': 'width: 100px;',
            }),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'gallery_images': forms.ClearableFileInput(attrs={'class': 'form-control'}),

            'is_customize': forms.CheckboxInput(attrs={'class': 'form-check-input', "id" : "customPrintToggle"}),
            'instant_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'self_pickup': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'general_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_on_shop': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            'return_policy': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cod': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'replacement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'shop_exchange': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'shop_warranty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'brand_warranty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'tax_inclusive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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

class VendorBankForm(forms.ModelForm):
    class Meta:
        model = vendor_bank
        fields = [
            'name',
            'account_holder',
            'account_number',
            'ifsc_code',
            'branch',
            'balance',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name'}),
            'account_holder': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Holder Name'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IFSC Code'}),
            'branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch Name'}),
            'balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter balance'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductAddonForm(forms.ModelForm):
    class Meta:
        model = product_addon
        fields = ['addon']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # 👈 get the user from view
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['addon'].queryset = addon.objects.filter(user=user, is_active=True)
        else:
            self.fields['addon'].queryset = addon.objects.none()

        self.fields['addon'].label_from_instance = lambda obj: f"{obj.name} (₹{obj.price_per_unit})"

        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

                

class PrintVariantForm(forms.ModelForm):
    class Meta:
        model = PrintVariant
        fields = ['product', 'paper', 'color_type', 'min_quantity', 'max_quantity', 'price', 'sided']



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

        # ✅ Make DELETE field not required and style it
        if 'DELETE' in self.fields:
            self.fields['DELETE'].required = False
            self.fields['DELETE'].widget.attrs.update({'class': 'form-check-input'})

                    

class CustomizePrintVariantForm(forms.ModelForm):
    class Meta:
        model = CustomizePrintVariant
        fields = ['size', 'price']



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    # ✅ Make DELETE field not required and style it
        if 'DELETE' in self.fields:
            self.fields['DELETE'].required = False
            self.fields['DELETE'].widget.attrs.update({'class': 'form-check-input'})



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


class vendor_vendorsForm(forms.ModelForm):
    
    class Meta:
        model = vendor_vendors
        fields = [
            'name', 'email', 'contact', 'balance',
            'company_name', 'gst', 'aadhar', 'pan',
            'address_line_1', 'address_line_2', 'pincode',
            'city', 'state', 'country'
        ]
        widgets = {
            field: forms.TextInput(attrs={'class': 'form-control'}) 
            for field in fields
        }


class vendor_customersForm(forms.ModelForm):
    class Meta:
        model = vendor_customers
        exclude = ['user']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email ID'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Balance'}),

            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GST'}),
            'aadhar_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aadhar Number'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PAN'}),

            'billing_address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'billing_address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2'}),
            'billing_pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            'billing_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'billing_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'billing_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),

            'dispatch_address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'dispatch_address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2'}),
            'dispatch_pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            'dispatch_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'dispatch_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'dispatch_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),

            'transport_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transport Name'}),
        }




class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Party Name'}),
            'mobile_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
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
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'pan': forms.TextInput(attrs={'class': 'form-control'}),
            'upi_id': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'signature': forms.FileInput(attrs={'class': 'form-control'}),
            'payment_qr': forms.FileInput(attrs={'class': 'form-control'}),
        }



from django.utils import timezone


class PurchaseForm(forms.ModelForm):

    purchase_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date()
    )

    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Purchase
        exclude = ['user']  # We don't want the user to manually pick this
        widgets = {
            'purchase_code': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),

            'supplier_invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),

            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),

            'payment_method': forms.Select(attrs={'class': 'form-control', 'id': 'payment_method'}),

            'advance_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'advance_mode': forms.Select(attrs={'class': 'form-control'}),
            
            'eway_bill_no': forms.TextInput(attrs={'class': 'form-control'}),
            'lr_no': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_no': forms.TextInput(attrs={'class': 'form-control', 'id' : 'vehicle_number'}),
            'transport_name': forms.TextInput(attrs={'class': 'form-control', 'id' : 'vehicle_number'}),

            'dispatch_address': forms.TextInput(attrs={'class': 'form-control'}),
            'references': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),

            'delivery_shipping_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'packaging_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # 👈 move this up first
        super().__init__(*args, **kwargs)

        if not self.instance.pk or not self.instance.purchase_code:
            self.fields['purchase_code'].initial = self.generate_unique_code()

        if user is not None:
            self.fields['vendor'].queryset = vendor_vendors.objects.filter(user=user)

            
    def generate_unique_code(self):
        prefix = "SVIN-PUR-"
        last_purchase = Purchase.objects.filter(purchase_code__startswith=prefix).order_by('purchase_code').last()

        if not last_purchase:
            new_number = 1
        else:
            try:
                last_number = int(last_purchase.purchase_code.replace(prefix, ''))
            except (ValueError, AttributeError):
                last_number = 0

            new_number = last_number + 1

        return f"{prefix}{new_number:05d}"  # 5-digit number: 00001, 00002, etc.
        
from django.forms import ModelForm, inlineformset_factory
        
class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['product']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control select2'}),
        }



class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bank': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }



class StoreWorkingHourForm(forms.ModelForm):
    class Meta:
        model = StoreWorkingHour
        fields = ['day', 'open_time', 'close_time', 'is_open']
        widgets = {
            'open_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'close_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }





class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'price']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select product-select select2',
                'id': None  # <- This is key
            }),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control price-input', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(SaleItemForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['product'].queryset = product.objects.filter(user=user)


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = '__all__'
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select select2'}),
            'sale_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'company_profile': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(SaleForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['customer'].queryset = vendor_customers.objects.filter(user=user)
            self.fields['company_profile'].queryset = CompanyProfile.objects.filter(user=user)


class pos_wholesaleForm(forms.ModelForm):
    class Meta:
        model = pos_wholesale
        fields = [
            'invoice_type',
            'invoice_number',
            'date',

            # Optional Fields
            'dispatch_address',
            'delivery_city',
            'signature',
            'references',
            'notes',
            'terms',
            'delivery_charges',
            'reverse_charges',
            'packaging_charges',
            'eway_bill_number',
            'lr_number',
            'vehicle_number',
            'transport_name',
            'number_of_parcels',
        ]

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_city': forms.TextInput(attrs={'class': 'form-control', 'delivery_city' : 'delivery_city'}),

            'dispatch_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'references': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            'delivery_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reverse_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'packaging_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),

            'eway_bill_number': forms.TextInput(attrs={'class': 'form-control'}),
            'lr_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'id' : 'vehicle_number'}),
            'transport_name': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_parcels': forms.NumberInput(attrs={'class': 'form-control', 'id' : 'number_of_parcels'}),

            'signature': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(pos_wholesaleForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False  # All optional



from django import forms


class DeliveryBoyForm(forms.ModelForm):
    class Meta:
        model = DeliveryBoy
        fields = ['name', 'mobile', 'photo', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class DeliverySettingsForm(forms.ModelForm):
    class Meta:
        model = DeliverySettings
        fields = [
            'instant_order_prep_time',
            'general_delivery_days',
            'delivery_charge_per_km',
            'minimum_base_fare'
        ]
        widgets = {
            'instant_order_prep_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'general_delivery_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_charge_per_km': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_base_fare': forms.NumberInput(attrs={'class': 'form-control'}),
        }




class DeliveryModeForm(forms.ModelForm):
    class Meta:
        model = DeliveryMode
        fields = ['is_auto_assign_enabled']
        widgets = {
            'is_auto_assign_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class BankTransferForm(forms.Form):
    amount = forms.DecimalField(min_value=1, decimal_places=2, max_digits=10, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    bank_account = forms.ModelChoiceField(
        queryset=vendor_bank.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['bank_account'].queryset = vendor_bank.objects.filter(user=user)




class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['type', 'party', 'party_name', 'amount', 'payment_date', 'payment_type', 'account', 'notes', 'attachment']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }



        
class TaxSettingsForm(forms.ModelForm):
    class Meta:
        model = TaxSettings
        exclude = ['user']
        widgets = {field: forms.CheckboxInput(attrs={'class': 'form-check-input'}) for field in model._meta.get_fields() if field.name != 'user'}

class InvoiceSettingsForm(forms.ModelForm):
    class Meta:
        model = InvoiceSettings
        exclude = ['user']
        widgets = {field: forms.CheckboxInput(attrs={'class': 'form-check-input'}) for field in model._meta.get_fields() if field.name != 'user'}