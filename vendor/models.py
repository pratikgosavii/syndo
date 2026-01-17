

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
    start_date = models.DateTimeField()
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
    name = models.CharField(max_length=50)
    storetag = models.CharField(max_length=50, blank=True, null=True)
    banner_image = models.ImageField(upload_to='store/', blank=True, null=True)
    profile_image = models.ImageField(upload_to='store/', blank=True, null=True)
    about = models.CharField(max_length=500, blank=True, null=True)
    latitude = models.DecimalField(max_digits=50, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=50, decimal_places=6, blank=True, null=True)
    is_location = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    is_offline = models.BooleanField(default=False)
    display_as_catalog = models.BooleanField(default=False)
    private_catalog = models.BooleanField(default=False)
    is_catalog = models.BooleanField(default=False)

    # KYC details
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=20, blank=True, null=True)
    # Verification flags and timestamps
    is_pan_verified = models.BooleanField(default=False)
    pan_verified_at = models.DateTimeField(blank=True, null=True)
    is_gstin_verified = models.BooleanField(default=False)
    gstin_verified_at = models.DateTimeField(blank=True, null=True)
    is_bank_verified = models.BooleanField(default=False)
    bank_verified_at = models.DateTimeField(blank=True, null=True)
    kyc_last_error = models.CharField(max_length=255, blank=True, null=True)
    # FSSAI
    fssai_number = models.CharField(max_length=20, blank=True, null=True)
    is_fssai_verified = models.BooleanField(default=False)
    fssai_verified_at = models.DateTimeField(blank=True, null=True)
    
    # Global Supplier
    global_supplier = models.BooleanField(default=False, help_text="Mark vendor as global supplier")
    

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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='working_hours')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    
    

    def __str__(self):
        return f"{self.day.title()} - {'Open' if self.is_open else 'Closed'}"



