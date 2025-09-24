from rest_framework import serializers
from .models import *




class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity']

    

from vendor.models import product
import random, string
from django.db.models import Max


from decimal import Decimal


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["id", "created_at", "items", "item_total", "total_amount", "order_id"]
    
    def generate_order_id(self):
        """Generate sequential order_id like SVIND0001, SVIND0002..."""
        last_order = Order.objects.aggregate(max_id=Max("id"))["max_id"]
        next_number = (last_order or 0) + 1
        return f"SVIND{next_number:05d}"  # 5 digits padded with zeros
            
    def create(self, validated_data):
        request = self.context.get("request")
        items_data = request.data.get("items", [])

        # calculate totals
        item_total = Decimal("0.00")
        order_items = []

        for item in items_data:
            product_id = item.get("product")
            quantity = int(item.get("quantity", 1))

            # fetch product
            try:
                product1 = product.objects.get(id=product_id)
            except product.DoesNotExist:
                raise serializers.ValidationError(
                    {"items": [f"Product with id {product_id} does not exist."]}
                )

            unit_price = Decimal(str(product1.sales_price))
            line_total = unit_price * quantity
            item_total += line_total

            order_items.append(
                OrderItem(
                    product=product1,
                    quantity=quantity,
                    price=unit_price,
                )
            )

        # generate order_id
        order_id = self.generate_order_id()

        # convert values from validated_data to Decimal safely
        shipping_fee = Decimal(str(validated_data.get("shipping_fee", 0)))
        wallet_amount = Decimal(str(validated_data.get("wallet_amount", 0)))
        cashback = Decimal(str(validated_data.get("cashback", 0)))
        coupon = Decimal(str(validated_data.get("coupon", 0)))

        # calculate final total
        total_amount = item_total + shipping_fee - wallet_amount - cashback - coupon

        # set calculated totals in order
        order = Order.objects.create(
            **validated_data,
            order_id=order_id,
            item_total=item_total,
            total_amount=total_amount,
        )

        # bulk create items with linked order
        for oi in order_items:
            oi.order = order
        OrderItem.objects.bulk_create(order_items)

        return order

    def update(self, instance, validated_data):
        allowed_fields = ["status", "delivery_boy", "is_paid"]
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        instance.save()
        return instance



class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = ['user', 'follower', 'created_at']



class CartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "product", "product_name", "quantity", "updated_at"]
        read_only_fields = ["user", "updated_at"]
