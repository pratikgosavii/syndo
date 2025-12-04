from django.forms import ValidationError
from django.shortcuts import render

# Create your views here.


from masters.models import MainCategory, product_category, product_subcategory
from users.models import *

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from .payments.cashfree import create_order_for, refresh_order_status
from rest_framework.decorators import action
from .payments.cashfree import create_order_for, refresh_order_status
from vendor.models import BannerCampaign, Post, Reel, SpotlightProduct, coupon, vendor_store
from vendor.serializers import BannerCampaignSerializer, PostSerializer, ReelSerializer, SpotlightProductSerializer, VendorStoreSerializer, coupon_serializer
from .models import *
from .serializers import AddressSerializer, CartSerializer, OrderSerializer

from rest_framework import viewsets, permissions

class CustomerOrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Create order and immediately initiate Cashfree payment.
        Returns 201 with order payload + payment_session_id/payment_link.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(user=request.user)

        # Build URLs
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        return_url = f"{scheme}://{host}/payments/success?order_id={order.order_id}"
        notify_url = f"{scheme}://{host}/customer/cashfree/webhook/"
        # Prefer explicit phone from request; fallback to user's mobile/phone fields
        phone = (
            request.data.get("phone")
            or getattr(order.user, "mobile", None)
            or getattr(order.user, "mobile_number", None)
            or getattr(order.user, "phone", None)
            or ""
        )

        # Initiate payment
        payment = create_order_for(
            order,
            customer_id=order.user_id,
            customer_email=getattr(order.user, "email", "") if order.user_id else None,
            customer_phone=phone,
            return_url=return_url,
            notify_url=notify_url,
        )

        base = OrderSerializer(order, context={"request": request}).data
        base["payment"] = payment
        headers = self.get_success_headers(base)
        return Response(base, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        # Only return orders for the logged-in user
        user = self.request.user
        return Order.objects.prefetch_related('items').filter(user=user).order_by('-id')

    def perform_create(self, serializer):
        # Automatically set the user when saving
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="initiate-payment")
    def initiate_payment(self, request, pk=None):
        """
        Trigger Cashfree order creation and return payment_session_id (or payment_link).
        POST /customer/customer-order/{id}/initiate-payment/
        Optional body: {"phone": "9999999999"}
        """
        order = self.get_object()
        # Build return and notify URLs
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        return_url = f"{scheme}://{host}/payments/success?order_id={order.order_id}"
        notify_url = f"{scheme}://{host}/customer/cashfree/webhook/"
        # Prefer explicit phone; fallback to user's stored mobile
        phone = (
            request.data.get("phone")
            or getattr(order.user, "mobile", None)
            or getattr(order.user, "mobile_number", None)
            or getattr(order.user, "phone", None)
            or ""
        )
        data = create_order_for(
            order,
            customer_id=order.user_id,
            customer_email=getattr(order.user, "email", "") if order.user_id else None,
            customer_phone=phone,
            return_url=return_url,
            notify_url=notify_url,
        )
        return Response(data, status=200)

    @action(detail=True, methods=["get"], url_path="refresh-payment-status")
    def refresh_payment_status(self, request, pk=None):
        """
        Manually refresh order payment status from Cashfree (fallback if webhook delayed).
        GET /customer/customer-order/{id}/refresh-payment-status/
        """
        order = self.get_object()
        data = refresh_order_status(order)
        return Response(data, status=200)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import hmac, hashlib, base64, os, json

class ReturnShippingRatesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    

    def get(self, request):
        """
        Get all Return/Exchange requests of logged-in user
        """
        from vendor.models import DeliverySettings, vendor_store
        from users.models import User
        from customer.models import Address
        from decimal import Decimal

        # Compute shipping using vendor DeliverySettings and distance between store and order address
        def _to_float(val, default=None):
            try:
                return float(val)
            except Exception:
                return default

        # Inputs from query params
        vendor_user_id = request.query_params.get("vendor_user_id")
        address_id = request.query_params.get("address_id")
        delivery_type = request.query_params.get("delivery_type") or "self_pickup"

        if not vendor_user_id or not address_id:
            return Response(
                {"detail": "vendor_user_id and address_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            vendor_user = User.objects.get(id=vendor_user_id)
        except User.DoesNotExist:
            return Response({"detail": "Vendor user not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            addr = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        shipping_fee = Decimal("0.00")
        distance_km = None

        if vendor_user:
            # Load settings once
            ds = DeliverySettings.objects.filter(user=vendor_user).only(
                "general_delivery_charge", "instant_per_km_charge", "instant_min_base_fare"
            ).first()
            if delivery_type == "general_delivery":
                # Flat general delivery charge
                shipping_fee = Decimal(str(getattr(ds, "general_delivery_charge", 50.00))) if ds else Decimal("50.00")
            elif delivery_type == "instant_delivery":
                base_fare = Decimal(str(getattr(ds, "instant_min_base_fare", 30.00))) if ds else Decimal("30.00")
                per_km = Decimal(str(getattr(ds, "instant_per_km_charge", 10.00))) if ds else Decimal("10.00")
            else:
                # self_pickup or on_shop_order => no shipping
                shipping_fee = Decimal("0.00")
                # Need coordinates to compute distance; if missing, fall back to base fare
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
                    distance_km = Decimal(str(R * c)).quantize(Decimal("0.01"))

            if distance_km is not None:
                calculated = (per_km * distance_km).quantize(Decimal("0.01"))
                shipping_fee = max(base_fare, calculated) if base_fare is not None else calculated
            else:
                shipping_fee = base_fare
            

        return Response(
            {   
                "delivery_type": delivery_type,
                "shipping_fee": str(shipping_fee),
                "distance_km": str(distance_km) if distance_km is not None else None,
            },
            status=status.HTTP_200_OK,
        )


class RequestOfferAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    

    def get(self, request, request_id):
        """
        Get all Return/Exchange requests of logged-in user
        """
        from vendor.models import Offer
        from vendor.serializers import OfferSerializer

        queryset = Offer.objects.filter(request__id = request_id).order_by('-created_at')
        serializer = OfferSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AllRequestOfferAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get all Return/Exchange requests of logged-in user
        """
        from vendor.models import Offer
        from vendor.serializers import OfferSerializer

        queryset = Offer.objects.filter(request__user=request.user).order_by('-created_at')
        serializer = OfferSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
def cashfree_webhook(request):
    """
    Cashfree webhook to update order status.
    Expects JSON body and header 'x-webhook-signature' (base64 of HMAC-SHA256).
    """
    try:
        raw = request.body
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return Response({"detail": "invalid json"}, status=400)

    signature = request.headers.get("x-webhook-signature") or request.headers.get("X-Webhook-Signature")
    secret = os.getenv("CASHFREE_WEBHOOK_SECRET", "test_webhook_secret")

    # Verify signature if present
    try:
        computed = base64.b64encode(hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()).decode()
        if signature and not hmac.compare_digest(signature, computed):
            return Response({"detail": "invalid signature"}, status=401)
    except Exception:
        pass  # if missing headers, proceed best-effort in sandbox

    # Extract order_id and status robustly
    order_id = (
        payload.get("order_id")
        or payload.get("data", {}).get("order", {}).get("order_id")
        or payload.get("data", {}).get("order_id")
    )
    status_cf = (
        payload.get("order_status")
        or payload.get("data", {}).get("order", {}).get("order_status")
        or payload.get("data", {}).get("payment", {}).get("payment_status")
    )

    if not order_id:
        return Response({"detail": "missing order_id"}, status=400)

    # Update order by cashfree_order_id or order_id
    try:
        order = Order.objects.filter(cashfree_order_id=order_id).first() or Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({"detail": "order not found"}, status=404)

    if status_cf:
        order.cashfree_status = status_cf
        if str(status_cf).upper() in ("PAID", "SUCCESS", "CAPTURED"):
            order.is_paid = True
            order.payment_mode = "Cashfree"
        order.save(update_fields=["cashfree_status", "is_paid", "payment_mode"])

    return Response({"success": True}, status=200)

class ReturnExchangeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get all Return/Exchange requests of logged-in user
        """
        queryset = ReturnExchange.objects.filter(user=request.user).order_by('-created_at')
        serializer = ReturnExchangeSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new Return/Exchange request
        """
        serializer = ReturnExchangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": f"{serializer.validated_data['type'].capitalize()} request created successfully."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """
        Cancel an existing Return/Exchange request (if still pending/requested)
        Example JSON:
        {
            "id": 5
        }
        """
        return_id = request.data.get("id")
        if not return_id:
            return Response({"error": "Request ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = ReturnExchange.objects.get(id=return_id, user=request.user)
        except ReturnExchange.DoesNotExist:
            return Response({"error": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

        if instance.status not in ['returned/replaced_approved', 'returned/replaced_completed']:
            return Response({"error": "Cannot cancel. Request already processed or completed."}, status=status.HTTP_400_BAD_REQUEST)

        instance.order_item.status = 'returned/replaced_cancelled'
        instance.save()

        return Response({"success": "Return/Exchange request cancelled successfully."}, status=status.HTTP_200_OK)




from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import generics

from rest_framework import filters

       
from rest_framework import generics, mixins, filters


from .serializers import VendorStoreLiteSerializer

class VendorStoreListAPIView(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             generics.GenericAPIView):
    queryset = vendor_store.objects.filter(is_active=True)
    serializer_class = VendorStoreSerializer  # ✅ USE NEW ONE HERE
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name", "user__username"]
    lookup_field = "id"

    def get_serializer_context(self):
        return {"request": self.request}  # ✅ needed for following field

    def get(self, request, *args, **kwargs):
        if "id" in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)    # GET /stores/
 


from vendor.models import product
from vendor.serializers import product_serializer
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from vendor.filters import ProductFilter


from django.db.models import Exists, OuterRef, Value, BooleanField, F, FloatField, ExpressionWrapper
from django.db.models.functions import Cast


class ListProducts(ListAPIView):
    serializer_class = product_serializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        user = self.request.user
        qs = product.objects.filter(
            is_active=True,
            sale_type__in=["online", "both"],
            user__vendor_store__is_active=True,
            user__vendor_store__is_online=True,
        )
        print(user)
        # Filter by customer pincode
          # Use the user's default address (is_default=True)
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        print(default_addr)
        if pincode:
            qs = qs.filter(user__coverages__pincode__code=pincode)

        # Annotate favourites
        if user.is_authenticated:
            favs = Favourite.objects.filter(user=user, product=OuterRef('pk'))
            qs = qs.annotate(is_favourite=Exists(favs))
        else:
            qs = qs.annotate(is_favourite=Value(False, output_field=BooleanField()))

        # Optional: order by nearest using simple squared-distance if lat/lng provided
        lat = default_addr.latitude 
        lng = default_addr.longitude
        if lat and lng:
            try:
                lat_f = float(lat); lng_f = float(lng)
                qs = qs.filter(
                    user__vendor_store__latitude__isnull=False,
                    user__vendor_store__longitude__isnull=False,
                )
                dist_expr = (
                    (Cast(F('user__vendor_store__latitude'), FloatField()) - Value(lat_f)) ** 2 +
                    (Cast(F('user__vendor_store__longitude'), FloatField()) - Value(lng_f)) ** 2
                )
                qs = qs.annotate(_dist=ExpressionWrapper(dist_expr, output_field=FloatField())) \
                       .order_by('_dist', 'id')
            except ValueError:
                pass

        return qs.distinct()
    


class ListPosts(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        # Only return posts belonging to the logged-in user
        return Post.objects.all()
    

# class products_details(APIView):
#     """
#     Get details of a single product by ID.
#     """

#     def get(self, request, product_id):
#         try:
#             # Fetch the product by ID
#             product_obj = product.objects.get(id=product_id)

#         except product.DoesNotExist:
#             return Response(
#                 {"error": "Product not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         # Serialize and return product data
#         serializer = product_serializer(product_obj, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_200_OK)
    
    
from rest_framework import status


class FollowUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            target_user = User.objects.get(id=user_id)
            if target_user == request.user:
                return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
            
            obj, created = Follower.objects.get_or_create(user=target_user, follower=request.user)
            if created:
                return Response({"success": True, "message": f"You are now following {target_user.username}"})
            else:
                return Response({"success": True, "message": f"You already follow {target_user.username}"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        """Get list of users the current user is following"""
        following = Follower.objects.filter(follower=request.user).select_related("user")
        data = [{"id": f.user.id, "username": f.user.username} for f in following]
        return Response({"following": data})


class UnfollowUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            target_user = User.objects.get(id=user_id)
            deleted, _ = Follower.objects.filter(user=target_user, follower=request.user).delete()
            if deleted:
                return Response({"success": True, "message": f"You unfollowed {target_user.username}"})
            else:
                return Response({"success": False, "message": f"You were not following {target_user.username}"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        """Get list of users who follow the current user"""
        followers = Follower.objects.filter(user=request.user).select_related("follower")
        data = [{"id": f.follower.id, "username": f.follower.username} for f in followers]
        return Response({"followers": data})


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



from rest_framework.decorators import action
from rest_framework import serializers

from django.db import transaction
import json
from vendor.models import PrintVariant, CustomizePrintVariant, addon



class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Cart.objects.filter(user=self.request.user)
            .select_related("product")
            .prefetch_related("print_job__add_ons", "print_job__files")
        )

    def perform_create(self, serializer):
        product_instance = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)

        # ✅ Create or update cart item
        cart_item, created = Cart.objects.get_or_create(
            user=self.request.user,
            product=product_instance,
            defaults={"quantity": quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # ✅ Handle print jobs
        print_job_data = self.request.data.get("print_job")

        if print_job_data and getattr(product_instance, "product_type", None) == "print":
            # Parse JSON string if necessary
            if isinstance(print_job_data, str):
                try:
                    print_job_data = json.loads(print_job_data)
                except json.JSONDecodeError:
                    raise serializers.ValidationError({"print_job": "Invalid JSON format."})

            # Extract related data
            add_ons = print_job_data.pop("add_ons", [])
            files_data = print_job_data.pop("files", [])

            # 🔧 Convert FK IDs to model instances
            print_variant_id = print_job_data.get("print_variant")
            customize_variant_id = print_job_data.get("customize_variant")

            if print_variant_id:
                try:
                    print_job_data["print_variant"] = PrintVariant.objects.get(id=print_variant_id)
                except PrintVariant.DoesNotExist:
                    raise serializers.ValidationError({"print_variant": "Invalid ID."})

            if customize_variant_id:
                try:
                    print_job_data["customize_variant"] = CustomizePrintVariant.objects.get(id=customize_variant_id)
                except CustomizePrintVariant.DoesNotExist:
                    raise serializers.ValidationError({"customize_variant": "Invalid ID."})

            # ✅ Create or update print job
            print_job, _ = PrintJob.objects.update_or_create(
                cart=cart_item, defaults=print_job_data
            )

            # Handle add-ons (many-to-many)
            if add_ons:
                valid_addons = addon.objects.filter(id__in=add_ons)
                print_job.add_ons.set(valid_addons)

            # Delete old files and recreate
            print_job.files.all().delete()

            # ✅ Handle JSON inline files
            for file_data in files_data:
                PrintFile.objects.create(print_job=print_job, **file_data)

            # ✅ Handle actual uploaded files
            index = 0
            while True:
                uploaded_file = self.request.FILES.get(f"files[{index}].file")
                if not uploaded_file:
                    break
                PrintFile.objects.create(
                    print_job=print_job,
                    file=uploaded_file,
                    number_of_copies=self.request.data.get(f"files[{index}].number_of_copies", 1),
                    page_count=self.request.data.get(f"files[{index}].page_count", 0),
                    page_numbers=self.request.data.get(f"files[{index}].page_numbers", ""),
                )
                index += 1

        return cart_item

    # ✅ Clear cart and add new product
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def clear_and_add(self, request):
        """Clears cart and adds new product (supports print job & file uploads)."""
        product_id = request.data.get("product")
        quantity = request.data.get("quantity", 1)

        if not product_id:
            return Response({"error": "product is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_instance = product.objects.get(pk=product_id)
        except product.DoesNotExist:
            return Response({"error": "Invalid product id."}, status=status.HTTP_404_NOT_FOUND)

        # Clear user's existing cart
        Cart.objects.filter(user=request.user).delete()

        # Create new cart item
        cart_item = Cart.objects.create(user=request.user, product=product_instance, quantity=quantity)

        # ✅ Handle print job and file uploads
        print_job_data = request.data.get("print_job")
        if print_job_data and getattr(product_instance, "product_type", None) == "print":
            if isinstance(print_job_data, str):
                try:
                    print_job_data = json.loads(print_job_data)
                except json.JSONDecodeError:
                    raise serializers.ValidationError({"print_job": "Invalid JSON format."})

            add_ons = print_job_data.pop("add_ons", [])
            files_data = print_job_data.pop("files", [])

            # 🔧 Convert FK IDs to model instances
            print_variant_id = print_job_data.get("print_variant")
            customize_variant_id = print_job_data.get("customize_variant")

            if print_variant_id:
                try:
                    print_job_data["print_variant"] = PrintVariant.objects.get(id=print_variant_id)
                except PrintVariant.DoesNotExist:
                    raise serializers.ValidationError({"print_variant": "Invalid ID."})

            if customize_variant_id:
                try:
                    print_job_data["customize_variant"] = CustomizePrintVariant.objects.get(id=customize_variant_id)
                except CustomizePrintVariant.DoesNotExist:
                    raise serializers.ValidationError({"customize_variant": "Invalid ID."})

            print_job = PrintJob.objects.create(cart=cart_item, **print_job_data)

            if add_ons:
                valid_addons = addon.objects.filter(id__in=add_ons)
                print_job.add_ons.set(valid_addons)

            # JSON-style file data
            for file_data in files_data:
                PrintFile.objects.create(print_job=print_job, **file_data)

            # Multipart-style file data
            index = 0
            while True:
                uploaded_file = request.FILES.get(f"files[{index}].file")
                if not uploaded_file:
                    break
                PrintFile.objects.create(
                    print_job=print_job,
                    file=uploaded_file,
                    number_of_copies=request.data.get(f"files[{index}].number_of_copies", 1),
                    page_count=request.data.get(f"files[{index}].page_count", 0),
                    page_numbers=request.data.get(f"files[{index}].page_numbers", ""),
                )
                index += 1

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["patch"])
    def update_quantity(self, request, pk=None):
        """Update only the quantity (increase or decrease) of an existing cart item."""
        try:
            cart_item = Cart.objects.get(pk=pk, user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=404)

        new_qty = request.data.get("quantity")
        if not new_qty:
            return Response({"error": "quantity is required."}, status=400)

        new_qty = int(new_qty)
        if new_qty <= 0:
            cart_item.delete()
            return Response({"message": "Item removed from cart"}, status=200)

        cart_item.quantity = new_qty
        cart_item.save()
        return Response({"message": "Quantity updated ✅", "quantity": cart_item.quantity}, status=200)
    

        # ✅ Clear entire cart
    @action(detail=False, methods=["post"])
    def clear_cart(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(
            {"message": "Cart cleared successfully ✅"},
            status=status.HTTP_200_OK,
        )

    

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import random



class RandomBannerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = BannerCampaign.objects.filter(is_approved = True)
        count = qs.count()

        if count == 0:
            return Response({"detail": "No banners available."}, status=404)

        ids = list(qs.values_list("id", flat=True))
        random_ids = random.sample(ids, min(10, len(ids)))
        banners = qs.filter(id__in=random_ids)

        serializer = BannerCampaignSerializer(banners, many=True)
        return Response(serializer.data)



from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class FavouriteViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def add(self, request):
        product_id = request.data.get("product_id")
        user = request.user

        fav, created = Favourite.objects.get_or_create(user=user, product_id=product_id)
        if created:
            return Response({"status": "added"}, status=status.HTTP_201_CREATED)
        return Response({"status": "already exists"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def remove(self, request):
        product_id = request.data.get("product_id")
        user = request.user
        Favourite.objects.filter(user=user, product_id=product_id).delete()
        return Response({"status": "removed"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["get"])
    def my_favourites(self, request):
        favourites = Favourite.objects.filter(user=request.user).select_related('product')
        products = [fav.product for fav in favourites]
        serializer = product_serializer(products, many=True)
        return Response(serializer.data)
    


class FavouriteStoreViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def add(self, request):
        store_id = request.data.get("store_id")
        user = request.user

        fav, created = FavouriteStore.objects.get_or_create(user=user, store_id=store_id)
        if created:
            return Response({"status": "added"}, status=status.HTTP_201_CREATED)
        return Response({"status": "already exists"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def remove(self, request):
        store_id = request.data.get("store_id")
        user = request.user
        FavouriteStore.objects.filter(user=user, store_id=store_id).delete()
        return Response({"status": "removed"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["get"])
    def my_favourites(self, request):
        favourites = FavouriteStore.objects.filter(user=request.user).select_related('store')
        stores = [fav.store for fav in favourites]
        serializer = VendorStoreSerializer(stores, many=True)
        return Response(serializer.data)
    




class SpotlightProductView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = SpotlightProduct.objects.all()
        serializer = SpotlightProductSerializer(products, many=True)
        return Response(serializer.data)


class reelsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reels = Reel.objects.all()
        # Filter by customer's pincode coverage if available
        try:
            pincode = getattr(request.user, "pincode", None)
            if pincode:
                reels = reels.filter(
                    Q(product__user__coverages__pincode__code=pincode) |
                    Q(user__coverages__pincode__code=pincode)
                ).distinct()
        except Exception:
            pass
        serializer = ReelSerializer(reels, many=True, context={'request': request})
        return Response(serializer.data)


class offersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Reel.objects.all()
        serializer = ReelSerializer(products, many=True)
        return Response(serializer.data)
    




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone


class CartCouponAPIView(APIView):
    """
    GET: List all active coupons for the store of products in the user's cart.
    POST: Apply a coupon to the cart (send "coupon_code" in body).
    """
    permission_classes = [IsAuthenticated]

    def get_cart_user(self, user):
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return None, cart_items
        return cart_items.first().product.user, cart_items


    def get(self, request):
        user, cart_items = self.get_cart_user(request.user)
        if not user:
            return Response({"coupons": []}, status=200)

        now = timezone.now()
        
        coupons = coupon.objects.filter(
            user=user,
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )

        serializer = coupon_serializer(coupons, many=True)
        return Response({"coupons": serializer.data}, status=200)

    def post(self, request):
        coupon_code = request.data.get("coupon_code")
        if not coupon_code:
            return Response({"error": "coupon_code is required"}, status=status.HTTP_400_BAD_REQUEST)

        user, cart_items = self.get_cart_user(request.user)
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            coupon_instance = coupon.objects.get(user=user, code=coupon_code, is_active=True)
        except coupon.DoesNotExist:
            return Response({"error": "Invalid or inactive coupon"}, status=status.HTTP_404_NOT_FOUND)

        # Check validity dates
        if coupon_instance.start_date > timezone.now() or coupon_instance.end_date < timezone.now():
            return Response({"error": "Coupon is not valid at this time."}, status=status.HTTP_400_BAD_REQUEST)

        # Only apply discount-type coupons
        if coupon_instance.coupon_type != "discount":
            return Response({"error": "This coupon cannot be applied to cart total."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total cart value
        total_cart_amount = sum(item.product.sales_price * item.quantity for item in cart_items)

        # Check minimum purchase condition
        if coupon_instance.min_purchase and total_cart_amount < coupon_instance.min_purchase:
            return Response({
                "error": f"Cart total must be at least {coupon_instance.min_purchase} to use this coupon."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate discount
        discount_amount = 0
        if coupon_instance.type == "percent" and coupon_instance.discount_percentage:
            discount_amount = (total_cart_amount * coupon_instance.discount_percentage) / 100
            if coupon_instance.max_discount:
                discount_amount = min(discount_amount, coupon_instance.max_discount)
        elif coupon_instance.type == "amount" and coupon_instance.discount_amount:
            discount_amount = coupon_instance.discount_amount

        # Ensure discount does not exceed total
        discount_amount = min(discount_amount, total_cart_amount)
        final_total = total_cart_amount - discount_amount

        # Round amounts
        discount_amount = round(discount_amount, 2)
        final_total = round(final_total, 2)

        return Response({
            "detail": f"Coupon '{coupon_instance.code}' applied successfully.",
            "total_cart_amount": total_cart_amount,
            "discount_amount": discount_amount,
            "final_total": final_total,
            "coupon_type": coupon_instance.coupon_type,
            "discount_method": coupon_instance.type,
            "discount_percentage": coupon_instance.discount_percentage,
            "discount_amount_field": coupon_instance.discount_amount,
            "max_discount": coupon_instance.max_discount,
        }, status=status.HTTP_200_OK)
    




from .serializers import *

class SupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:  # Admin can see all tickets
            return SupportTicket.objects.all().order_by("-created_at")
        return SupportTicket.objects.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    

    @action(detail=True, methods=["get", "post"], url_path="messages")
    def messages(self, request, pk=None):
        """Handle GET (list) and POST (send) messages for a ticket"""
        ticket = self.get_object()

        if request.method == "GET":
            msgs = ticket.messages.all().order_by("created_at")
            serializer = TicketMessageSerializer(msgs, many=True)
            return Response(serializer.data)

        if request.method == "POST":
            serializer = TicketMessageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(ticket=ticket, sender=request.user)
            return Response(serializer.data, status=201)




from django.db.models import Q
from .models import product
from .serializers import product_serializer

class ProductSearchAPIView(ListAPIView):
    serializer_class = product_serializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        search_term = self.request.query_params.get("q")  # use ?q=shirt
        qs = product.objects.filter(is_active=True, sale_type__in = ["online", "both"])

         # Filter by customer pincode
          # Get pincode from ?pincode=XXXX in URL
        pincode = self.request.GET.get("pincode")

        if pincode:
            qs = qs.filter(vendor__coverages__pincode=pincode)
        user = self.request.user
        # Annotate favourites
        
    
        if search_term:
            qs = qs.filter(
                Q(name__icontains=search_term) |
                Q(brand_name__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(color__icontains=search_term) |
                Q(size__icontains=search_term) |
                Q(category__name__icontains=search_term) |
                Q(sub_category__name__icontains=search_term)
            )

        if user.is_authenticated:
            favs = Favourite.objects.filter(user=user, product=OuterRef('pk'))
            qs = qs.annotate(is_favourite=Exists(favs))
        else:
            qs = qs.annotate(is_favourite=Value(False, output_field=BooleanField()))

        return qs.distinct()



class StoreBySubCategoryView(APIView):
    """
    Get all vendor stores that have products in a given subcategory.
    """

    def get(self, request, *args, **kwargs):
        subcategory_id = request.query_params.get('subcategory_id')

        if not subcategory_id:
            return Response(
                {"error": "subcategory_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get distinct user IDs who have products in this subcategory
        user_ids = (
            product.objects.filter(sub_category_id=subcategory_id, is_active=True)
            .values_list('user_id', flat=True)
            .distinct()
        )

        # Get all vendor stores of those users
        stores = vendor_store.objects.filter(user_id__in=user_ids, is_active=True).distinct()

        serializer = VendorStoreSerializer(stores, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    


    

class StoreByCategoryView(APIView):
    """
    Get all vendor stores that have products in a given subcategory.
    """

    def get(self, request, *args, **kwargs):
        category_id = request.query_params.get('category_id')

        if not category_id:
            return Response(
                {"error": "category_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get distinct user IDs who have products in this category
        user_ids = (
            product.objects.filter(category_id=category_id, is_active=True)
            .values_list('user_id', flat=True)
            .distinct()
        )

        # Get all vendor stores of those users
        stores = vendor_store.objects.filter(user_id__in=user_ids, is_active=True).distinct()

        serializer = VendorStoreSerializer(stores, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    


from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import time
from django.db import connection

class HomeScreenView(APIView):
    """
    Return for each MainCategory:
      - categories (product_category list)
      - up to 6 random stores that sell products from those categories
      - up to 6 products (full details) from those categories

    Optimizations:
      - prefetch related sets for products (variants, addons, print variants)
      - fetch all reviews for the product batch in a single query and pass via context
      - fetch store list via user ids derived from product batch (fast)
    """

    def get(self, request, *args, **kwargs):
        start_total = time.time()
        response_data = []

        # Prefetch categories (these are product_category linked from MainCategory)
        main_categories = MainCategory.objects.prefetch_related(
            Prefetch('categories', queryset=product_category.objects.only('id', 'name', 'image'))
        ).only('id', 'name')

        for main_cat in main_categories:
            # direct categories under this main category
            categories_qs = main_cat.categories.all()  # already prefetched
            category_ids = list(categories_qs.values_list('id', flat=True))

            # -------------------------
            # Fetch product batch (limit 6) with related prefetches
            # -------------------------
            # Base product queryset for this main category
            products_qs = product.objects.filter(
                category_id__in=category_ids,
                is_active=True
            )

            # Apply pincode and distance logic like in ListProducts (using user's default address)
            user = request.user
            default_addr = Address.objects.filter(user=user, is_default=True).only('pincode', 'latitude', 'longitude').first()
            pincode = default_addr.pincode if default_addr else None
            if pincode:
                products_qs = products_qs.filter(user__coverages__pincode__code=pincode)

            products_qs = products_qs.select_related(
                'user', 'category', 'sub_category'
            ).prefetch_related(
                'variants',                           # product.variants (if you have related_name 'variants')
                'variants__size',                     # size on variants
                'product_addon__addon',              # product_addon -> addon
                'print_variants',                     # PrintVariant (related_name)
                'customize_print_variants',           # CustomizePrintVariant (related_name)
                'user__vendor_store'                  # prefetch vendor_store of the user
            )

            # Distance ordering using user's default address coordinates, fallback to random if not available
            lat = getattr(default_addr, 'latitude', None) if default_addr else None
            lng = getattr(default_addr, 'longitude', None) if default_addr else None
            if lat and lng:
                try:
                    lat_f = float(lat); lng_f = float(lng)
                    products_qs = products_qs.filter(
                        user__vendor_store__latitude__isnull=False,
                        user__vendor_store__longitude__isnull=False,
                    )
                    dist_expr = (
                        (Cast(F('user__vendor_store__latitude'), FloatField()) - Value(lat_f)) ** 2 +
                        (Cast(F('user__vendor_store__longitude'), FloatField()) - Value(lng_f)) ** 2
                    )
                    products_qs = products_qs.annotate(
                        _dist=ExpressionWrapper(dist_expr, output_field=FloatField())
                    ).order_by('_dist', 'id')[:6]
                except (ValueError, TypeError):
                    products_qs = products_qs.order_by('?')[:6]  # fallback to random
            else:
                products_qs = products_qs.order_by('?')[:6]  # random 6 products for this main category

            products = list(products_qs)  # evaluate

            product_ids = [p.id for p in products]

            # -------------------------
            # Fetch reviews for all products in batch — single query
            # -------------------------
            reviews_map = {}
            if product_ids:
                # Reviews are referenced via order_item__product in your serializer.
                # We fetch reviews that relate to these products in one shot.
                reviews_qs = Review.objects.filter(order_item__product_id__in=product_ids).select_related('order_item', 'user')
                # Serialize them (use existing ReviewSerializer)
                serialized_reviews = ReviewSerializer(reviews_qs, many=True, context={'request': request}).data

                # Build map: product_id -> list of review dicts
                for r in serialized_reviews:
                    # Try to get product_id from nested order_item if serializer provides it,
                    # else attempt to read it from r['order_item']['product'] etc.
                    # This depends on your ReviewSerializer output; adapt if needed.
                    prod_id = None
                    # safe extraction — best-effort
                    try:
                        prod_id = r.get('order_item', {}).get('product')
                    except Exception:
                        prod_id = None

                    # fallback: attempt to read order_item -> id and then map using DB (rare)
                    if not prod_id:
                        # try to pull from related objects on reviews_qs if needed
                        # since serialized_reviews order matches reviews_qs order, we can map by index,
                        # but easier is to re-query minimal mapping from DB (cheap for small batch)
                        pass

                    if prod_id:
                        reviews_map.setdefault(prod_id, []).append(r)

            # -------------------------
            # Stores: determine user_ids from products we fetched (fast)
            # then pick up to 6 random stores for this main category
            # -------------------------
            user_ids = set([p.user_id for p in products if p.user_id])
            stores_qs = vendor_store.objects.filter(user_id__in=user_ids, is_active=True).only('id', 'name', 'profile_image')
            stores_list = list(stores_qs)
            # pick random up to 6
            random_stores = random.sample(stores_list, min(6, len(stores_list)))
            # ✅ Get approved banner campaigns (latest or random as per your choice)
            stores_data = []
            for s in random_stores:
                store_banners = BannerCampaign.objects.filter(
                    user=s.user,   # 🔥 filter only for this store's owner
                    is_approved=True
                ).order_by('-created_at')[:5]

                # Use full serializer for banners so frontend gets redirect/product/store fields too
                store_banners_data = BannerCampaignSerializer(store_banners, many=True, context={'request': request}).data

                stores_data.append({
                    'id': s.id,
                    'name': s.name,
                    'profile_image': s.profile_image.url if s.profile_image else None,
                    'banners': store_banners_data  # serialized BannerCampaign data
                })

            # -------------------------
            # Serialize products using product_serializer but pass reviews_map in context
            # product_serializer must use reviews_map if present to avoid per-object queries
            # -------------------------
            # prepare serializer context
            ser_context = {'request': request, 'reviews_map': reviews_map}

            # Use your existing serializer but because we prefetched related objects, it should not do extra queries
            products_serialized = product_serializer(products, many=True, context=ser_context).data

            # -------------------------
            # build response payload for this main category
            # -------------------------
            response_data.append({
                "main_category_id": main_cat.id,
                "main_category_name": main_cat.name,
                "subcategories": [
                    {"id": c.id, "name": c.name, "image": c.image.url if c.image else None}
                    for c in categories_qs
                ],
                "stores": stores_data,
                "products": products_serialized
            })

        total_ms = (time.time() - start_total) * 1000.0
        # optional: print timings to server console for debug
        print(f"HomeScreenView total time: {total_ms:.2f} ms")

        return Response(response_data, status=status.HTTP_200_OK)



from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
 
class CustomerProductReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        order_item = serializer.validated_data['order_item']
        user = self.request.user

        # ✅ Block duplicate review
        if Review.objects.filter(order_item=order_item, user=user).exists():
            raise ValidationError("You have already reviewed this product.")

        # ✅ Ensure user actually purchased THIS exact order item
        if order_item.order.user != user:
            raise ValidationError("You can only review products you have purchased.")

        # ✅ Ensure order was delivered before review
        if order_item.status != "delivered":
            raise ValidationError("You can only review after delivery.")

        # ✅ Save safely
        serializer.save(user=user)



from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
        
class ProductRequestViewSet(viewsets.ModelViewSet):
    queryset = ProductRequest.objects.all().order_by("-created_at")
    serializer_class = ProductRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Return only requests created by the logged-in user
        return ProductRequest.objects.filter(user=self.request.user).order_by("-created_at")
    


from stream_chat import StreamChat  # ✅ Correct import

import os


from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from stream_chat import StreamChat
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from vendor.models import  vendor_store
from rest_framework.exceptions import ValidationError



class ChatInitAPIView(APIView):
    """
    Single API endpoint to:
    1. Generate a Stream token for the logged-in user
    2. Create or get a direct chat (customer ↔ vendor)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        api_key = getattr(settings, "STREAM_API_KEY", None)
        api_secret = getattr(settings, "STREAM_API_SECRET", None)
        if not api_key or not api_secret:
            return Response({"error": "Missing Stream API credentials"}, status=500)

        client = StreamChat(api_key=api_key, api_secret=api_secret)

        me = request.user
        user_id = str(me.id)
        app_role = "customer" if getattr(me, "is_customer", False) else ("vendor" if getattr(me, "is_vendor", False) else "user")

        # Create or update the Stream user
        client.upsert_user({
            "id": user_id,
            "name": me.username,
            "role": "user",
            "app_role": app_role,
        })

        # Create Stream token for frontend use
        token = client.create_token(user_id)

        # Optional: handle direct chat creation if other_user_id is provided
        other_user_id = request.data.get("other_user_id")
        channel_data = None

        if other_user_id:
            User = get_user_model()
            other = get_object_or_404(User, id=other_user_id)

            # Allow only customer↔vendor pairs
            is_allowed = (
                (getattr(me, "is_customer", False) and getattr(other, "is_vendor", False)) or
                (getattr(me, "is_vendor", False) and getattr(other, "is_customer", False))
            )
            if not is_allowed:
                return Response({"error": "Only customer↔vendor chats allowed"}, status=403)

            members = [user_id, str(other.id)]
            channel = client.channel("messaging", data={"members": members, "distinct": True})
            resp = channel.create(user_id)
            channel_id = resp.get("channel", {}).get("id")

            channel_data = {
                "channel_id": channel_id,
                "type": "messaging",
                "members": members,
            }

        return Response({
            "user": {
                "id": user_id,
                "username": me.username,
                "role": "user",
                "app_role": app_role,
            },
            "token": token,
            "api_key": api_key,
            "channel": channel_data,  # will be None if other_user_id not provided
        }, status=200)


# class StoreRatingViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = StoreRatingSerializer

#     def perform_create(self, serializer):
#         vendor_user_id = serializer.validated_data.pop('vendor_user_id', None)
#         if not vendor_user_id:
#             raise ValidationError({"vendor_user_id": "This field is required."})

#         try:
#             store = vendor_store.objects.get(user_id=vendor_user_id)
#         except vendor_store.DoesNotExist:
#             raise ValidationError({"vendor_user_id": "Store not found for this user"})

#         obj, created = StoreRating.objects.get_or_create(
#             user=self.request.user,
#             store=store,
#             defaults={
#                 'rating': serializer.validated_data.get('rating'),
#                 'comment': serializer.validated_data.get('comment'),
#             }
#         )
#         if not created:
#             obj.rating = serializer.validated_data.get('rating')
#             obj.comment = serializer.validated_data.get('comment')
#             obj.save(update_fields=['rating', 'comment', 'created_at'])
#         self._created_instance = obj

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         out = StoreRatingSerializer(self._created_instance)
#         return Response(out.data, status=201)