class SpotlightProduct(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
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



class BannerCampaign(models.Model):
    REDIRECT_CHOICES = [
        ('store', 'Store'),
        ('product', 'Product'),
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name='banners')
    banner_image = models.ImageField(upload_to='campaign_banners/', help_text="Max 1MB, Ratio 1:3")
    campaign_name = models.CharField(max_length=255)
    redirect_to = models.CharField(choices=REDIRECT_CHOICES, max_length=50)
    product = models.ForeignKey("vendor.product", on_delete=models.CASCADE, null=True, blank=True)
    store = models.ForeignKey("vendor.vendor_store", on_delete=models.CASCADE, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.campaign_name
    



# -------------------------------
# Vendor Bank
# -------------------------------
class vendor_bank(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100)
    account_holder = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50, unique=True)
    ifsc_code = models.CharField(max_length=20)
    branch = models.CharField(max_length=100, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    online_order_bank = models.BooleanField(default=False, help_text="Bank account used for online order payments")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # On creation: seed running balance from opening_balance
        if self._state.adding:
            self.balance = self.opening_balance
        else:
            # On update: lock opening_balance (never editable after create)
            try:
                old = vendor_bank.objects.get(pk=self.pk)
                self.opening_balance = old.opening_balance
            except vendor_bank.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.account_holder}"


# -------------------------------
# Store Rating (by customers for stores)
# -------------------------------
# class StoreRating(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_ratings', blank=True, null=True)
#     store = models.ForeignKey('vendor_store', on_delete=models.CASCADE, related_name='ratings', blank=True, null=True)
#     rating = models.PositiveSmallIntegerField()
#     comment = models.TextField(blank=True, null=True)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-created_at']
#         unique_together = ('user', 'store')

#     def __str__(self):
#         return f"{self.store.name} rated {self.rating} by {self.user.username}"

# -------------------------------
# Vendor Customers
# -------------------------------
class vendor_customers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    # Basic
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    contact = models.CharField(max_length=15)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
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
    state = models.ForeignKey('masters.State', on_delete=models.SET_NULL, null=True, blank=True)

    transport_name = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        # On creation: seed running balance from opening_balance
        if self._state.adding:
            self.balance = self.opening_balance
        else:
            # Lock opening_balance after create
            try:
                old = vendor_customers.objects.get(pk=self.pk)
                self.opening_balance = old.opening_balance
            except vendor_customers.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# -------------------------------
# Vendor Vendors
# -------------------------------
class vendor_vendors(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    contact = models.CharField(max_length=15)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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
    state = models.ForeignKey('masters.State', on_delete=models.SET_NULL, null=True, blank=True)

    country = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        # On creation: seed running balance from opening_balance
        if self._state.adding:
            self.balance = self.opening_balance
        else:
            # Lock opening_balance after create
            try:
                old = vendor_vendors.objects.get(pk=self.pk)
                self.opening_balance = old.opening_balance
            except vendor_vendors.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# -------------------------------
# Bank Ledger
# -------------------------------
class BankLedger(models.Model):
    bank = models.ForeignKey(vendor_bank, related_name="ledger_entries", on_delete=models.CASCADE)
    TRANSACTION_TYPES = [
        ("sale", "Sale (POS)"),
        ("purchase", "Purchase"),
        ("expense", "Expense"),
        ("deposit", "Manual Deposit"),
        ("withdrawal", "Bank Withdrawal"),
        ("transfered", "Transferred"),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference_id = models.PositiveIntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.bank.name} - {self.transaction_type} - {self.amount}"


# -------------------------------
# Cash Ledger
# -------------------------------
class CashLedger(models.Model):
    user = models.ForeignKey('users.User', related_name="cash_user", on_delete=models.CASCADE)

    TRANSACTION_TYPES = [
        ("sale", "Sale (POS)"),
        ("purchase", "Purchase"),
        ("expense", "Expense"),
        ("deposit", "Cash Deposit"),
        ("withdrawal", "Cash Withdrawal"),
        ("payment", "Payment"),
        ("cash_transfer", "Cash Transfer"),
        ("adjustment", "Cash Adjustment"),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference_id = models.PositiveIntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cash | {self.transaction_type} | {self.amount}"




# -------------------------------
# Customer Ledger
# -------------------------------
class CustomerLedger(models.Model):
    customer = models.ForeignKey(vendor_customers, related_name="ledger_entries", on_delete=models.CASCADE)
    TRANSACTION_TYPES = [
        ("sale", "Sale (POS)"),
        ("payment", "Payment Received"),
        ("refund", "Refund Given"),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference_id = models.PositiveIntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bill_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total bill amount for credit sales (includes advance payment)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer} | {self.transaction_type} | {self.amount}"


# -------------------------------
# Vendor Ledger
# -------------------------------
class VendorLedger(models.Model):
    vendor = models.ForeignKey(vendor_vendors, related_name="ledger_entries", on_delete=models.CASCADE)
    TRANSACTION_TYPES = [
        ("purchase", "Purchase"),
        ("payment", "Payment Made"),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference_id = models.PositiveIntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.vendor} | {self.transaction_type} | {self.amount}"



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
    # Multiple gallery images via M2M to ProductImage
    gallery_images = models.ManyToManyField('ProductImage', blank=True, related_name='products')

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

    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="variants")
    
    product_type  = models.CharField(max_length=10, choices=TYPE_CHOICES, default='product')
    sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES, default='offline')
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES, null=True, blank=True)

    name = models.CharField(max_length=255)
    category = models.ForeignKey("masters.product_category", on_delete=models.CASCADE)
    sub_category = models.ForeignKey("masters.product_subcategory", related_name='sdfdsz', on_delete=models.CASCADE)

    # Pricing details
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)    #pos
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
   
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, null=True, blank=True)
    hsn = models.CharField(max_length=50, null=True, blank=True)
    gst = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Stock;
    # Allow very large numeric values (more than 18 digits)
    assign_barcode = models.DecimalField(max_digits=30, decimal_places=0, null=True, blank=True)
    track_serial_numbers = models.BooleanField(default=False)
    
    track_stock = models.BooleanField(default=False)
    opening_stock = models.IntegerField(null=True, blank=True)
    low_stock_alert = models.BooleanField(default=False)
    low_stock_quantity = models.IntegerField(null=True, blank=True)
    stock = models.IntegerField(null=True, blank=True)

    # Optional
    brand_name = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.ForeignKey("masters.size", on_delete=models.CASCADE, null=True, blank=True)
    batch_number = models.CharField(max_length=100, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    # Multiple gallery images via M2M
    gallery_images = models.ManyToManyField('ProductImage', blank=True, related_name='products_gallery_images')

    # Delivery & Policies
    is_customize = models.BooleanField(default=False)
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

    is_food = models.BooleanField(default=False)

    # Flags
    tax_inclusive = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)

    stock_cached = models.IntegerField(default=0, null=True, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.gst is not None:
            half_gst = round(self.gst / 2, 2)
            self.sgst_rate = half_gst
            self.cgst_rate = half_gst
        
        # Set stock_cached to opening_stock when product is first created
        if self.pk is None and self.opening_stock is not None:
            self.stock_cached = self.opening_stock
        
        super().save(*args, **kwargs)


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


class serial_imei_no(models.Model):
    """
    Stores serial/IMEI numbers for a product (multiple per product).
    """
    product = models.ForeignKey(product, on_delete=models.CASCADE, related_name='serial_imei_list')
    value = models.CharField(max_length=64, db_index=True)
    is_sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.value}"


