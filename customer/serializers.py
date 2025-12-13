from typing import Any
from rest_framework import serializers
from .models import *



from vendor.serializers import product_serializer

from django.utils import timezone
import datetime
from django.db import transaction

class OrderPrintFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPrintFile
        fields = ["id", "file", "instructions", "number_of_copies", "page_count", "page_numbers"]


class OrderPrintJobSerializer(serializers.ModelSerializer):
    files = OrderPrintFileSerializer(many=True, read_only=True)
    add_ons = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = OrderPrintJob
        fields = ["total_amount", "print_type", "print_variant", "customize_variant", "add_ons", "files"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_details = product_serializer(source="product", read_only=True)
    is_return_eligible = serializers.SerializerMethodField()
    is_exchange_eligible = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()  # ✅ NEW FIELD
    # Include print job details if any (read-only)
    print_job = OrderPrintJobSerializer(read_only=True)
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
            'is_reviewed'  # ✅ add here also
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

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_details = UserProfileSerializer(source = 'user', read_only=True)
    address_details = AddressSerializer(source="address", read_only = True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["id", "created_at", "items", "item_total", "tax_total", "delivery_discount_amount", "total_amount", "order_id", 'user_details', 'address_details', 'store_details']
    
    def create(self, validated_data):
        request = self.context.get("request")
        items_data = request.data.get("items", [])

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
                cart_item = Cart.objects.filter(user=request.user, product=product1).select_related("print_job").first()
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
                            customize_variant = CustomizePrintVariant.objects.get(id=customize_variant_id)
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

        # generate order_id
        # order_id will be generated in Order.save() method

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
            ds = DeliverySettings.objects.filter(user=vendor_user).only(
                "general_delivery_charge", "instant_per_km_charge", "instant_min_base_fare"
            ).first()
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
                    store = vendor_store.objects.filter(user=vendor_user).only("latitude", "longitude").first()
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
                        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
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

        # convert values from validated_data to Decimal safely
        coupon = Decimal(str(validated_data.get("coupon", 0)))

        # Check and apply delivery discount if vendor has it enabled
        delivery_discount_amount = Decimal("0.00")
        if vendor_user and shipping_fee > 0:
            try:
                from vendor.models import DeliveryDiscount
                delivery_discount = DeliveryDiscount.objects.filter(user=vendor_user).first()
                if delivery_discount and delivery_discount.is_enabled:
                    # Check if cart value meets minimum requirement
                    if item_total >= Decimal(str(delivery_discount.min_cart_value)):
                        # Calculate discount on shipping fee
                        discount_percent = Decimal(str(delivery_discount.discount_percent))
                        delivery_discount_amount = (shipping_fee * discount_percent / Decimal("100")).quantize(Decimal("0.01"))
            except Exception:
                # If any error, continue without discount
                pass

            # calculate final total (subtract delivery discount from shipping fee)
            total_amount = item_total + tax_total + shipping_fee - coupon - delivery_discount_amount

            # set calculated totals in order
            # order_id will be generated in Order.save() method
            order = Order.objects.create(
                **validated_data,
                item_total=item_total,
                tax_total=tax_total,
                delivery_discount_amount=delivery_discount_amount,
                total_amount=total_amount,
            )

            # bulk create items with linked order
            for oi in order_items:
                oi.order = order
            OrderItem.objects.bulk_create(order_items)

            # Serviceability check (must have address + instant_delivery)
            print("\n" + "=" * 80)
            print("🛒 [OrderSerializer] Serviceability pre-check")
            print(f"📦 Order ID: {order.order_id}")
            print(f"🚚 Delivery Type: {order.delivery_type}")
            print(f"🏠 Has Address: {bool(order.address)}")

            if order.delivery_type == "instant_delivery" and order.address:
                try:
                    from integrations.uengage import get_serviceability_for_order

                    print("🔍 Checking uEngage serviceability before finalizing order...")
                    serviceability_result = get_serviceability_for_order(order)
                    print(f"📊 Serviceability result: {serviceability_result}")

                    ok = serviceability_result.get("ok")
                    svc = (serviceability_result.get("raw") or {}).get("serviceability") or {}
                    rider_ok = svc.get("riderServiceAble")
                    location_ok = svc.get("locationServiceAble")

                    if not ok:
                        msg = "No delivery boy present at the moment."
                        if location_ok is False:
                            msg = "Delivery location not serviceable."
                        raise serializers.ValidationError({"delivery": msg})
                except serializers.ValidationError:
                    raise
                except Exception as e:
                    print(f"💥 Serviceability check exception: {e}")
                    raise serializers.ValidationError({"delivery": "Unable to confirm delivery availability. Please try again."})
            else:
                print("⏭️ Skipping serviceability: not instant_delivery or no address")

            # After bulk create, attach print jobs (if any)
            for oi, pj_payload in zip(order_items, print_jobs_payload):
                if not pj_payload:
                    continue
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

                # files
                files = pj_payload.get("files") or []
                for f in files:
                    OrderPrintFile.objects.create(
                        print_job=order_pj,
                        file=f.get("file"),
                        instructions=f.get("instructions"),
                        number_of_copies=f.get("number_of_copies", 1),
                        page_count=f.get("page_count", 0),
                        page_numbers=f.get("page_numbers", ""),
                    )

            # ✅ CLEAR CART AFTER SUCCESSFUL ORDER CREATION
            Cart.objects.filter(user=request.user).delete()

            # Delivery task creation is deferred to vendor when status becomes ready_to_shipment
            print("⏭️ Delivery task will be created when vendor marks ready_to_shipment.")
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
        fields = ['id', 'order_item', 'type', 'reason', 'created_at']

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
        order_item.status = 'returned/replaced_requested'
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

    user_details = UserProfileSerializer(source = 'user', read_only = True)
    category_details = product_category_serializer(source = 'category', read_only = True)
    sub_category_details = product_subcategory_serializer(source = 'sub_category', read_only = True)
    class Meta:
        model = ProductRequest
        fields = "__all__"
        read_only_fields = ["user", "created_at"]


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
        