from typing import Any
import logging
from rest_framework import serializers
from .models import *

logger = logging.getLogger(__name__)



from vendor.serializers import product_serializer

from django.utils import timezone
import datetime
from django.db import transaction

class OrderPrintFileSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderPrintFile
        fields = ["id", "file", "instructions", "number_of_copies", "page_count", "page_numbers"]
    
    def get_file(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class OrderPrintJobSerializer(serializers.ModelSerializer):
    files = OrderPrintFileSerializer(many=True, read_only=True)
    add_ons = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = OrderPrintJob
        fields = ["total_amount", "print_type", "print_variant", "customize_variant", "add_ons", "files"]
    
    def to_representation(self, instance):
        """Override to pass context to nested OrderPrintFileSerializer"""
        representation = super().to_representation(instance)
        # Get files with proper context
        if hasattr(instance, 'files'):
            files_serializer = OrderPrintFileSerializer(
                instance.files.all(), 
                many=True, 
                context=self.context
            )
            representation['files'] = files_serializer.data
        return representation


class ReturnExchangeEmbedSerializer(serializers.ModelSerializer):
    """Read-only serializer for embedding return/exchange in order item (vendor/orders API, etc.)."""
    image = serializers.SerializerMethodField()

    class Meta:
        model = ReturnExchange
        fields = ['id', 'type', 'reason', 'image', 'created_at', 'updated_at']
        read_only_fields = fields

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class OrderItemSerializer(serializers.ModelSerializer):
    product_details = product_serializer(source="product", read_only=True)
    is_return_eligible = serializers.SerializerMethodField()
    is_exchange_eligible = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()  # ✅ NEW FIELD
    # Include print job details if any (read-only)
    print_job = OrderPrintJobSerializer(read_only=True)
    # Active return/exchange for this order item (single object: latest one) - for vendor/orders API
    return_exchange = serializers.SerializerMethodField()
    class Meta:
        model = OrderItem
        fields = [
            'id', 
            'product', 
            'quantity', 
            'product_details',
            'print_job',
            'is_return_eligible',
            'is_exchange_eligible',
            'status',
            'tracking_link',
            'delivery_date',
            'is_reviewed',  # ✅ add here also
            'return_exchange',
        ]

    def get_return_exchange(self, obj):
        """Return the active (latest) return/exchange request for this order item, or None."""
        active = getattr(obj, 'return_exchanges', None)
        if active is None:
            return None
        if hasattr(active, 'all'):
            all_re = list(active.all())
        else:
            all_re = list(ReturnExchange.objects.filter(order_item=obj).order_by('-created_at'))
        if not all_re:
            return None
        latest = max(all_re, key=lambda r: r.created_at) if len(all_re) > 1 else all_re[0]
        return ReturnExchangeEmbedSerializer(latest, context=self.context).data
    
    def to_representation(self, instance):
        """Override to pass context to nested OrderPrintJobSerializer"""
        representation = super().to_representation(instance)
        # Get print_job with proper context
        if hasattr(instance, 'print_job') and instance.print_job:
            print_job_serializer = OrderPrintJobSerializer(
                instance.print_job,
                context=self.context
            )
            representation['print_job'] = print_job_serializer.data
        return representation

        
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
        blocked_status = [
            'returned/replaced_rejected', 
            'returned/replaced_completed', 
            'cancelled'
        ]
        
        if obj.status not in blocked_status:
            return True  # eligible

        return True

    def get_is_return_eligible(self, obj):
        return self._is_allowed_check(obj, 'return')

    def get_is_exchange_eligible(self, obj):
        return self._is_allowed_check(obj, 'exchange')

    def get_is_reviewed(self, obj):
        user = self.context['request'].user  # logged-in user
        return Review.objects.filter(order_item=obj, user=user).exists()
    
    
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]



from vendor.models import product, vendor_store, DeliverySettings
import random, string
from django.db.models import Max


from decimal import Decimal
from users.serializer import UserProfileSerializer


def calculate_coupon_discount_amount(coupon_id, item_total, user=None):
    """
    Calculate coupon discount amount based on coupon settings.
    Coupon is calculated on item_total only (items only, no tax/shipping).
    Same calculation logic used in cart and order creation.
    
    Args:
        coupon_id: The coupon ID to apply
        item_total: Total value of items in cart/order (Decimal)
        user: The customer user applying the coupon (for validation)
    
    Returns:
        tuple: (discount_amount: Decimal, coupon_instance: coupon or None, error_message: str or None)
        Returns (0.00, None, None) if no discount applies or coupon is invalid
    """
    from decimal import Decimal
    from django.utils import timezone
    import logging
    
    logger = logging.getLogger(__name__)
    
    discount_amount = Decimal("0.00")
    coupon_instance = None
    error_message = None
    
    if not coupon_id or item_total <= 0:
        return discount_amount, None, None
    
    # Handle case where coupon_id might be a coupon instance instead of ID
    if hasattr(coupon_id, 'id'):
        coupon_id = coupon_id.id
    elif hasattr(coupon_id, 'pk'):
        coupon_id = coupon_id.pk
    
    # Convert to int if it's a string
    try:
        coupon_id = int(coupon_id)
    except (ValueError, TypeError):
        logger.warning(f"[COUPON] Invalid coupon_id type: {type(coupon_id)}, value: {coupon_id}")
        return discount_amount, None, "Invalid coupon ID format"
    
    try:
        from vendor.models import coupon
        
        coupon_instance = coupon.objects.get(id=coupon_id, is_active=True)
    except coupon.DoesNotExist:
        logger.warning(f"[COUPON] Coupon with id {coupon_id} not found or inactive")
        return discount_amount, None, "Invalid or inactive coupon"
    
    # Check validity dates
    now = timezone.now()
    if coupon_instance.start_date > now or coupon_instance.end_date < now:
        logger.warning(f"[COUPON] Coupon {coupon_instance.code} is not valid at this time")
        return discount_amount, None, "Coupon is not valid at this time"
    
    # Check customer_id: if set, must match user.id
    if coupon_instance.customer_id is not None:
        if not user or coupon_instance.customer_id != user.id:
            logger.warning(f"[COUPON] Coupon {coupon_instance.code} is not available for this user")
            return discount_amount, None, "This coupon is not available for your account"
    
    # # Only apply discount-type coupons
    # if coupon_instance.coupon_type != "discount":
    #     logger.warning(f"[COUPON] Coupon {coupon_instance.code} is not a discount coupon")
    #     return discount_amount, None, "This coupon cannot be applied to cart total"
    
    # Check minimum purchase condition (against item_total only, as per cart logic)
    if coupon_instance.min_purchase and item_total < coupon_instance.min_purchase:
        logger.warning(f"[COUPON] Cart value {item_total} is less than minimum purchase {coupon_instance.min_purchase}")
        return discount_amount, None, f"Cart value is less to apply this coupon. Minimum cart value required is {coupon_instance.min_purchase}."
    
    # Calculate discount based on item_total only (same as cart)
    if coupon_instance.type == "percent" and coupon_instance.discount_percentage:
        discount_amount = (item_total * coupon_instance.discount_percentage / Decimal("100")).quantize(Decimal("0.01"))
        # Apply max_discount limit if set
        if coupon_instance.max_discount:
            discount_amount = min(discount_amount, coupon_instance.max_discount)
    elif coupon_instance.type == "amount" and coupon_instance.discount_amount:
        discount_amount = coupon_instance.discount_amount
        # Apply max_discount limit if set (for amount type coupons too)
        if coupon_instance.max_discount:
            discount_amount = min(discount_amount, coupon_instance.max_discount)
    
    # Ensure discount does not exceed item_total
    discount_amount = min(discount_amount, item_total)
    discount_amount = discount_amount.quantize(Decimal("0.01"))
    
    logger.info(f"[COUPON] ✅ Coupon {coupon_instance.code} applied - Discount: {discount_amount} on item_total: {item_total}")
    
    return discount_amount, coupon_instance, None


