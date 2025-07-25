

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
    image = models.ImageField(upload_to='doctor_images/', null=True, blank=True)
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField()
    only_followers = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

class BannerCampaign(models.Model):
    REDIRECT_CHOICES = [
        ('store', 'Store'),
        ('product', 'Product'),
        ('category', 'Category'),
        ('external', 'External URL'),
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name='banners')
    banner_image = models.ImageField(upload_to='campaign_banners/', help_text="Max 1MB, Ratio 1:3")
    campaign_name = models.CharField(max_length=255)
    redirect_to = models.CharField(max_length=20, choices=REDIRECT_CHOICES)
    redirect_target = models.CharField(max_length=255, blank=True, null=True)  # ID or URL

    boost_post = models.BooleanField(default=False)
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.campaign_name
    

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
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('store', 'day')

    def __str__(self):
        return f"{self.day.title()} - {'Open' if self.is_open else 'Closed'}"


class vendor_vendors(models.Model):
    
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    balance = models.BigIntegerField()

    # Business Details
    company_name = models.CharField(max_length=100, blank=True, null=True)
    gst = models.CharField(max_length=20, blank=True, null=True)
    aadhar = models.CharField(max_length=20, blank=True, null=True)
    pan = models.CharField(max_length=20, blank=True, null=True)

    # Address
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)



    def __str__(self):
        return self.name


class delivery_boy(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    contact = models.CharField(max_length=15)


    def __str__(self):
        return self.name


class vendor_bank(models.Model):
    
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100)
    account_holder = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50, unique=True)
    ifsc_code = models.CharField(max_length=20)
    branch = models.CharField(max_length=100, blank=True, null=True)
    balance = models.BigIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.account_holder}"


class vendor_customers(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True)
    
    # Basic
    name = models.CharField(max_length=50)
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    balance = models.BigIntegerField(default=0)

    # Business Details
    company_name = models.CharField(max_length=100, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    aadhar_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)

    # Billing Address
    billing_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    billing_pincode = models.CharField(max_length=10, blank=True, null=True)
    billing_city = models.CharField(max_length=50, blank=True, null=True)
    billing_state = models.CharField(max_length=50, blank=True, null=True)
    billing_country = models.CharField(max_length=50, blank=True, null=True)

    # Dispatch Address
    dispatch_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    dispatch_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    dispatch_pincode = models.CharField(max_length=10, blank=True, null=True)
    dispatch_city = models.CharField(max_length=50, blank=True, null=True)
    dispatch_state = models.CharField(max_length=50, blank=True, null=True)
    dispatch_country = models.CharField(max_length=50, blank=True, null=True)

    # Transport
    transport_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name




class addon(models.Model):

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True)
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

    FOOD_TYPE_CHOICES = (
        ('veg', 'Veg'),
        ('non_veg', 'Non Veg'),
    )

    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('sa', 'Milligram'),
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
        ('page', 'Page'),
    ]



    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name='productssdsdsd', null=True, blank=True)

    product_type  = models.CharField(max_length=10, choices=TYPE_CHOICES, default='product')
    sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES, default='offline')
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES, null=True, blank=True)

    name = models.CharField(max_length=255)
    category = models.ForeignKey("masters.product_category", on_delete=models.SET_NULL, null=True, blank=True)
    sub_category = models.ForeignKey("masters.product_subcategory", related_name='sdfdsz', on_delete=models.SET_NULL, null=True, blank=True)

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
    is_on_shop = models.BooleanField(default=False)

    return_policy = models.BooleanField(default=False)
    cod = models.BooleanField(default=False)
    replacement = models.BooleanField(default=False)
    shop_exchange = models.BooleanField(default=False)
    shop_warranty = models.BooleanField(default=False)
    brand_warranty = models.BooleanField(default=False)

    # Flags
    tax_inclusive = models.BooleanField(default=False)
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

    product = models.ForeignKey(product, related_name='print_variants', on_delete=models.CASCADE, null=True, blank=True)
    paper = models.CharField(max_length=30, choices=PAPER_CHOICES, null=True, blank=True)
    color_type = models.CharField(max_length=10, choices=COLOR_CHOICES, null=True, blank=True)
    sided = models.CharField(max_length=10, choices=SIDED_CHOICES, null=True, blank=True)
    min_quantity = models.PositiveIntegerField(null=True, blank=True)
    max_quantity = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.get_color_type_display()} | {self.get_sided_display()} | {self.get_paper_display()}"
    

