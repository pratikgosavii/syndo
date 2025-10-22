from django.utils import timezone

from django.db import models

# Create your models here.


import random



from users.models import User

from django.db import models

class Address(models.Model):
    STATE_CHOICES = [
        ("Andhra Pradesh", "Andhra Pradesh"),
        ("Arunachal Pradesh", "Arunachal Pradesh"),
        ("Assam", "Assam"),
        ("Bihar", "Bihar"),
        ("Chhattisgarh", "Chhattisgarh"),
        ("Goa", "Goa"),
        ("Gujarat", "Gujarat"),
        ("Haryana", "Haryana"),
        ("Himachal Pradesh", "Himachal Pradesh"),
        ("Jharkhand", "Jharkhand"),
        ("Karnataka", "Karnataka"),
        ("Kerala", "Kerala"),
        ("Madhya Pradesh", "Madhya Pradesh"),
        ("Maharashtra", "Maharashtra"),
        ("Manipur", "Manipur"),
        ("Meghalaya", "Meghalaya"),
        ("Mizoram", "Mizoram"),
        ("Nagaland", "Nagaland"),
        ("Odisha", "Odisha"),
        ("Punjab", "Punjab"),
        ("Rajasthan", "Rajasthan"),
        ("Sikkim", "Sikkim"),
        ("Tamil Nadu", "Tamil Nadu"),
        ("Telangana", "Telangana"),
        ("Tripura", "Tripura"),
        ("Uttar Pradesh", "Uttar Pradesh"),
        ("Uttarakhand", "Uttarakhand"),
        ("West Bengal", "West Bengal"),
        ("Andaman and Nicobar Islands", "Andaman and Nicobar Islands"),
        ("Chandigarh", "Chandigarh"),
        ("Dadra and Nagar Haveli and Daman and Diu", "Dadra and Nagar Haveli and Daman and Diu"),
        ("Delhi", "Delhi"),
        ("Jammu and Kashmir", "Jammu and Kashmir"),
        ("Ladakh", "Ladakh"),
        ("Lakshadweep", "Lakshadweep"),
        ("Puducherry", "Puducherry"),
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="addresses")
    
    full_name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15)
    pincode = models.CharField(max_length=6)
    flat_building = models.CharField(max_length=255)
    area_street = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    town_city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, choices=STATE_CHOICES)  # 🔽 dropdown
    
    is_default = models.BooleanField(default=False)
    delivery_instructions = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.town_city}, {self.state}"
    
    @property
    def full_address(self):
        parts = [
            self.flat_building,
            self.area_street,
            self.landmark if self.landmark else "",
            f"{self.town_city}, {self.state} - {self.pincode}"
        ]
        return ", ".join([p for p in parts if p])  # removes blanks

    @property
    def full_address(self):
        parts = [
            self.flat_building,
            self.area_street,
            self.landmark if self.landmark else "",
            f"{self.town_city}, {self.state} - {self.pincode}"
        ]
        return ", ".join([p for p in parts if p])  # removes blanks

    
class Cart(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="carts"
    )
    product = models.ForeignKey(
        "vendor.product",  # or Product model
        on_delete=models.CASCADE,
        related_name="carts"
    )
    quantity = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')  # one product per user cart

    def __str__(self):
        return f"{self.user.username} - {self.product.name} x {self.quantity}"
    

class PrintJob(models.Model):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name="print_job")
    instructions = models.TextField(blank=True, null=True)
    total_amount = models.IntegerField(default=0)
    print_type = models.CharField(
        max_length=20,
        choices=[("single", "Single Side"), ("double", "Double Side")],
        default="single",
    )
    add_ons = models.ManyToManyField("vendor.addon", blank=True, related_name="print_jobs")

    # 🆕 New fields
    print_variant = models.ForeignKey(
        "vendor.PrintVariant", on_delete=models.SET_NULL, null=True, blank=True, related_name="print_jobs"
    )
    customize_variant = models.ForeignKey(
        "vendor.CustomizePrintVariant", on_delete=models.SET_NULL, null=True, blank=True, related_name="print_jobs"
    )

    def __str__(self):
        return f"Print Job for {self.cart.product.name}"



class PrintFile(models.Model):
    print_job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="print_jobs/files/")
    number_of_copies = models.PositiveIntegerField(default=1)
    page_count = models.PositiveIntegerField(default=0)
    page_numbers = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.file_name} ({self.number_of_copies} copies)"


