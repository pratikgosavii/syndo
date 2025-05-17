

from django.db import models


from users.models import User
from django.utils.timezone import now
from datetime import datetime, timezone

import pytz
ist = pytz.timezone('Asia/Kolkata')



from users.models import User





class addon(models.Model):
    product_category = models.ForeignKey("masters.product_category", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='addons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name





class product(models.Model):
    
    TYPE_CHOICES = (
        ('product', 'Product'),
        ('service', 'Service'),
        ('print', 'Print'),
    )

    SALE_TYPE_CHOICES = (
        ('offline', 'Offline Only'),
        ('both', 'Both Online & Offline'),
    )

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name='productssdsdsd')

    product_type  = models.CharField(max_length=10, choices=TYPE_CHOICES, default='product')
    sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES, default='offline')

    name = models.CharField(max_length=255)
    category = models.ForeignKey("masters.product_category", on_delete=models.SET_NULL, null=True, blank=True)
    sub_category = models.CharField(max_length=255, null=True, blank=True)

    # Pricing details
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    hsn = models.CharField(max_length=50, null=True, blank=True)
    gst = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Stock
    track_serial_numbers = models.BooleanField(default=False)
    opening_stock = models.IntegerField(null=True, blank=True)
    low_stock_alert = models.BooleanField(default=False)
    low_stock_quantity = models.IntegerField(null=True, blank=True)
    stock = models.IntegerField(null=True, blank=True)

    # Optional
    brand_name = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    batch_number = models.CharField(max_length=100, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    gallery_images = models.ImageField(upload_to='product_gallery/', null=True, blank=True)

    # Delivery & Policies
    instant_delivery = models.BooleanField(default=False)
    self_pickup = models.BooleanField(default=False)
    general_delivery = models.BooleanField(default=False)

    return_policy = models.BooleanField(default=False)
    cod = models.BooleanField(default=False)
    replacement = models.BooleanField(default=False)
    shop_exchange = models.BooleanField(default=False)
    shop_warranty = models.BooleanField(default=False)
    brand_warranty = models.BooleanField(default=False)

    # Flags
    is_popular = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def current_stock(self):
        if self.track_serial_numbers:
            return self.serials.filter(is_sold=False).count()
        return self.stock or 0


class ProductSerial(models.Model):
    product = models.ForeignKey(product, on_delete=models.CASCADE, related_name='serials')
    serial_number = models.CharField(max_length=100, unique=True)
    is_sold = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.serial_number}"



class product_addon(models.Model):
  
    product = models.ForeignKey('product', on_delete=models.CASCADE, null=True, blank=True)
    addon = models.ForeignKey('addon', on_delete=models.CASCADE, null=True, blank=True)
    # Optional: if you want to override price or add quantity etc.

    def __str__(self):
        return f"{self.product.name} - {self.addon.name}"


class SpotlightProduct(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(product, on_delete=models.CASCADE)
    discount_tag = models.CharField(max_length=255, blank=True, null=True)
    boost = models.BooleanField(default=False)
    budget = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.product.name


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purchase_code = models.CharField(max_length=50)
    purchase_date = models.DateField()
    vendor = models.CharField(max_length=255, blank=True, null=True)
    product = models.CharField(max_length=255, blank=True, null=True)
    supplier_invoice_date = models.DateField(blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    # Optional fields
    dispatch_address = models.CharField(max_length=255, blank=True, null=True)
    bank_cash = models.CharField(max_length=100, blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    extra_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    delivery_shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    packaging_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.purchase_code
    
    
class CompanyProfile(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    brand_name = models.CharField(max_length=255)
    billing_address = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    pan = models.CharField(max_length=10, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='company_profiles/', blank=True, null=True)

    def __str__(self):
        return self.company_name

