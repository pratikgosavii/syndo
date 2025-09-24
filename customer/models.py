from django.db import models

# Create your models here.


import random


class Order(models.Model):


    ORDER_STATUS = [
        ('not_accepted', 'Not Accepted'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    order_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='not_accepted')
    payment_mode = models.CharField(max_length=50, default='COD')
    is_paid = models.BooleanField(default=False)
    delivery_type = models.CharField(max_length=50, default='Self Pickup')

    # Financials
    item_total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wallet_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cashback = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Delivery details
    customer_name = models.CharField(max_length=255)
    customer_mobile = models.CharField(max_length=15)
    customer_address = models.TextField()
    
    delivery_boy = models.ForeignKey("vendor.DeliveryBoy", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_orders")
    created_at = models.DateField(auto_now=True)

    
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("vendor.product", on_delete=models.CASCADE, related_name="items")
    quantity = models.IntegerField(default=1)
    price = models.IntegerField()
    


    def total_price(self):
        return self.quantity * self.mrp


from users.models import User


class Follower(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'follower')  # Prevent duplicate follows

    def __str__(self):
        return f"{self.follower.username} follows {self.user.username}"
    


    
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