from rest_framework import serializers
from .models import *



from vendor.serializers import product_serializer

from django.utils import timezone
import datetime


class OrderItemSerializer(serializers.ModelSerializer):
    product_details = product_serializer(source="product", read_only=True)
    is_return_eligible = serializers.SerializerMethodField()
    is_exchange_eligible = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 
            'product', 
            'quantity', 
            'product_details',
            'is_return_eligible',
            'is_exchange_eligible',
            'status'
        ]

        
    def _is_allowed_check(self, obj, return_type):
        """
        Common check:
        - Delivered
        - Product allows return/replacement
        - Within 7 days
        - No pending/approved ReturnExchange already exists
        """
        if obj.status != 'delivered':
            return False

        product = obj.product
        order_date = obj.order.created_at
        if isinstance(order_date, datetime.date) and not isinstance(order_date, datetime.datetime):
            order_date = datetime.datetime.combine(order_date, datetime.time.min, tzinfo=timezone.get_current_timezone())

        within_7_days = (timezone.now() - order_date).days <= 7
        if not within_7_days:
            return False

        if return_type == 'return' and not getattr(product, 'return_policy', False):
            return False
        if return_type == 'exchange' and not getattr(product, 'replacement', False):
            return False

        # Check if a pending/approved ReturnExchange exists
        existing = obj.return_exchanges.exclude(status__in=['rejected', 'cancled_by_user', 'completed'])
        if existing.exists():
            return False

        return True

    def get_is_return_eligible(self, obj):
        return self._is_allowed_check(obj, 'return')

    def get_is_exchange_eligible(self, obj):
        return self._is_allowed_check(obj, 'exchange')

    
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]



from vendor.models import product
import random, string
from django.db.models import Max


from decimal import Decimal
from users.serializer import UserProfileSerializer

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    store_details = serializers.SerializerMethodField()
    user_details = UserProfileSerializer(source = 'user', read_only=True)
    address_details = AddressSerializer(source="address", read_only = True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["id", "created_at", "items", "item_total", "total_amount", "order_id", 'user_details', 'address_details', 'store_details']
    
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

                # ✅ CLEAR CART AFTER SUCCESSFUL ORDER CREATION
        Cart.objects.filter(user=request.user).delete()


        return order

    def update(self, instance, validated_data):
        allowed_fields = ["status", "delivery_boy", "is_paid"]
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        instance.save()
        return instance

    def get_store_details(self, obj):
        from vendor.serializers import VendorStoreSerializer
        first_item = obj.items.first()  # ✅ correct — use obj, never self.instance

        if first_item:
            store = first_item.product.user.vendor_store.first()  # reverse FK returns queryset → use first()
            return VendorStoreSerializer(store).data

        return None




class ReturnExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnExchange
        fields = ['id', 'order_item', 'type', 'reason', 'status', 'created_at']

    def validate(self, data):
        user = self.context['request'].user
        order_item = data['order_item']
        req_type = data['type']

        instance = ReturnExchange(
            order_item=order_item,
            user=user,
            type=req_type
        )
        if not instance.is_allowed():
            raise serializers.ValidationError("Return/Exchange not allowed. Product not eligible or 7-day window expired.")
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user

        instance = super().create(validated_data)

        # ✅ Update OrderItem status to 'returned'
        order_item = instance.order_item
        order_item.status = 'returned requested'
        order_item.save(update_fields=['status'])

        return instance


class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = ['user', 'follower', 'created_at']







# ---------- Print File ----------
class PrintFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintFile
        fields = ["id", "file", "number_of_copies", "page_count", "page_numbers"]


# ---------- Print Job ----------
class PrintJobSerializer(serializers.ModelSerializer):

    from vendor.models import addon
    files = PrintFileSerializer(many=True)
    add_ons = serializers.PrimaryKeyRelatedField(queryset=addon.objects.all(), many=True)

    class Meta:
        model = PrintJob
        fields = ["instructions", "print_type", "add_ons", "files", "total_amount"]

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        add_ons = validated_data.pop("add_ons", [])
        print_job = PrintJob.objects.create(**validated_data)
        print_job.add_ons.set(add_ons)
        for file_data in files_data:
            PrintFile.objects.create(print_job=print_job, **file_data)
        return print_job



# ---------- Cart ----------
class CartSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=product.objects.all())
    product_details = product_serializer(source="product", read_only=True)
    print_job = PrintJobSerializer(required=False)

    class Meta:
        model = Cart
        fields = ["id", "product", "quantity", "product_details", "print_job"]

    def create(self, validated_data):
        user = self.context["request"].user
        product_instance = validated_data["product"]
        quantity = validated_data.get("quantity", 1)
        print_job_data = validated_data.pop("print_job", None)

        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product_instance,
            defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # Handle print job if it's a print product
        if product_instance.type == "print" and print_job_data:
            if hasattr(cart_item, "print_job"):
                cart_item.print_job.delete()  # replace old job
            PrintJobSerializer().create({**print_job_data, "cart": cart_item})

        return cart_item



class TicketMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TicketMessage
        fields = "__all__"
        read_only_fields = ["id", "sender", "created_at"]


class SupportTicketSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ["id", "is_admin", "user", "status", "created_at", "updated_at"]





class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'rating', 'comment', 'created_at', 'updated_at']


from vendor.models import vendor_store

class VendorStoreLiteSerializer(serializers.ModelSerializer):
    following = serializers.SerializerMethodField()

    class Meta:
        model = vendor_store
        fields = [
            "id", "name", "banner_image", "profile_image", "about",'user',
            "is_active", "is_online", "following"
        ]

    def get_following(self, obj):
        user = self.context["request"].user
        # ✅ just check if this vendor has this user as follower
        return Follower.objects.filter(user=obj.user, follower=user).exists()