class CustomizePrintVariant(models.Model):

    product = models.ForeignKey(product, related_name='customize_print_variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.size()
    
    
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
    bank = models.ForeignKey(vendor_bank, on_delete=models.CASCADE, blank=True, null=True)
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
    brand_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    is_gst_registered = models.BooleanField(default=False)
    contact = models.CharField(max_length=15, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pan = models.CharField(max_length=10, blank=True, null=True)
    upi_id = models.CharField(max_length=50, blank=True, null=True)
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

    company_profile = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(vendor_customers, on_delete=models.SET_NULL, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    credit_time_days = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_wholesale_rate = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

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
    def final_amount(self):
        return round(self.total_amount - self.total_discount, 2)

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
    
class pos_wholesale(models.Model):

    INVOICE_TYPES = [
        ('invoice', 'Invoice'),
        ('proforma', 'Pro Forma Invoice'),
        ('quotation', 'Quotation'),
        ('credit_note', 'Credit Note'),
        ('delivery_challan', 'Delivery Challan'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # creator
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="wholesales")
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES, default='invoice')
    invoice_number = models.CharField(max_length=100)
    date = models.DateField(blank=True, null=True)

    # Optional Fields
    dispatch_address = models.TextField(blank=True, null=True)
    delivery_city = models.TextField(blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)

    delivery_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    packaging_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    reverse_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    eway_bill_number = models.CharField(max_length=50, blank=True, null=True)
    lr_number = models.CharField(max_length=50, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    transport_name = models.CharField(max_length=100, blank=True, null=True)
    number_of_parcels = models.PositiveIntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'invoice_number')

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = pos_wholesale.objects.filter(user=self.user).order_by('-id').first()
            if last and last.invoice_number.startswith("SVI"):
                try:
                    last_number = int(last.invoice_number.replace("SVI", ""))
                except ValueError:
                    last_number = 0
            else:
                last_number = 0
            self.invoice_number = f"SVI{last_number + 1}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.get_invoice_type_display()}" 

        # models.py
from django.db import models


class DeliverySettings(models.Model):
    instant_order_prep_time = models.PositiveIntegerField(default=30)  # in minutes
    general_delivery_days = models.PositiveIntegerField(default=2)
    delivery_charge_per_km = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    minimum_base_fare = models.DecimalField(max_digits=6, decimal_places=2, default=30.00)

class DeliveryBoy(models.Model):
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='delivery_boys/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    total_deliveries = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    spent = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    available = models.DecimalField(max_digits=8, decimal_places=2, default=0)

class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('credit', 'Credit'), ('debit', 'Debit')])
    order_id = models.CharField(max_length=50)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

class DeliveryEarnings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    orders_delivered = models.PositiveIntegerField(default=0)
    earnings = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    last_order_id = models.CharField(max_length=50, blank=True)
    last_order_date = models.DateField(null=True, blank=True)
    last_order_time = models.TimeField(null=True, blank=True)

class DeliveryMode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, unique=True)
    is_auto_assign_enabled = models.BooleanField(default=False)
    is_self_delivery_enabled = models.BooleanField(default=False)



class CashBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cash_balance')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Rs {self.balance}"


class CashTransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_account = models.ForeignKey(vendor_bank, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="pending")  # pending, approved, failed

    def __str__(self):
        return f"{self.user.username} → ₹{self.amount} to {self.bank_account.bank_name}"



class Payment(models.Model):
    TYPE_CHOICES = (
        ('gave', 'You Gave'),
        ('received', 'You Received'),
    )
    
    PARTY_CHOICES = (
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
    )

    PAYMENT_TYPE_CHOICES = (
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('cheque', 'Cheque'),
        ('emi', 'EMI'),
        ('netbanking', 'Netbanking'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    party = models.CharField(max_length=10, choices=PARTY_CHOICES)
    party_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    account = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='payment_attachments/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.party_name} - ₹{self.amount}"



class TaxSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tax_settings')
    igst = models.BooleanField(default=False)
    gst = models.BooleanField(default=False)
    hsn_sac_code = models.BooleanField(default=False)
    additional_cess = models.BooleanField(default=False)
    reverse_charge = models.BooleanField(default=False)
    city_of_supply = models.BooleanField(default=False)
    eway_bill_no = models.BooleanField(default=False)
    composite_scheme = models.BooleanField(default=False)

class InvoiceSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='invoice_settings')
    show_round_off = models.BooleanField(default=False)
    show_due_date = models.BooleanField(default=False)
    show_dispatch_address = models.BooleanField(default=False)
    show_hsn_sac_summary = models.BooleanField(default=False)




class ReminderSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Reminder toggles
    credit_bill_reminder = models.BooleanField(default=False)
    pending_invoice_reminder = models.BooleanField(default=False)
    low_stock_reminder = models.BooleanField(default=False)
    expiry_stock_reminder = models.BooleanField(default=False)

    # Reminder days
    credit_bill_days = models.PositiveIntegerField(default=30)
    pending_invoice_days = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"ReminderSettings for {self.user.username}"