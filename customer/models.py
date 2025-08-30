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
