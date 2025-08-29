from rest_framework import serializers
from .models import *




class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity']

    


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)  # items cannot be updated

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ["id", "created_at", "items"]

    def create(self, validated_data):
        items_data = self.context['request'].data.get('items', [])
        order = Order.objects.create(**validated_data)

        order_items = [
            OrderItem(order=order, **item)
            for item in items_data
        ]
        OrderItem.objects.bulk_create(order_items)

        return order

    def update(self, instance, validated_data):
        # allow updating only these fields
        allowed_fields = ["status", "delivery_boy", "is_paid"]
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        instance.save()
        return instance