class product_addon(models.Model):
  
    product = models.ForeignKey('product', on_delete=models.CASCADE, null=True, blank=True, related_name="product_addon")
    addon = models.ForeignKey('addon', on_delete=models.CASCADE, null=True, blank=True, related_name = "product_addon_addon")
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
    shop_orders = models.BooleanField(default=False)

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
    




import uuid
from django.utils.crypto import get_random_string

class Purchase(models.Model):
    
  
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('cash', 'Cash'),
        ('credit', 'Credit'),
    ]

    ADVANCE_MODE_CHOICES = [
        ('bank', 'Bank'),
        ('cash', 'Cash'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    purchase_code = models.CharField(max_length=100, blank=True, null=True)

    purchase_date = models.DateField()
    vendor = models.ForeignKey('vendor_vendors', on_delete=models.CASCADE)

    supplier_invoice_date = models.DateField(blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)

    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    advance_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True) 
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    advance_mode = models.CharField(max_length=10, choices=ADVANCE_MODE_CHOICES, blank=True, null=True)
    advance_bank = models.ForeignKey(vendor_bank, on_delete=models.CASCADE, blank=True, null=True)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)

    due_date = models.DateField(blank=True, null=True)

    dispatch_address = models.CharField(max_length=255, blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)

    delivery_shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    packaging_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Newly added transport-related fields
    eway_bill_no = models.CharField(max_length=50, blank=True, null=True)
    lr_no = models.CharField(max_length=50, blank=True, null=True)
    vehicle_no = models.CharField(max_length=50, blank=True, null=True)
    transport_name = models.CharField(max_length=100, blank=True, null=True)
    no_of_parcels = models.PositiveIntegerField(blank=True, null=True)
    
    # Total amount calculated from purchase items
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)

    # GST fields (similar to Sale)
    total_taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True, help_text="Total taxable value (sum of item amounts)")
    total_gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True, help_text="Total GST amount (sum of item tax_amount)")

    def save(self, *args, **kwargs):
        # Generate purchase_code if it's empty or doesn't match the expected format (YY-YY/MM/MONTH/PUR-XXXX)
        # Check if code matches the expected pattern: YY-YY/MM/MONTH/PUR-XXXX
        import re
        pattern = r'^\d{2}-\d{2}/\d{2}/[A-Z]{3}/PUR-\d{4}$'
        if not self.purchase_code or not re.match(pattern, self.purchase_code):
            from django.utils import timezone
            
            # Ensure purchase_date is set before generating code (use today's date if not set)
            if not self.purchase_date:
                self.purchase_date = timezone.now().date()
            
            # Ensure user is set (required for code generation)
            if not self.user:
                # If user is not set, we can't generate a proper code
                # This should not happen in normal flow, but log a warning
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Purchase.save(): user is None, cannot generate purchase_code properly")
                # Don't generate code if user is None - let it be handled by the caller
                super().save(*args, **kwargs)
                return
            
            from .utils import generate_serial_number
            # Use a retry mechanism to handle race conditions
            max_retries = 5
            new_code = None
            for attempt in range(max_retries):
                try:
                    new_code = generate_serial_number(
                        prefix='PUR',
                        model_class=Purchase,
                        date=self.purchase_date,
                        user=self.user
                    )
                    # Check if this code already exists (race condition check)
                    existing = Purchase.objects.filter(purchase_code=new_code)
                    if self.pk:  # If updating, exclude current instance
                        existing = existing.exclude(pk=self.pk)
                    if not existing.exists():
                        self.purchase_code = new_code
                        break
                    # If code exists, wait a tiny bit and retry (only if not last attempt)
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(0.1)
                except Exception as e:
                    # Log the error for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Purchase.save(): Error generating purchase_code (attempt {attempt + 1}/{max_retries}): {e}")
                    # If generation fails, use a fallback on last attempt
                    if attempt == max_retries - 1:
                        timestamp = int(timezone.now().timestamp())
                        new_code = f"PUR-{timestamp}-{self.id or 'NEW'}"
                        self.purchase_code = new_code
            
            # Ensure purchase_code is set (fallback if all attempts failed)
            if not self.purchase_code and new_code:
                self.purchase_code = new_code
            elif not self.purchase_code:
                # Last resort fallback
                timestamp = int(timezone.now().timestamp())
                self.purchase_code = f"PUR-FALLBACK-{timestamp}"
        
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculate and update total_amount from purchase items + GST + other charges (like Sale)"""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Calculate GST totals from PurchaseItems (similar to Sale)
        total_taxable_amount = Decimal(0)
        total_gst_amount = Decimal(0)
        
        for item in self.items.all():
            # Sum taxable amounts (amount field from PurchaseItem)
            total_taxable_amount += Decimal(item.amount or 0)
            # Sum GST amounts (tax_amount field from PurchaseItem)
            total_gst_amount += Decimal(item.tax_amount or 0)
        
        # Apply discount if any
        discount_amount = Decimal(0)
        if self.discount_percentage:
            discount_amount = total_taxable_amount * Decimal(self.discount_percentage) / Decimal(100)
        elif self.discount_amount:
            discount_amount = Decimal(self.discount_amount)
        
        base_total_amount = total_taxable_amount - discount_amount
        
        # Add other charges
        delivery_charges = Decimal(self.delivery_shipping_charges or 0)
        packaging_charges = Decimal(self.packaging_charges or 0)
        
        # Final total includes: items (after discount) + GST + delivery + packaging (like Sale)
        new_total = base_total_amount + total_gst_amount + delivery_charges + packaging_charges
        
        # Update instance fields directly (like Sale._recalculate_totals does)
        # This ensures instance is updated in memory, then caller can save() to trigger signal
        self.total_taxable_amount = total_taxable_amount
        self.total_gst_amount = total_gst_amount
        self.total_amount = new_total
        
        # Don't save here - let the caller save() to trigger signal with updated values
        # This matches how Sale._recalculate_totals() works - it sets fields then saves

    def __str__(self):
        return self.purchase_code or f"Purchase #{self.id}"

    
class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    # GST fields (similar to SaleItem)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Taxable value (quantity * price)")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="GST amount")
    total_with_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Final total including tax")

    def save(self, *args, **kwargs):
        # Calculate GST like SaleItem
        from decimal import Decimal, ROUND_HALF_UP
        
        def _to_decimal(value):
            """Safely convert value to Decimal."""
            if value is None:
                return Decimal("0")
            if isinstance(value, Decimal):
                return value
            return Decimal(str(value))
        
        quantity = _to_decimal(self.quantity)
        price = _to_decimal(self.price)
        gst_rate = _to_decimal(getattr(self.product, "gst", 0))

        # Calculations (kept in Decimal)
        self.amount = (quantity * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.tax_amount = (self.amount * gst_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.total_with_tax = (self.amount + self.tax_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # Keep total for backward compatibility (same as total_with_tax)
        self.total = self.total_with_tax
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purchase.id} ({self.product.name})"

            

class CompanyProfile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True, related_name="user_company_profile")
    company_name = models.CharField(max_length=255)
    brand_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    is_gst_registered = models.BooleanField(default=False)
    contact = models.CharField(max_length=15, blank=True, null=True)
    # Billing address (existing + missing fields)
    billing_address = models.TextField(blank=True, null=True)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.ForeignKey('masters.State', on_delete=models.SET_NULL, null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Shipping address
    shipping_same_as_billing = models.BooleanField(default=True)
    shipping_address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    shipping_address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    shipping_pincode = models.CharField(max_length=10, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_state = models.ForeignKey('masters.State', on_delete=models.SET_NULL, null=True, blank=True, related_name='shipping_company_profiles')
    shipping_country = models.CharField(max_length=100, blank=True, null=True)

    pan = models.CharField(max_length=10, blank=True, null=True)
    upi_id = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='company_profiles/', blank=True, null=True)
    signature  = models.ImageField(upload_to='company_profiles/', blank=True, null=True)
    payment_qr  = models.ImageField(upload_to='company_profiles/', blank=True, null=True)

    is_default = models.BooleanField(default=False)

    # uEngage Flash: per-store identifier for delivery APIs
    uengage_store_id = models.CharField(max_length=50, blank=True, null=True)


    def __str__(self):
        return self.company_name


class DeliveryDiscount(models.Model):
    """Delivery discount settings per vendor"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True, related_name="delivery_discount")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Discount percentage for delivery")
    min_cart_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum cart value to apply discount")
    is_enabled = models.BooleanField(default=False, help_text="Enable/disable delivery discount")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery Discount - {self.user.username if self.user else 'No User'} ({self.discount_percent}%)"