class Order(models.Model):

    user = models.ForeignKey(
            "users.User",
            on_delete=models.CASCADE,
            related_name="orders", blank=True, null=True
    )

    ORDER_STATUS = [
        ('not_accepted', 'Not Accepted'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    DELIVERY_TYPES = [
        ('instant_delivery', 'Instant Delivery'),
        ('general_delivery', 'General Delivery'),
        ('self_pickup', 'Self Pickup'),
        ('on_shop_order', 'On-shop Order'),
    ]

    order_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='not_accepted')
    payment_mode = models.CharField(max_length=50, default='COD')
    is_paid = models.BooleanField(default=False)
      

    delivery_type = models.CharField(
        max_length=50,
        choices=DELIVERY_TYPES,
        default='self_pickup'
    )

    # Financials
    item_total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wallet_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cashback = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Delivery details
    address = models.ForeignKey(Address, on_delete=models.CASCADE, null=True, blank=True)
    
    delivery_boy = models.ForeignKey("vendor.DeliveryBoy", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_orders")
    created_at = models.DateTimeField(auto_now=True)

    
    

class OrderItem(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('intransit', 'In Transit'),
        ('delivered', 'Delivered'),
        
        ('returned/replaced_requested', 'returned/replaced_requested'),
        ('returned/replaced_approved', 'returned/replaced_approved'),
        ('returned/replaced_rejected', 'returned/replaced_rejected'),
        ('returned/replaced_completed', 'returned/replaced_completed'),
        ('returned/replaced_cancelled', 'returned/replaced_cancelled'),
        
        ('cancelled', 'Cancelled'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("vendor.product", on_delete=models.CASCADE, related_name="items")
    quantity = models.IntegerField(default=1)
    price = models.IntegerField()
    status = models.CharField(max_length=28, choices=STATUS_CHOICES, default='pending')

    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.product} × {self.quantity} ({self.status})"




class ReturnExchange(models.Model):
    RETURN_TYPES = [
        ('return', 'Return'),
        ('exchange', 'Exchange'),
    ]

    order_item = models.ForeignKey("OrderItem", on_delete=models.CASCADE, related_name="return_exchanges")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="return_exchanges")

    type = models.CharField(max_length=10, choices=RETURN_TYPES)
    reason = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_allowed(self):
        """
        Checks if return/exchange is allowed:
        - Product must have return_policy or replacement enabled
        - Within 7 days of delivery
        """
        product = self.order_item.product
        order_date = self.order_item.order.created_at

        within_7_days = (timezone.now().date() - order_date).days <= 7
        if not within_7_days:
            return False

        if self.type == 'return' and not product.return_policy:
            return False
        if self.type == 'exchange' and not product.replacement:
            return False

        return True

    def __str__(self):
        return f"{self.get_type_display()} - {self.order_item.product.name}"

    

class Follower(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="following")
    follower = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'follower')  # Prevent duplicate follows

    def __str__(self):
        return f"{self.follower.username} follows {self.user.username}"
    


from vendor.models import product

class Favourite(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="favourites")
    product = models.ForeignKey(product, on_delete=models.CASCADE, related_name="favourited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

class FavouriteStore(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="favourites_user")
    store = models.ForeignKey("vendor.vendor_store", on_delete=models.CASCADE, related_name="favourited_store")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "store")



        
class SupportTicket(models.Model):
    ROLE_CHOICES = [
        ("vendor", "Vendor"),
        ("customer", "Customer"),
        ("admin", "Admin"),
    ]
   
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="support_tickets")
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)  # who created ticket
    subject = models.CharField(max_length=255)
    order = models.ForeignKey(
        "customer.Order",   # replace with your actual Appointment model
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="support_tickets"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"



class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages", blank=True, null=True)
    sender = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="sent_support_messages")
    message = models.TextField()
    is_admin = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="support/attachments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg by {self.sender.username} in Ticket {self.ticket.id}"







class Review(models.Model):
    product = models.ForeignKey(product, on_delete=models.CASCADE, related_name='product_reviews')
    user = models.ForeignKey("users.user", on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()  # 1 to 5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')  # ensures 1 review per user per product
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} review on {self.product.name}"