def calculate_delivery_discount_amount(vendor_user, item_total, tax_total, shipping_fee):
    """
    Calculate delivery discount amount based on vendor's delivery discount settings.
    Discount is calculated as percentage of order total (item_total + tax_total + shipping_fee).
    Same calculation logic used in cart and order creation.
    
    Args:
        vendor_user: The vendor user who owns the products
        item_total: Total value of items in cart/order (Decimal)
        tax_total: Total tax amount (Decimal)
        shipping_fee: Shipping fee amount (Decimal)
    
    Returns:
        Decimal: Delivery discount amount (0.00 if no discount applies)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    delivery_discount_amount = Decimal("0.00")
    
    # Calculate order total (item + tax + shipping) before any discounts
    order_total = item_total + tax_total + shipping_fee
    
    if vendor_user and order_total > 0:
        try:
            from vendor.models import DeliveryDiscount
            
            delivery_discount = DeliveryDiscount.objects.filter(user=vendor_user).first()
            logger.info(f"[DELIVERY_DISCOUNT] Vendor: {vendor_user.id}, Delivery Discount Found: {delivery_discount is not None}")
            
            if delivery_discount:
                logger.info(f"[DELIVERY_DISCOUNT] Enabled: {delivery_discount.is_enabled}, Min Cart Value: {delivery_discount.min_cart_value}, Discount %: {delivery_discount.discount_percent}")
                logger.info(f"[DELIVERY_DISCOUNT] Item Total: {item_total}, Tax: {tax_total}, Shipping Fee: {shipping_fee}, Order Total: {order_total}")
                
            if delivery_discount and delivery_discount.is_enabled:
                # Check if cart value meets minimum requirement
                if item_total >= Decimal(str(delivery_discount.min_cart_value)):
                    # Calculate discount on order total (item + tax + shipping)
                    discount_percent = Decimal(str(delivery_discount.discount_percent))
                    calculated_discount = (order_total * discount_percent / Decimal("100")).quantize(
                        Decimal("0.01")
                    )
                    # Cap discount at shipping fee (discount cannot exceed shipping fee)
                    delivery_discount_amount = min(calculated_discount, shipping_fee)
                    logger.info(f"[DELIVERY_DISCOUNT] ✅ Discount Calculated: {calculated_discount} ({(discount_percent)}% of {order_total})")
                    if calculated_discount > shipping_fee:
                        logger.info(f"[DELIVERY_DISCOUNT] ✅ Discount Capped at Shipping Fee: {delivery_discount_amount} (max: {shipping_fee})")
                    else:
                        logger.info(f"[DELIVERY_DISCOUNT] ✅ Discount Applied: {delivery_discount_amount}")
                else:
                    logger.info(f"[DELIVERY_DISCOUNT] ❌ Min cart value not met: {item_total} < {delivery_discount.min_cart_value}")
            elif delivery_discount:
                logger.info(f"[DELIVERY_DISCOUNT] ❌ Discount exists but is not enabled")
            else:
                logger.info(f"[DELIVERY_DISCOUNT] ❌ No delivery discount found for vendor {vendor_user.id}")
        except Exception as e:
            # If any error, continue without discount
            logger.error(f"[DELIVERY_DISCOUNT] ❌ Error calculating discount: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    if not vendor_user:
        logger.info(f"[DELIVERY_DISCOUNT] No vendor_user provided")
    elif order_total <= 0:
        logger.info(f"[DELIVERY_DISCOUNT] Order total is 0 or negative: {order_total}")
    
    logger.info(f"[DELIVERY_DISCOUNT] Final discount amount: {delivery_discount_amount}")
    return delivery_discount_amount


def send_order_notification_to_customer(order):
    """
    Send push notification to customer when a new order is placed.
    Gets notification message from each vendor whose products are in the order.
    """
    from firebase_admin import messaging
    from users.models import DeviceToken
    from vendor.models import OrderNotificationMessage
    
    # Get customer (order user)
    customer = order.user
    if not customer:
        logger.warning("No customer found for order, skipping notification")
        return
    
    # Get all unique vendors from order items
    order_items = order.items.select_related('product', 'product__user').all()
    vendor_ids = set()
    for item in order_items:
        if item.product and item.product.user:
            vendor_ids.add(item.product.user.id)
    
    if not vendor_ids:
        logger.warning("No vendors found in order items, skipping notification")
        return
    
    # Get device token for customer
    try:
        device_token_obj = DeviceToken.objects.get(user=customer)
        if not device_token_obj.token or not device_token_obj.token.strip():
            logger.warning(f"No device token found for customer {customer.id}, skipping notification")
            return
        customer_token = device_token_obj.token.strip()
    except DeviceToken.DoesNotExist:
        logger.warning(f"No device token found for customer {customer.id}, skipping notification")
        return
    
    # Send notification for each vendor (if they have a notification message configured)
    for vendor_id in vendor_ids:
        try:
            # Get vendor's order notification message
            notification_msg = OrderNotificationMessage.objects.filter(
                user_id=vendor_id,
                is_active=True
            ).first()
            
            if not notification_msg or not notification_msg.message:
                logger.info(f"No active notification message for vendor {vendor_id}, skipping")
                continue
            
            # Send push notification
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Message from vendor",
                        body=f"Message from vendor: {notification_msg.message}",
                    ),
                    data={
                        "order_id": str(order.order_id),
                        "type": "new_order"
                    },
                    token=customer_token,
                )
                
                response = messaging.send(message)
                logger.info(f"Successfully sent order notification to customer {customer.id} for vendor {vendor_id}: {response}")
            except Exception as e:
                logger.error(f"Error sending notification to customer {customer.id} for vendor {vendor_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing notification for vendor {vendor_id}: {e}")


def send_vendor_notification(vendor_user, notification_type, title, body, data=None):
    """
    Send push notification to vendor (product.user or vendor_store.user).
    
    Args:
        vendor_user: The vendor User object to notify
        notification_type: Type of notification (shop_visit, follow, unfollow, review, product_like, cart_add)
        title: Notification title
        body: Notification body
        data: Additional data dict for the notification
    """
    from firebase_admin import messaging
    from users.models import DeviceToken
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not vendor_user:
        logger.warning(f"No vendor user provided for {notification_type} notification")
        return False
    
    # Get device token for vendor
    try:
        device_token_obj = DeviceToken.objects.get(user=vendor_user)
        if not device_token_obj.token or not device_token_obj.token.strip():
            logger.warning(f"No device token found for vendor {vendor_user.id}, skipping notification")
            return False
        vendor_token = device_token_obj.token.strip()
    except DeviceToken.DoesNotExist:
        logger.warning(f"No device token found for vendor {vendor_user.id}, skipping notification")
        return False
    
    # Prepare notification data
    notification_data = {
        "type": notification_type,
        "vendor_id": str(vendor_user.id),
    }
    if data:
        notification_data.update(data)
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={k: str(v) for k, v in notification_data.items()},
            token=vendor_token,
        )
        
        response = messaging.send(message)
        logger.info(f"✅ Successfully sent {notification_type} notification to vendor {vendor_user.id}: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ Error sending {notification_type} notification to vendor {vendor_user.id}: {e}")
        return False


def send_order_status_notification(order, status, previous_status=None):
    """
    Send push notification to customer when order status changes.
    
    Status mapping:
    - 'not_accepted' -> "Order Placed"
    - 'accepted' -> "Order Accepted"
    - 'ready_to_shipment' -> "Order Ready"
    - 'intransit' (OrderItem) -> "Out for Delivery"
    - 'completed' -> "Order Completed"
    """
    from firebase_admin import messaging
    from users.models import DeviceToken
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get customer (order user)
    customer = order.user
    if not customer:
        logger.warning(f"No customer found for order {order.order_id}, skipping status notification")
        return False
    
    # Get device token for customer
    try:
        device_token_obj = DeviceToken.objects.get(user=customer)
        if not device_token_obj.token or not device_token_obj.token.strip():
            logger.warning(f"No device token found for customer {customer.id}, skipping status notification")
            return False
        customer_token = device_token_obj.token.strip()
    except DeviceToken.DoesNotExist:
        logger.warning(f"No device token found for customer {customer.id}, skipping status notification")
        return False
    
    # Map status to notification title and body
    status_messages = {
        'not_accepted': {
            'title': 'Order Placed',
            'body': f'Your order {order.order_id} has been placed successfully!'
        },
        'accepted': {
            'title': 'Order Accepted',
            'body': f'Your order {order.order_id} has been accepted by the vendor.'
        },
        'ready_to_shipment': {
            'title': 'Order Ready',
            'body': f'Your order {order.order_id} is ready for shipment!'
        },
        'intransit': {
            'title': 'Out for Delivery',
            'body': f'Your order {order.order_id} is out for delivery!'
        },
        'completed': {
            'title': 'Order Completed',
            'body': f'Your order {order.order_id} has been delivered successfully!'
        },
        'cancelled': {
            'title': 'Order Cancelled',
            'body': f'Your order {order.order_id} has been cancelled.'
        },
        'cancelled_by_vendor': {
            'title': 'Order Cancelled',
            'body': f'Your order {order.order_id} has been cancelled by the vendor.'
        },
        'refund_initiated': {
            'title': 'Refund Initiated',
            'body': f'Refund for your order {order.order_id} has been initiated. Please wait up to 48 hours for the amount to reflect in your account.'
        }
    }
    
    # Get notification message for this status
    notification_data = status_messages.get(status)
    if not notification_data:
        logger.info(f"No notification message configured for status: {status}")
        return False
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification_data['title'],
                body=notification_data['body'],
            ),
            data={
                "order_id": str(order.order_id),
                "order_status": status,
                "type": "order_status_update"
            },
            token=customer_token,
        )
        
        response = messaging.send(message)
        logger.info(f"✅ Successfully sent order status notification to customer {customer.id} for order {order.order_id}: {status} - {response}")
        return True
    except Exception as e:
        # Common Firebase error: token is no longer valid (user uninstalled app / token rotated)
        # Example message: "Requested entity was not found."
        msg = str(e)
        logger.error(
            f"❌ Error sending order status notification to customer {customer.id} for order {order.order_id}: {msg}"
        )
        try:
            if "Requested entity was not found" in msg:
                # Delete invalid token so we don't keep failing for this user
                DeviceToken.objects.filter(user=customer).delete()
                logger.warning(f"[FCM] Deleted invalid device token for customer {customer.id}")
        except Exception:
            pass
        return False


def on_order_accepted(order):
    """
    When vendor accepts an online order: create OnlineOrderLedger per item, reduce stock,
    assign serial/IMEI where applicable. Call from accept_order, OrderViewSet.update, uEngage webhook.
    """
    from vendor.models import OnlineOrderLedger, serial_imei_no
    from vendor.signals import log_stock_transaction
    from django.db.models import F

    for oi in order.items.select_related("product", "product__user").all():
        # Idempotent: if ledger exists, we already processed this item
        if OnlineOrderLedger.objects.filter(order_item=oi).exists():
            continue
        # 1. OnlineOrderLedger
        OnlineOrderLedger.objects.create(
            user=oi.product.user,
            order_item=oi,
            product=oi.product,
            order_id=order.id,
            quantity=oi.quantity,
            amount=order.total_amount,
            status="recorded",
            note="Online order recorded (accepted)",
        )
        logger.info(f"[ON_ORDER_ACCEPTED] OnlineOrderLedger created for OrderItem {oi.id}")
        # 2. Stock
        product.objects.filter(id=oi.product.id).update(
            stock_cached=F("stock_cached") - oi.quantity
        )
        log_stock_transaction(oi.product, "sale", -oi.quantity, ref_id=oi.pk)
        logger.info(f"[ON_ORDER_ACCEPTED] Stock reduced for Product {oi.product.id} by {oi.quantity}")
        # 3. Serial/IMEI if not already assigned
        if not oi.serial_imei_number_id:
            unsold = serial_imei_no.objects.filter(product=oi.product, is_sold=False)
            if unsold.exists():
                s = random.choice(list(unsold))
                oi.serial_imei_number = s
                oi.save(update_fields=["serial_imei_number"])
                serial_imei_no.objects.filter(id=s.id).update(is_sold=True)
                logger.info(f"[ON_ORDER_ACCEPTED] Assigned serial/IMEI {s.id} to OrderItem {oi.id}")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_details = UserProfileSerializer(source = 'user', read_only=True)
    address_details = AddressSerializer(source="address", read_only = True)
    coupon_details = serializers.SerializerMethodField()
    vendor_mobile = serializers.SerializerMethodField()
    delivery_boy_details = serializers.SerializerMethodField()
    uengage_delivery_boy = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["id", "created_at", "items", "item_total", "tax_total", "coupon", "delivery_discount_amount", "total_amount", "order_id", 'user_details', 'address_details', 'store_details', 'coupon_details', 'vendor_mobile', 'delivery_boy_details', 'uengage_delivery_boy']
    
    def get_coupon_details(self, obj):
        """Return full coupon details if coupon was applied"""
        if obj.coupon_id:
            from vendor.serializers import coupon_serializer
            return coupon_serializer(obj.coupon_id).data
        return None
    
    def get_vendor_mobile(self, obj):
        """Return vendor mobile number from order items"""
        try:
            # Get first order item to find vendor
            first_item = obj.items.select_related('product', 'product__user').first()
            if first_item and first_item.product and first_item.product.user:
                vendor_user = first_item.product.user
                # Try to get mobile number from user
                mobile = getattr(vendor_user, 'mobile_number', None) or getattr(vendor_user, 'mobile', None) or getattr(vendor_user, 'phone', None)
                return str(mobile) if mobile else None
        except Exception:
            pass
        return None
    
    def get_delivery_boy_details(self, obj):
        """Return full delivery boy details if assigned"""
        if obj.delivery_boy:
            from vendor.serializers import DeliveryBoySerializer
            return DeliveryBoySerializer(obj.delivery_boy).data
        return None
    
    def get_uengage_delivery_boy(self, obj):
        """Return uEngage delivery boy details from webhook data"""
        if obj.uengage_task_id:
            return {
                "task_id": obj.uengage_task_id,
                "rider_name": obj.uengage_rider_name,
                "rider_contact": obj.uengage_rider_contact,
                "rider_latitude": float(obj.uengage_rider_latitude) if obj.uengage_rider_latitude else None,
                "rider_longitude": float(obj.uengage_rider_longitude) if obj.uengage_rider_longitude else None,
            }
        return None
    
    def create(self, validated_data):
        logger.info("=" * 80)
        logger.info("[ORDER_SERIALIZER] ========== CREATE METHOD CALLED ==========")
        request = self.context.get("request")
        items_data = request.data.get("items", [])
        logger.info(f"[ORDER_SERIALIZER] Items count: {len(items_data) if items_data else 0}")
        if not items_data or not isinstance(items_data, list):
            raise serializers.ValidationError({"items": ["No items provided."]})

        with transaction.atomic():
            # calculate totals
            item_total = Decimal("0.00")
            tax_total = Decimal("0.00")
            order_items = []
            print_jobs_payload = []  # parallel array of print job payloads or None

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

            # Gather print job payload either from request item or from cart (fallback)
            item_print_job = item.get("print_job")
            is_print_product = getattr(product1, "product_type", None) == "print"
            
            if item_print_job is None and is_print_product:
                cart_item = (
                    Cart.objects.filter(user=request.user, product=product1)
                    .select_related("print_job")
                    .first()
                )
                if cart_item and hasattr(cart_item, "print_job"):
                    pj = cart_item.print_job
                    item_print_job = {
                        "total_amount": pj.total_amount,
                        "print_type": pj.print_type,
                        "print_variant": getattr(pj.print_variant, "id", None),
                        "customize_variant": getattr(pj.customize_variant, "id", None),
                        "add_ons": list[Any](pj.add_ons.values_list("id", flat=True)),
                        "files": [
                            {
                                "file": pf.file,  # will be used directly
                                "instructions": getattr(pf, "instructions", None),  # Instructions now at file level
                                "number_of_copies": pf.number_of_copies,
                                "page_count": pf.page_count,
                                "page_numbers": pf.page_numbers,
                            }
                            for pf in pj.files.all()
                        ],
                    }
            print_jobs_payload.append(item_print_job)

            # Calculate pricing based on product type
            if is_print_product and item_print_job:
                # For print products: get price from variant if available, otherwise use product sales_price
                unit_price = None
                
                # Check for print_variant first
                print_variant_id = item_print_job.get("print_variant")
                if print_variant_id:
                    try:
                        from vendor.models import PrintVariant

                        print_variant = PrintVariant.objects.get(id=print_variant_id)
                        if print_variant.price:
                            unit_price = Decimal(str(print_variant.price))
                    except Exception:
                        pass
                
                # If no print_variant price, check customize_variant
                if unit_price is None:
                    customize_variant_id = item_print_job.get("customize_variant")
                    if customize_variant_id:
                        try:
                            from vendor.models import CustomizePrintVariant

                            customize_variant = CustomizePrintVariant.objects.get(
                                id=customize_variant_id
                            )
                            if customize_variant.price:
                                unit_price = Decimal(str(customize_variant.price))
                        except Exception:
                            pass
                
                # Fallback to product sales_price if no variant price found
                if unit_price is None:
                    unit_price = Decimal(str(product1.sales_price))
                
                # For print products: calculate based on total pages
                # Total pages = sum of (page_count * number_of_copies) for all files
                total_pages = Decimal("0")
                files_data = item_print_job.get("files", [])
                for file_data in files_data:
                    page_count = Decimal(str(file_data.get("page_count", 0)))
                    number_of_copies = Decimal(str(file_data.get("number_of_copies", 1)))
                    total_pages += page_count * number_of_copies
                
                # Use variant price (or product sales_price) per page * total_pages
                line_total = unit_price * total_pages
            else:
                # For regular products: use sales_price * quantity
                unit_price = Decimal(str(product1.sales_price))
                line_total = unit_price * quantity
            
            item_total += line_total

            # Add GST to tax_total only if product price is NOT tax inclusive
            try:
                gst_rate = Decimal(str(getattr(product1, "gst", 0) or 0))
            except Exception:
                gst_rate = Decimal("0")
            if not getattr(product1, "tax_inclusive", False) and gst_rate > 0:
                line_tax = (line_total * gst_rate / Decimal("100"))
                # Round to 2 decimals for currency
                line_tax = line_tax.quantize(Decimal("0.01"))
                tax_total += line_tax

            # Store the calculated unit_price (variant price for print products, sales_price for regular)
            order_items.append(
                OrderItem(
                    product=product1,
                    quantity=quantity,
                    price=unit_price,
                )
            )

        # Compute shipping using vendor DeliverySettings and distance between store and order address
        def _to_float(val, default=None):
            try:
                return float(val)
            except Exception:
                return default

        # Determine vendor (assumes all items from one vendor; fallbacks to first item's vendor)
        vendor_user = None
        if order_items:
            vendor_user = order_items[0].product.user

        # Resolve address from validated_data
        addr = validated_data.get("address")
        delivery_type = validated_data.get("delivery_type") or "self_pickup"
        shipping_fee = Decimal("0.00")
        if vendor_user:
            # Load settings once
            ds = (
                DeliverySettings.objects.filter(user=vendor_user)
                .only("general_delivery_charge", "instant_per_km_charge", "instant_min_base_fare")
                .first()
            )
            if delivery_type == "general_delivery":
                # Flat general delivery charge
                shipping_fee = Decimal(str(getattr(ds, "general_delivery_charge", 50.00)))
            elif delivery_type == "instant_delivery":
                base_fare = Decimal(str(getattr(ds, "instant_min_base_fare", 30.00)))
                per_km = Decimal(str(getattr(ds, "instant_per_km_charge", 10.00)))

                # Need coordinates to compute distance; if missing, fall back to base fare
                dist_km = None
                if addr:
                    # vendor store coords
                    store = (
                        vendor_store.objects.filter(user=vendor_user)
                        .only("latitude", "longitude")
                        .first()
                    )
                    lat1 = _to_float(getattr(store, "latitude", None)) if store else None
                    lon1 = _to_float(getattr(store, "longitude", None)) if store else None
                    # customer address coords
                    lat2 = _to_float(getattr(addr, "latitude", None))
                    lon2 = _to_float(getattr(addr, "longitude", None))

                    if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
                        # Haversine distance in km
                        import math

                        R = 6371.0
                        dlat = math.radians(lat2 - lat1)
                        dlon = math.radians(lon2 - lon1)
                        a = (
                            math.sin(dlat / 2) ** 2
                            + math.cos(math.radians(lat1))
                            * math.cos(math.radians(lat2))
                            * math.sin(dlon / 2) ** 2
                        )
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                        dist_km = Decimal(str(R * c)).quantize(Decimal("0.01"))

                if dist_km is not None:
                    calculated = (per_km * dist_km).quantize(Decimal("0.01"))
                    shipping_fee = max(base_fare, calculated)
                else:
                    shipping_fee = base_fare
            else:
                # self_pickup or on_shop_order => no shipping
                shipping_fee = Decimal("0.00")

        # ensure shipping fee in validated_data reflects computed value
        validated_data["shipping_fee"] = shipping_fee

        # Calculate coupon discount - recalculate based on actual order totals
        coupon_id = validated_data.get("coupon_id") or request.data.get("coupon_id")
        coupon_discount = Decimal("0.00")
        coupon_instance = None
        
        if coupon_id:
            logger.info(f"[ORDER_SERIALIZER] Calculating coupon discount - Coupon ID: {coupon_id}, Item Total: {item_total}")
            coupon_discount, coupon_instance, coupon_error = calculate_coupon_discount_amount(
                coupon_id=coupon_id,
                item_total=item_total,
                user=request.user
            )
            
            if coupon_error:
                logger.warning(f"[ORDER_SERIALIZER] ❌ Coupon validation failed: {coupon_error}")
                raise serializers.ValidationError({"coupon_id": [coupon_error]})
            
            if coupon_discount > 0:
                logger.info(f"[ORDER_SERIALIZER] ✅ Coupon discount calculated: {coupon_discount}")
            else:
                logger.info(f"[ORDER_SERIALIZER] No coupon discount applied")
        else:
            # Fallback: if coupon amount is provided directly (for backward compatibility)
            coupon_amount = validated_data.get("coupon", 0)
            if coupon_amount:
                coupon_discount = Decimal(str(coupon_amount))
                logger.info(f"[ORDER_SERIALIZER] Using provided coupon amount (backward compatibility): {coupon_discount}")
            else:
                logger.info(f"[ORDER_SERIALIZER] No coupon provided - coupon_id: {coupon_id}, coupon amount: {coupon_amount}")

        # Calculate delivery discount using the same calculation logic as cart
        logger.info(f"[ORDER_SERIALIZER] Calculating delivery discount - Vendor: {vendor_user.id if vendor_user else None}, Item Total: {item_total}, Tax: {tax_total}, Shipping Fee: {shipping_fee}")
        delivery_discount_amount = calculate_delivery_discount_amount(vendor_user, item_total, tax_total, shipping_fee)
        logger.info(f"[ORDER_SERIALIZER] ✅ Delivery discount calculated: {delivery_discount_amount}")

        # calculate final total (subtract coupon and delivery discount)
        calculated_total = item_total + tax_total + shipping_fee - coupon_discount - delivery_discount_amount
        # Round total amount up to nearest whole number (ceiling)
        import math
        total_amount = Decimal(str(math.ceil(float(calculated_total)))).quantize(Decimal("0.01"))
        logger.info(f"[ORDER_SERIALIZER] Calculated Total: {calculated_total}, Rounded Up Total: {total_amount}")
        logger.info(f"[ORDER_SERIALIZER] Final totals - Item Total: {item_total}, Tax: {tax_total}, Shipping: {shipping_fee}, Coupon: {coupon_discount}, Delivery Discount: {delivery_discount_amount}, Total Amount: {total_amount}")

        # Create order (order_id is generated server-side in Order.save()).
        # Add an extra retry layer here to avoid crashing the API on rare UNIQUE collisions.
        from django.db import IntegrityError
        order = None
        last_exc = None
        
        # is_paid: False at creation for all orders. Set True only when payment is confirmed:
        # - Online (Cashfree): webhook sets is_paid=True when Cashfree sends PAYMENT_SUCCESS
        # - COD/Cash: set is_paid=True when order is completed/delivered (vendor or uengage webhook)
        payment_mode = validated_data.get('payment_mode', 'COD')
        is_paid = False
        if payment_mode and payment_mode.lower() not in ('cod', 'cash'):
            logger.info(f"[ORDER_SERIALIZER] Payment mode is '{payment_mode}' (online) - is_paid=False until Cashfree webhook confirms payment")
        else:
            logger.info(f"[ORDER_SERIALIZER] Payment mode is '{payment_mode}' (COD/Cash) - is_paid will be set when order is completed")
        
        # Remove is_paid from validated_data if it exists to avoid duplicate keyword argument
        validated_data.pop('is_paid', None)
        
        for _attempt in range(5):
            try:
                with transaction.atomic():
                    # Remove coupon_id from validated_data if it exists to avoid duplicate
                    validated_data.pop('coupon_id', None)
                    validated_data.pop('coupon', None)  # Remove old coupon amount field
                    
                    order = Order.objects.create(
                        **validated_data,
                        item_total=item_total,
                        tax_total=tax_total,
                        coupon=coupon_discount,
                        coupon_id=coupon_instance,
                        delivery_discount_amount=delivery_discount_amount,
                        total_amount=total_amount,
                        is_paid=is_paid,
                    )
                break
            except IntegrityError as e:
                last_exc = e
                if "order_id" in str(e) or "UNIQUE constraint failed" in str(e):
                    continue
                raise

        if order is None:
            raise last_exc or serializers.ValidationError({"detail": "Unable to create order. Please try again."})

        # bulk create items with linked order (serial/IMEI, ledger, stock: deferred to order accepted)
        logger.info(f"[ORDER_SERIALIZER] About to bulk_create {len(order_items)} order items")
        for oi in order_items:
            oi.order = order
        OrderItem.objects.bulk_create(order_items)
        logger.info(f"[ORDER_SERIALIZER] ✅ bulk_create completed for {len(order_items)} items")
        
        # Refresh order from DB to get saved order items with IDs
        order.refresh_from_db()
        logger.info(f"[ORDER_SERIALIZER] Order refreshed from DB. Order ID: {order.id}")
        # OnlineOrderLedger, stock reduction, serial/IMEI assignment: done in on_order_accepted() when vendor accepts
        saved_order_items = list(order.items.all().order_by("id"))

        # Serviceability check (only when vendor has auto-assign enabled)
        auto_assign_enabled = False
        try:
            if vendor_user:
                from vendor.models import DeliveryMode

                dm = DeliveryMode.objects.filter(user=vendor_user).only("is_auto_assign_enabled").first()
                auto_assign_enabled = bool(getattr(dm, "is_auto_assign_enabled", False))
        except Exception:
            auto_assign_enabled = False

        print("\n" + "=" * 80)
        print("[OrderSerializer] Serviceability pre-check")
        print(f"Order ID: {order.order_id}")
        print(f"Delivery Type: {order.delivery_type}")
        print(f"Has Address: {bool(order.address)}")
        print(f"Vendor auto-assign enabled: {auto_assign_enabled}")

        if auto_assign_enabled and order.delivery_type == "instant_delivery" and order.address:
            try:
                from integrations.uengage import get_serviceability_for_order
                print("[OrderSerializer] Checking uEngage serviceability before finalizing order...")
                serviceability_result = get_serviceability_for_order(order)
                print(f"[OrderSerializer] Serviceability result: {serviceability_result}")

                ok = serviceability_result.get("ok")
                svc = (serviceability_result.get("raw") or {}).get("serviceability") or {}
                location_ok = svc.get("locationServiceAble")

                if not ok:
                    msg = "No delivery boy present at the moment."
                    if location_ok is False:
                        msg = "Delivery location not serviceable."
                    raise serializers.ValidationError({"delivery": msg})
            except serializers.ValidationError:
                raise
            except Exception as e:
                print(f"[OrderSerializer] Serviceability check exception: {e}")
                raise serializers.ValidationError(
                    {"delivery": "Unable to confirm delivery availability. Please try again."}
                )
        else:
            print("[OrderSerializer] Skipping serviceability: auto-assign disabled or not instant_delivery or no address")
        
        # Set is_auto_managed based on whether auto-assign is enabled
        # If auto-assign is disabled, explicitly set to False (though it's already the default)
        # If auto-assign is enabled, it will be set to True later when auto-assignment actually happens
        if not auto_assign_enabled:
            order.is_auto_managed = False
            order.save(update_fields=['is_auto_managed'])

        # After bulk create, attach print jobs (if any)
        # IMPORTANT: Read all file data FIRST before any deletions happen
        # This prevents files from being deleted when cart is cleared
        files_data_cache = []  # Store file data before cart deletion
        
        for oi, pj_payload in zip(saved_order_items, print_jobs_payload):
            if not pj_payload:
                files_data_cache.append(None)
                continue
            
            # Pre-read all file data from cart BEFORE cart deletion
            files = pj_payload.get("files") or []
            cached_files = []
            
            for f in files:
                src = f.get("file")
                if not src:
                    cached_files.append(None)
                    continue

                from django.core.files.base import ContentFile
                from django.core.files.storage import default_storage
                import os

                # Read bytes from source file IMMEDIATELY (before cart deletion)
                data = None
                filename = "file"
                
                try:
                    # Handle different file types
                    if hasattr(src, "read"):
                        # It's an UploadedFile or open file handle
                        if hasattr(src, "seek"):
                            src.seek(0)  # Reset to beginning
                        data = src.read()
                        filename = getattr(src, "name", "file")
                        if hasattr(src, "close") and not hasattr(src, "closed"):
                            try:
                                src.close()
                            except Exception:
                                pass
                    elif hasattr(src, "name"):
                        # It's a FieldFile (Django model file field)
                        # Check if file actually exists on disk
                        if hasattr(src, "storage") and hasattr(src, "name"):
                            if src.storage.exists(src.name):
                                src.open("rb")
                                data = src.read()
                                src.close()
                                filename = os.path.basename(src.name)
                            else:
                                logger.warning(f"[ORDER_SERIALIZER] File does not exist on disk: {src.name}")
                                cached_files.append(None)
                                continue
                        else:
                            # Fallback: try to open it
                            try:
                                if hasattr(src, "open"):
                                    src.open("rb")
                                data = src.read()
                                filename = getattr(src, "name", "file")
                            finally:
                                try:
                                    if hasattr(src, "close"):
                                        src.close()
                                except Exception:
                                    pass
                    else:
                        logger.warning(f"[ORDER_SERIALIZER] Unknown file type: {type(src)}")
                        cached_files.append(None)
                        continue
                        
                except Exception as e:
                    logger.error(f"[ORDER_SERIALIZER] Error reading file for order: {e}", exc_info=True)
                    cached_files.append(None)
                    continue

                if not data:
                    logger.warning(f"[ORDER_SERIALIZER] No data read from file, skipping")
                    cached_files.append(None)
                    continue

                filename = os.path.basename(filename) if filename else "file"
                cached_files.append({
                    "data": data,
                    "filename": filename,
                    "instructions": f.get("instructions"),
                    "number_of_copies": f.get("number_of_copies", 1),
                    "page_count": f.get("page_count", 0),
                    "page_numbers": f.get("page_numbers", ""),
                })
            
            files_data_cache.append({
                "pj_payload": pj_payload,
                "files": cached_files
            })

        # NOW create OrderPrintJob and OrderPrintFile using cached data
        for oi, cached_data in zip(saved_order_items, files_data_cache):
            if not cached_data or not cached_data.get("pj_payload"):
                continue
                
            pj_payload = cached_data["pj_payload"]
            
            # Resolve foreign keys if IDs provided
            print_variant = None
            customize_variant = None
            if isinstance(pj_payload.get("print_variant"), int):
                from vendor.models import PrintVariant as PV

                try:
                    print_variant = PV.objects.get(id=pj_payload["print_variant"])
                except PV.DoesNotExist:
                    print_variant = None
            if isinstance(pj_payload.get("customize_variant"), int):
                from vendor.models import CustomizePrintVariant as CPV

                try:
                    customize_variant = CPV.objects.get(id=pj_payload["customize_variant"])
                except CPV.DoesNotExist:
                    customize_variant = None

            order_pj = OrderPrintJob.objects.create(
                order_item=oi,
                total_amount=pj_payload.get("total_amount") or 0,
                print_type=pj_payload.get("print_type") or "single",
                print_variant=print_variant,
                customize_variant=customize_variant,
            )

            # add-ons
            addon_ids = pj_payload.get("add_ons") or []
            if addon_ids:
                from vendor.models import addon as Addon

                valid_addons = Addon.objects.filter(id__in=addon_ids)
                order_pj.add_ons.set(valid_addons)

            # files - use cached data (already read from disk)
            cached_files = cached_data.get("files", [])
            for f_data in cached_files:
                if not f_data:
                    continue
                
                from django.core.files.base import ContentFile
                
                new_file = ContentFile(f_data["data"])
                new_file.name = f_data["filename"]  # upload_to will prepend order_print_jobs/files/

                OrderPrintFile.objects.create(
                    print_job=order_pj,
                    file=new_file,
                    instructions=f_data.get("instructions"),
                    number_of_copies=f_data.get("number_of_copies", 1),
                    page_count=f_data.get("page_count", 0),
                    page_numbers=f_data.get("page_numbers", ""),
                )
                # Do NOT reuse original path; create a fresh file so
                # OrderPrintFile.upload_to("order_print_jobs/files/") is applied.
                src = f.get("file")
                if not src:
                    continue

                from django.core.files.base import ContentFile
                from django.core.files.storage import default_storage
                import os

                # Read bytes from source file / FieldFile / UploadedFile
                data = None
                filename = "file"
                
                try:
                    # Handle different file types
                    if hasattr(src, "read"):
                        # It's an UploadedFile or open file handle
                        if hasattr(src, "seek"):
                            src.seek(0)  # Reset to beginning
                        data = src.read()
                        filename = getattr(src, "name", "file")
                        if hasattr(src, "close") and not hasattr(src, "closed"):
                            try:
                                src.close()
                            except Exception:
                                pass
                    elif hasattr(src, "name"):
                        # It's a FieldFile (Django model file field)
                        # Check if file actually exists on disk
                        if hasattr(src, "storage") and hasattr(src, "name"):
                            if src.storage.exists(src.name):
                                src.open("rb")
                                data = src.read()
                                src.close()
                                filename = os.path.basename(src.name)
                            else:
                                logger.warning(f"[ORDER_SERIALIZER] File does not exist on disk: {src.name}")
                                continue
                        else:
                            # Fallback: try to open it
                            try:
                                if hasattr(src, "open"):
                                    src.open("rb")
                                data = src.read()
                                filename = getattr(src, "name", "file")
                            finally:
                                try:
                                    if hasattr(src, "close"):
                                        src.close()
                                except Exception:
                                    pass
                    else:
                        logger.warning(f"[ORDER_SERIALIZER] Unknown file type: {type(src)}")
                        continue
                        
                except Exception as e:
                    logger.error(f"[ORDER_SERIALIZER] Error reading file for order: {e}", exc_info=True)
                    continue

        # Clear cart only when order is confirmed: COD/cash immediately; online pay only after payment success (cleared in webhook).
        payment_mode = (getattr(order, "payment_mode", "") or "COD").strip().lower()
        is_online_pay = payment_mode not in ("cod", "cash")
        should_clear_cart = not is_online_pay or getattr(order, "is_paid", False)
        if should_clear_cart:
            Cart.objects.filter(user=request.user).delete()
        else:
            logger.info(f"[ORDER_SERIALIZER] Skipping cart clear (online pay, payment not confirmed yet) for order {order.order_id}")

        # Send order-placed notifications only if NOT online pay, or if online pay then only when already paid.
        # For online pay, payment is not confirmed yet at create time → skip; notifications sent when webhook sets is_paid=True.
        is_online_pay = payment_mode not in ("cod", "cash")
        should_send_order_placed = not is_online_pay or getattr(order, "is_paid", False)
        if should_send_order_placed:
            try:
                send_order_notification_to_customer(order)
                send_order_status_notification(order, 'not_accepted')
            except Exception as e:
                logger.error(f"Error sending order notification: {e}", exc_info=True)
            try:
                order_items = order.items.select_related('product', 'product__user').all()
                vendor_users = set()
                for item in order_items:
                    if item.product and item.product.user:
                        vendor_users.add(item.product.user)
                for vendor_user in vendor_users:
                    try:
                        send_vendor_notification(
                            vendor_user=vendor_user,
                            notification_type="new_order",
                            title="New Order Received",
                            body=f"You have received a new order: {order.order_id}",
                            data={
                                "order_id": str(order.order_id),
                                "order_total": str(order.total_amount),
                                "type": "new_order"
                            }
                        )
                        logger.info(f"[ORDER_SERIALIZER] ✅ Sent order notification to vendor {vendor_user.id} for order {order.order_id}")
                    except Exception as e:
                        logger.error(f"[ORDER_SERIALIZER] ❌ Error sending notification to vendor {vendor_user.id}: {e}")
            except Exception as e:
                logger.error(f"[ORDER_SERIALIZER] ❌ Error sending vendor notifications: {e}", exc_info=True)
        else:
            logger.info(f"[ORDER_SERIALIZER] Skipping order-placed notifications (online pay, payment not confirmed yet) for order {order.order_id}")

        # Delivery task creation is deferred to vendor when status becomes ready_to_shipment
        print("[OrderSerializer] Delivery task will be created when vendor marks ready_to_shipment.")
        print("=" * 80 + "\n")

        return order

    def update(self, instance, validated_data):
        allowed_fields = ["status", "delivery_boy", "is_paid"]
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        instance.save()
        return instance

   



class ReturnExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnExchange
        fields = ['id', 'order_item', 'type', 'reason', 'image', 'created_at', 'updated_at']

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

        # ✅ Update OrderItem status based on return/exchange type
        order_item = instance.order_item
        return_type = instance.type  # 'return' or 'exchange'
        order_item.status = f'{return_type}_requested'  # 'return_requested' or 'exchange_requested'
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
        fields = ["id", "file", "instructions", "number_of_copies", "page_count", "page_numbers"]


# ---------- Print Job ----------
class PrintJobSerializer(serializers.ModelSerializer):

    from vendor.models import addon
    files = PrintFileSerializer(many=True)
    add_ons = serializers.PrimaryKeyRelatedField(queryset=addon.objects.all(), many=True)

    class Meta:
        model = PrintJob
        fields = ["print_type", "add_ons", "files", "total_amount"]

    def create(self, validated_data):
        # Remove instructions if present (instructions moved to file level)
        validated_data.pop("instructions", None)
        files_data = validated_data.pop("files", [])
        add_ons = validated_data.pop("add_ons", [])
        print_job = PrintJob.objects.create(**validated_data)
        print_job.add_ons.set(add_ons)
        for file_data in files_data:
            PrintFile.objects.create(print_job=print_job, **file_data)
        return print_job



# ---------- Cart ----------
class CartSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=product.objects.filter(is_active=True))
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
            # Remove instructions from print_job_data if present (instructions moved to file level)
            print_job_data_clean = {k: v for k, v in print_job_data.items() if k != "instructions"}
            PrintJobSerializer().create({**print_job_data_clean, "cart": cart_item})

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

    user_details = UserProfileSerializer(source = 'user', read_only = True)

    class Meta:
        model = Review
        fields = ['id', 'order_item', 'photo', 'is_visible', 'rating', 'comment', 'user_details', 'created_at', 'updated_at']
        read_only_fields = [ "user"]

from vendor.models import vendor_store

class VendorStoreLiteSerializer(serializers.ModelSerializer):
    following = serializers.SerializerMethodField()

    class Meta:
        model = vendor_store
        fields = "__all__"

    def get_following(self, obj):
        user = self.context["request"].user
        # ✅ just check if this vendor has this user as follower
        return Follower.objects.filter(user=obj.user, follower=user).exists()




class ProductRequestSerializer(serializers.ModelSerializer):
    from masters.serializers import product_category_serializer, product_subcategory_serializer

    store = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()

    user_details = UserProfileSerializer(source = 'user', read_only = True)
    category_details = product_category_serializer(source = 'category', read_only = True)
    sub_category_details = product_subcategory_serializer(source = 'sub_category', read_only = True)
    
    class Meta:
        model = ProductRequest
        fields = "__all__"
        read_only_fields = ["user", "created_at"]

    def get_photos(self, obj):
        """Return list of photo URLs for this request"""
        from .models import ProductRequestImage
        photos = ProductRequestImage.objects.filter(request=obj)
        return [photo.photo.url for photo in photos]

    def get_store(self, obj):
        try:
            # Assuming one store per user
            store = vendor_store.objects.get(user = obj.user)  # related_name='vendor_store'
            if store:
                context = getattr(self, "context", {})
                return VendorStoreLiteSerializer(store, context=context).data
        except vendor_store.DoesNotExist:
            return None

    def get_city(self, obj):
        """Return user's default address city if type is personal, otherwise None."""
        if obj.type == 'personal':
            try:
                from .models import Address
                default_addr = Address.objects.filter(user=obj.user, is_default=True).first()
                if default_addr:
                    return default_addr.town_city
            except Exception:
                pass
        return None 

    def create(self, validated_data):
        """Create ProductRequest and handle multiple photo uploads"""
        from .models import ProductRequestImage
        
        # Get user from context if not in validated_data (set by perform_create)
        user = validated_data.pop('user', None)
        if not user:
            request_obj = self.context.get('request')
            if request_obj and hasattr(request_obj, 'user'):
                user = request_obj.user
        
        # Create the ProductRequest instance
        request_instance = ProductRequest.objects.create(user=user, **validated_data)
        
        # Handle multiple photo uploads
        request_obj = self.context.get('request')
        if request_obj and hasattr(request_obj, 'FILES'):
            # Support multiple field names: photos, photos[], photo, photo[]
            photo_files = []
            for key in request_obj.FILES.keys():
                if key in ('photos', 'photos[]', 'photo', 'photo[]'):
                    photo_files.extend(request_obj.FILES.getlist(key))
                elif key.startswith('photos[') or key.startswith('photo['):
                    photo_files.extend(request_obj.FILES.getlist(key))
            
            # Create ProductRequestImage for each uploaded photo
            for photo_file in photo_files:
                ProductRequestImage.objects.create(
                    request=request_instance,
                    photo=photo_file
                )
        
        return request_instance

    def update(self, instance, validated_data):
        """Update ProductRequest and handle photo uploads"""
        from .models import ProductRequestImage
        
        # Update the ProductRequest instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle new photo uploads
        request_obj = self.context.get('request')
        if request_obj and hasattr(request_obj, 'FILES'):
            # Support multiple field names: photos, photos[], photo, photo[]
            photo_files = []
            for key in request_obj.FILES.keys():
                if key in ('photos', 'photos[]', 'photo', 'photo[]'):
                    photo_files.extend(request_obj.FILES.getlist(key))
                elif key.startswith('photos[') or key.startswith('photo['):
                    photo_files.extend(request_obj.FILES.getlist(key))
            
            # Create ProductRequestImage for each uploaded photo
            for photo_file in photo_files:
                ProductRequestImage.objects.create(
                    request=instance,
                    photo=photo_file
                )
        
        return instance 
        