class Expense(models.Model):
    
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('cash', 'Cash'),
    ]

    bank = models.ForeignKey(vendor_bank, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    category = models.ForeignKey("masters.expense_category", on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_date = models.DateField(null=True, blank=True)
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
        ('cheque', 'Cheque'),
        ('cash', 'Cash'),
        ('credit', 'Credit'),
    ]

    ADVANCE_PAYMENT_METHOD_CHOICES = [
        ('bank', 'Bank'),
        ('cash', 'Cash'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    company_profile = models.ForeignKey('CompanyProfile', on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey('vendor_customers', on_delete=models.SET_NULL, null=True, blank=True)
    
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    advance_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_payment_method = models.CharField(max_length=10, choices=ADVANCE_PAYMENT_METHOD_CHOICES, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Summary fields
    total_items = models.PositiveIntegerField(default=0, null=True, blank=True)
    total_amount_before_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    advance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    advance_bank = models.ForeignKey(vendor_bank, on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    
    # GST fields
    total_taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True, help_text="Total taxable value (sum of item amounts)")
    total_gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True, help_text="Total GST amount (sum of item tax_amount)")

    credit_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    is_wholesale_rate = models.BooleanField(default=False)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number and not self.is_wholesale_rate:
            # Only generate POS serial number for non-wholesale sales
            from .utils import generate_serial_number
            from django.utils import timezone
            self.invoice_number = generate_serial_number(
                prefix='POS',
                model_class=Sale,
                date=timezone.now().date(),
                user=self.user,
                filter_kwargs={'is_wholesale_rate': False}
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale #{self.id}"

from decimal import Decimal, ROUND_HALF_UP

def _to_decimal(value):
    """
    Safely convert value to Decimal.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))  # str() avoids float artifacts


class SaleItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(product, on_delete=models.CASCADE)  # ✅ corrected `product` -> `Product`
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of sale

    # DB fields
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)           # taxable value
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)       # GST amount
    total_with_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # final total incl tax

    def save(self, *args, **kwargs):
        # Convert inputs to Decimal safely
        quantity = _to_decimal(self.quantity)
        price = _to_decimal(self.price)
        gst_rate = _to_decimal(getattr(self.product, "gst", 0))

        # Calculations (kept in Decimal)
        self.amount = (quantity * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.tax_amount = (self.amount * gst_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.total_with_tax = (self.amount + self.tax_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

   
    
class pos_wholesale(models.Model):

    INVOICE_TYPES = [
        ('invoice', 'Sales Invoice'),
        ('sales_return', 'Sales Return'),
        ('sales_order', 'Sales Order'),
        ('proforma', 'Pro Forma Invoice'),
        ('quotation', 'Quotation'),
        ('delivery_challan', 'Delivery Challan'),
        ('credit_note', 'Credit Note'),
        ('debit_note', 'Debit Note'),
        ('e_invoice', 'E-Invoice (IRN)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # creator
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="wholesales")
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES, default='invoice')
    invoice_number = models.CharField(max_length=100)
    date = models.DateField(blank=True, null=True)

    # Optional Fields
    dispatch_address = models.TextField(blank=True, null=True)
    delivery_city = models.TextField(blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)

    delivery_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    packaging_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    reverse_charges = models.BooleanField(default=False)

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
            from .utils import generate_serial_number
            
            # Map invoice types to prefixes
            prefix_map = {
                'invoice': 'SAL',
                'sales_return': 'SRN',
                'sales_order': 'SOR',
                'proforma': 'PFI',
                'quotation': 'QTN',
                'delivery_challan': 'DC',
                'credit_note': 'CRN',
                'debit_note': 'DBN',
                'e_invoice': 'EIN',
            }
            
            prefix = prefix_map.get(self.invoice_type, 'SAL')
            date = self.date if self.date else None
            
            self.invoice_number = generate_serial_number(
                prefix=prefix,
                model_class=pos_wholesale,
                date=date,
                user=self.user,
                filter_kwargs={'invoice_type': self.invoice_type}
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.get_invoice_type_display()}" 


        # models.py
from django.db import models


class DeliverySettings(models.Model):
    instant_order_prep_time = models.PositiveIntegerField(default=30)  # in minutes
    general_delivery_days = models.PositiveIntegerField(default=2)
    # General delivery: flat charge
    general_delivery_charge = models.DecimalField(max_digits=7, decimal_places=2, default=50.00)
    # Instant delivery pricing: per-km after base fare
    instant_per_km_charge = models.DecimalField(max_digits=7, decimal_places=2, default=10.00)
    instant_min_base_fare = models.DecimalField(max_digits=7, decimal_places=2, default=30.00)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)


class DeliveryBoy(models.Model):
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='delivery_boys/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    total_deliveries = models.PositiveIntegerField(default=0)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)

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
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, unique=True, related_name="delivery_mode")
    is_auto_assign_enabled = models.BooleanField(default=False)
    is_self_delivery_enabled = models.BooleanField(default=True)



class CashBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cash_balance')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Rs {self.balance}"


class CashTransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_account = models.ForeignKey(vendor_bank, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> Rs {self.amount}"


class ProductImage(models.Model):
    image = models.ImageField(upload_to='product_gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.name if self.image else "ProductImage"


class BankTransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_bank = models.ForeignKey(
        vendor_bank, related_name="outgoing_transfers", on_delete=models.CASCADE
    )
    to_bank = models.ForeignKey(
        vendor_bank, related_name="incoming_transfers", on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transfer {self.amount} from {self.from_bank} to {self.to_bank}"

        

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
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('bank', 'Bank'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    vendor = models.ForeignKey("vendor_vendors", on_delete=models.CASCADE, blank=True, null=True)
    customer = models.ForeignKey("vendor_customers", on_delete=models.CASCADE, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    bank = models.ForeignKey(vendor_bank, on_delete=models.CASCADE, blank=True, null=True)
    payment_number = models.CharField(max_length=100, blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='payment_attachments/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.payment_number:
            from .utils import generate_serial_number
            # Payment Received = REC, Payment Made (You Gave) = PAY
            prefix = 'REC' if self.type == 'received' else 'PAY'
            self.payment_number = generate_serial_number(
                prefix=prefix,
                model_class=Payment,
                date=self.payment_date,
                user=self.user,
                filter_kwargs={'type': self.type}
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_payment_type_display()} - Rs {self.amount}"



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


class BarcodeSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="barcode_settings")

    show_package_date = models.BooleanField(default=False)
    mrp_label = models.BooleanField(default=False)
    show_discount = models.BooleanField(default=False)
    show_price_with_text = models.BooleanField(default=False)

    BARCODE_SIZE_CHOICES = [
        ("50x100", "50MM * 100MM"),
    ]
    barcode_size = models.CharField(max_length=10, choices=BARCODE_SIZE_CHOICES, default="25x50")

    show_note = models.BooleanField(default=False)
    note_label = models.CharField(max_length=20, blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Barcode Settings for {self.user.username}"


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
    expiry_stock_days = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"ReminderSettings for {self.user.username}"


class SMSSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sms_setting')
    
    # SMS Credits
    available_credits = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    used_credits = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Message Enablement Toggles
    enable_purchase_message = models.BooleanField(default=False)
    enable_quote_message = models.BooleanField(default=False)
    enable_credit_reminder_message = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SMS Setting"
        verbose_name_plural = "SMS Settings"
    
    def __str__(self):
        return f"SMS Settings for {self.user.username}"


class Reminder(models.Model):
    """
    Stores reminders generated based on ReminderSetting for each user/vendor.
    """
    REMINDER_TYPE_CHOICES = [
        ('credit_bill', 'Credit Bill'),
        ('pending_invoice', 'Pending Invoice'),
        ('low_stock', 'Low Stock'),
        ('expiry_stock', 'Expiry Stock'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Reference fields - can be Purchase, Sale, or Product
    purchase = models.ForeignKey('Purchase', on_delete=models.CASCADE, null=True, blank=True)
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('product', on_delete=models.CASCADE, null=True, blank=True)
    
    # Additional info
    due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'reminder_type', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_reminder_type_display()} - {self.title}"


class NotificationCampaign(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("active", "Active"),
        ("ended", "Ended"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign_name = models.CharField(max_length=255)
    redirect_to = models.CharField(max_length=50, choices=[("store", "Store"), ("product", "Product"), ("custom", "Custom")])
    description = models.CharField(max_length=90)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    banner = models.ImageField(upload_to='notifications/banners/', null=True, blank=True)
    # Foreign keys for redirect targets
    product = models.ForeignKey('product', on_delete=models.SET_NULL, null=True, blank=True, related_name='notification_campaigns')
    store = models.ForeignKey('vendor_store', on_delete=models.SET_NULL, null=True, blank=True, related_name='notification_campaigns')

    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag - campaigns marked as deleted still count toward monthly limit")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campaign_name} ({self.status})"
    


    

class StockTransaction(models.Model):
    TRANSACTION_TYPE = [
        ('purchase', 'Purchase'),
        ('return', 'Return'),
        ('sale', 'Sale'),
    ]

    product = models.ForeignKey("vendor.product", on_delete=models.CASCADE, related_name="stock_transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE)
    quantity = models.IntegerField()  # positive or negative
    reference_id = models.CharField(max_length=50, null=True, blank=True)  # purchase_id / order_id
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']







class VendorCoverage(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='coverages')
    pincode = models.ForeignKey('masters.Pincode', on_delete=models.CASCADE, related_name='vendors')

    class Meta:
        unique_together = ('user', 'pincode')  # prevent duplicate entries

    def __str__(self):
        return f"{self.user} covers {self.pincode.code} ({self.pincode.city})"
    

# models.py
from django.db import models


class OfferMedia(models.Model):
    """Multiple media files for Offer"""
    offer = models.ForeignKey('Offer', on_delete=models.CASCADE, related_name='media_files')
    media = models.ImageField(upload_to="offers/media/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Media for {self.offer.heading}"


class Offer(models.Model):
   

    request = models.ForeignKey(
        'customer.ProductRequest',
        on_delete=models.CASCADE,
        related_name="offers"
    )
    seller = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name="offers"
    )
    product = models.CharField(max_length=50, blank=True, null=True)
    heading = models.CharField(max_length=255)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_till = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Offer automatically expires after 7 days
        if not self.valid_till:
            from datetime import timedelta, datetime
            self.valid_till = datetime.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.heading} - {self.seller.username}"


# -------------------------------
# Online Order Ledger (per vendor)
# -------------------------------
class OnlineOrderLedger(models.Model):
    STATUS_CHOICES = [
        ("recorded", "Recorded"),
        ("returned", "Returned"),
        ("replaced", "Replaced"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="online_order_ledgers")  # vendor/user who owns product
    order_item = models.ForeignKey("customer.OrderItem", on_delete=models.CASCADE, related_name="online_order_ledgers")
    product = models.ForeignKey("vendor.product", on_delete=models.CASCADE, related_name="online_order_ledgers")

    order_id = models.IntegerField(blank=True, null=True)
    quantity = models.IntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="recorded")
    note = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OrderItem #{self.order_item_id} | {self.product.name} | {self.status}"


# -------------------------------
# Expense Ledger (per vendor)
# -------------------------------
class ExpenseLedger(models.Model):
    """Dedicated ledger for expenses with category tracking"""
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('cash', 'Cash'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expense_ledgers")
    expense = models.ForeignKey('Expense', on_delete=models.CASCADE, related_name="ledger_entries")
    category = models.ForeignKey("masters.expense_category", on_delete=models.CASCADE, related_name="expense_ledgers")
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    bank = models.ForeignKey(vendor_bank, on_delete=models.SET_NULL, blank=True, null=True, related_name="expense_ledgers")
    
    expense_date = models.DateField()
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['expense_date']),
        ]

    def __str__(self):
        return f"Expense #{self.expense.id} | {self.category} | {self.amount}"


class StoreVisit(models.Model):
    """Track store visits by customers"""
    store = models.ForeignKey(vendor_store, on_delete=models.CASCADE, related_name='visits')
    visitor = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='store_visits')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', '-created_at']),
            models.Index(fields=['visitor', '-created_at']),
        ]

    def __str__(self):
        visitor_name = self.visitor.username if self.visitor else 'Anonymous'
        return f"Visit to {self.store.name} by {visitor_name} at {self.created_at}"


# -------------------------------
# Order Notification Message (per vendor)
# -------------------------------
class OrderNotificationMessage(models.Model):
    """Order notification message template per vendor"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="order_notification_message")
    message = models.TextField(help_text="Notification message to send when a new order is received")
    is_active = models.BooleanField(default=True, help_text="Enable/disable order notifications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order Notification Message"
        verbose_name_plural = "Order Notification Messages"

    def __str__(self):
        return f"Order notification for {self.user.username}"