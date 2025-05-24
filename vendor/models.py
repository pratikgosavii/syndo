

from django.db import models


from users.models import User
from django.utils.timezone import now
from datetime import datetime, timezone

import pytz
ist = pytz.timezone('Asia/Kolkata')



from users.models import User




class coupon(models.Model):

    COUPON_TYPE_CHOICES = [
    ("discount", "Discount Coupon"),
    ("no_return", "No Return & Exchange"),
    ("online_pay", "Online Pay"),
    ]

    TYPE_CHOICES = [
        ('percent', 'Percentage'),
        ('amount', 'Amount'),
    ]
    
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, null=True, blank=True)
    coupon_type = models.CharField(max_length=10, choices=COUPON_TYPE_CHOICES, default='percent')  # 👈 Add this
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='percent')  # 👈 Add this
    customer_id = models.IntegerField(null=True, blank=True)
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=500, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='doctor_images/')
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField()
    only_followers = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class OnlineStoreSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    store_page_visible = models.BooleanField(default=True)
    store_location_visible = models.BooleanField(default=True)
    display_as_catalog = models.BooleanField(default=False)
    private_catalog = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Store Settings"


class vendor_store(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="vendor_store", blank=True, null=True)

DAYS_OF_WEEK = [
    ('sunday', 'Sunday'),
    ('monday', 'Monday'),
    ('tuesday', 'Tuesday'),
    ('wednesday', 'Wednesday'),
    ('thursday', 'Thursday'),
    ('friday', 'Friday'),
    ('saturday', 'Saturday'),
]

class StoreWorkingHour(models.Model):
    
    store = models.ForeignKey(vendor_store, on_delete=models.CASCADE, related_name='working_hours')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK, unique=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    

    def __str__(self):
        return f"{self.day.title()} - {'Open' if self.is_open else 'Closed'}"


class vendor_vendors(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    balance = models.BigIntegerField()


    def __str__(self):
        return self.name


class vendor_customers(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    balance = models.BigIntegerField()

    def __str__(self):
        return self.name



class addon(models.Model):
    product_category = models.ForeignKey("masters.product_category", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='addons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name





class super_catalogue(models.Model):
    
    TYPE_CHOICES = (
        ('product', 'Product'),
        ('service', 'Service'),
        ('print', 'Print'),
    )

    SALE_TYPE_CHOICES = (
        ('offline', 'Offline Only'),
        ('both', 'Both Online & Offline'),
    )

    product_type  = models.CharField(max_length=10, choices=TYPE_CHOICES, default='product')
    sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES, default='offline')

    name = models.CharField(max_length=255)
    category = models.ForeignKey("masters.product_category", on_delete=models.SET_NULL, null=True, blank=True)
    sub_category = models.CharField(max_length=255, null=True, blank=True)

   
    unit = models.CharField(max_length=50, null=True, blank=True)
    hsn = models.CharField(max_length=50, null=True, blank=True)
    gst = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Stock
    track_serial_numbers = models.BooleanField(default=False)

    # Optional
    brand_name = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)

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


class product(models.Model):
    
    TYPE_CHOICES = (
        ('product', 'Product'),
        ('service', 'Service'),
        ('print', 'Print'),
    )

    SALE_TYPE_CHOICES = (
        ('offline', 'Offline Only'),
        ('online', 'Online Only'),
        ('both', 'Both Online & Offline'),
    )

    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('mg', 'Milligram'),
        ('lb', 'Pound'),
        ('l', 'Litre'),
        ('ml', 'Millilitre'),
        ('km', 'Kilometre'),
        ('m', 'Metre'),
        ('cm', 'Centimetre'),
        ('mm', 'Millimetre'),
        ('pcs', 'Piece'),
        ('box', 'Box'),
        ('unit', 'Unit'),
        ('dozen', 'Dozen'),
        ('set', 'Set'),
        ('pack', 'Pack'),
        ('pair', 'Pair'),
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name='productssdsdsd', null=True, blank=True)

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
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, null=True, blank=True)
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

class PrintVariant(models.Model):
    COLOR_CHOICES = [('color', 'Color'), ('bw', 'Black & White')]
    SIDED_CHOICES = [('single', 'Single Side'), ('both', 'Both Side')]
    
    PAPER_CHOICES = [
        ('a4_70gsm', 'A4 - 70 GSM'),
        ('a4_80gsm', 'A4 - 80 GSM'),
        ('glossy_90gsm', 'Glossy - 90 GSM'),
        ('matte_100gsm', 'Matte - 100 GSM'),
        ('a3_70gsm', 'A3 - 70 GSM'),
        # Add more commonly used types
    ]

    product = models.ForeignKey(product, related_name='print_variants', on_delete=models.CASCADE)
    paper = models.CharField(max_length=30, choices=PAPER_CHOICES)
    color_type = models.CharField(max_length=10, choices=COLOR_CHOICES)
    sided = models.CharField(max_length=10, choices=SIDED_CHOICES)
    min_quantity = models.PositiveIntegerField()
    max_quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_color_type_display()} | {self.get_sided_display()} | {self.get_paper_display()}"
    
    
class ProductSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="product_settings")

    # Product Fields
    wholesale_price = models.BooleanField(default=False)
    stock = models.BooleanField(default=False)
    imei = models.BooleanField(default=False)
    low_stock_alert = models.BooleanField(default=False)
    category = models.BooleanField(default=False)
    sub_category = models.BooleanField(default=False)
    brand_name = models.BooleanField(default=False)
    color = models.BooleanField(default=False)
    size = models.BooleanField(default=False)
    batch_number = models.BooleanField(default=False)
    expiry_date = models.BooleanField(default=False)
    description = models.BooleanField(default=False)
    image = models.BooleanField(default=False)
    tax = models.BooleanField(default=False)
    food = models.BooleanField(default=False)

    # Delivery
    instant_delivery = models.BooleanField(default=False)
    self_pickup = models.BooleanField(default=False)
    general_delivery = models.BooleanField(default=False)

    # Policies
    return_policy = models.BooleanField(default=False)
    cod = models.BooleanField(default=False)
    replacement = models.BooleanField(default=False)
    shop_exchange = models.BooleanField(default=False)
    shop_warranty = models.BooleanField(default=False)
    brand_warranty = models.BooleanField(default=False)

    # Catalog
    online_catalog_only = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Settings"
    


class SpotlightProduct(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(product, on_delete=models.CASCADE)
    discount_tag = models.CharField(max_length=255, blank=True, null=True)
    boost = models.BooleanField(default=False)
    budget = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.product.name


class Post(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # user who created post
    media = models.FileField(upload_to='posts/')  # upload media
    description = models.TextField(blank=True)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)
    boost_post = models.BooleanField(default=False)
    budget = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class Reel(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # user who created post
    media = models.FileField(upload_to='posts/')  # upload media
    description = models.TextField(blank=True)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)
    boost_post = models.BooleanField(default=False)
    budget = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)



import uuid

class Purchase(models.Model):
    
    BANK_CASH_CHOICES = [
        ('bank', 'Bank'),
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    purchase_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    # other fields...

    
    purchase_date = models.DateField()
    vendor = models.ForeignKey(vendor_vendors, on_delete=models.CASCADE)
    product = models.CharField(max_length=255, blank=True, null=True)
    supplier_invoice_date = models.DateField(blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    # Optional fields
    dispatch_address = models.CharField(max_length=255, blank=True, null=True)
    payment_type = models.CharField(
        max_length=100,
        choices=BANK_CASH_CHOICES,
        blank=True,
        null=True
    )
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    extra_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    delivery_shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    packaging_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.purchase_code
    

            

class CompanyProfile(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
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


class Expense(models.Model):
    PAYMENT_TYPES = [
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('cheque', 'Cheque'),
        ('emi', 'EMI'),
        ('netbanking', 'Netbanking'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    category = models.ForeignKey("masters.expense_category", on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_date = models.DateField(null=True, blank=True)
    bank = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    attachment = models.FileField(upload_to='expenses/', null=True, blank=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"


        
class Party(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.name

from decimal import Decimal

class Sale(models.Model):

    PAYMENT_CHOICES = [
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('credit', 'Credit'),
    ]

    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)


    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=50, null=True, blank=True)
    customer_mobile = models.CharField(max_length=14, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    credit_time_days = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_wholesale_rate = models.BooleanField(default=False)

    total_items = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self):
        return sum(item.amount for item in self.items.all())

    @property
    def total_discount(self):
        return round((self.discount_percentage / Decimal("100")) * self.total_amount, 2)

    @property
    def total_tax(self):
        discount_amount = self.total_discount
        taxable_amount = self.total_amount - discount_amount
        return round(taxable_amount * (self.tax_percentage / Decimal("100")), 2)

    @property
    def final_amount(self):
        return round(self.total_amount - self.total_discount + self.total_tax, 2)

    def __str__(self):
        return f"Sale #{self.id} - {self.party.name if self.party else 'Walk-in'}"

class SaleItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of sale

    @property
    def amount(self):
        return round(self.quantity * self.price, 2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"