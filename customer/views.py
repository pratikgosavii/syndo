from django.forms import ValidationError
from django.shortcuts import render

# Create your views here.


from masters.models import MainCategory, product_category, product_subcategory
from users.models import *

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from .payments.cashfree import create_order_for, refresh_order_status
from integrations.uengage import get_serviceability_for_order
from rest_framework.decorators import action
from .payments.cashfree import create_order_for, refresh_order_status
from vendor.models import BannerCampaign, Post, Reel, SpotlightProduct, coupon, vendor_store, VendorCoverage, NotificationCampaign, product
from masters.serializers import Pincode_serializer
from vendor.serializers import BannerCampaignSerializer, PostSerializer, ReelSerializer, SpotlightProductSerializer, VendorStoreSerializer, coupon_serializer, NotificationCampaignSerializer
from .models import *
from .serializers import AddressSerializer, CartSerializer, OrderSerializer
from types import SimpleNamespace

from rest_framework import viewsets, permissions

class CustomerOrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="check-delivery-availability")
    def check_delivery_availability(self, request):
        """
        Preflight check before taking payment: verifies serviceability/rider availability.
        Body should mirror order creation payload (needs items[0].product and address id).
        Only runs if vendor has auto_assign enabled.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        items = request.data.get("items") or []
        if not items or not isinstance(items, list):
            return Response({"detail": "No items provided"}, status=status.HTTP_400_BAD_REQUEST)

        first_item = items[0] or {}
        product_id = first_item.get("product")
        if not product_id:
            return Response({"detail": "Product id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            first_product = product.objects.select_related("user").get(id=product_id)
        except product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if vendor has auto_assign enabled
        vendor_user = first_product.user
        if vendor_user:
            from vendor.models import DeliveryMode
            delivery_mode = DeliveryMode.objects.filter(user=vendor_user).first()
            if not delivery_mode or not delivery_mode.is_auto_assign_enabled:
                # Auto-assign is disabled, skip serviceability check
                return Response({
                    "ok": True,
                    "message": "Auto-assign is disabled for this vendor. Delivery will be assigned manually.",
                    "auto_assign_enabled": False
                })

        address_id = request.data.get("address")
        if not address_id:
            return Response({"detail": "Address is required for delivery check"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            addr = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        # Log the coordinates being used for delivery check
        delivery_lat = getattr(addr, "latitude", None)
        delivery_lon = getattr(addr, "longitude", None)
        logger.info("=" * 80)
        logger.info("[check_delivery_availability] Delivery availability check triggered")
        logger.info("[check_delivery_availability] Address ID: %s", address_id)
        logger.info("[check_delivery_availability] Delivery coordinates: latitude=%s, longitude=%s", delivery_lat, delivery_lon)
        logger.info("[check_delivery_availability] User: %s (ID: %s)", request.user, request.user.id if request.user else "N/A")
        logger.info("[check_delivery_availability] Product ID: %s, Vendor: %s", product_id, vendor_user)

        delivery_type = request.data.get("delivery_type") or "self_pickup"
        logger.info("[check_delivery_availability] Delivery type: %s", delivery_type)
        
        if delivery_type == "instant_delivery":
            # Only instant_delivery needs rider check (and only if auto_assign is enabled)
            from integrations.uengage import get_serviceability_for_order
            # Build a lightweight order-like object for serviceability check
            temp_order = SimpleNamespace(
                order_id="TEMP",
                address=addr,
                items=SimpleNamespace(
                    select_related=lambda *args, **kwargs: SimpleNamespace(
                        first=lambda: SimpleNamespace(product=first_product)
                    )
                ),
            )

            try:
                logger.info("[check_delivery_availability] Calling get_serviceability_for_order with coordinates: lat=%s, lon=%s", delivery_lat, delivery_lon)
                svc_result = get_serviceability_for_order(temp_order)
                ok = svc_result.get("ok")
                svc = (svc_result.get("raw") or {}).get("serviceability") or {}
                rider_ok = svc.get("riderServiceAble")
                location_ok = svc.get("locationServiceAble")

                logger.info("[check_delivery_availability] Serviceability result: ok=%s, rider_ok=%s, location_ok=%s", ok, rider_ok, location_ok)

                if ok:
                    logger.info("[check_delivery_availability] Delivery boy available for coordinates: lat=%s, lon=%s", delivery_lat, delivery_lon)
                    logger.info("=" * 80)
                    return Response({
                        "ok": True,
                        "message": "Delivery boy available",
                        "serviceability": svc_result,
                        "auto_assign_enabled": True
                    })

                # Not serviceable
                if rider_ok is False:
                    msg = "No delivery boy present at the moment."
                    logger.warning("[check_delivery_availability] No delivery boy available for coordinates: lat=%s, lon=%s", delivery_lat, delivery_lon)
                elif location_ok is False:
                    msg = "Delivery location not serviceable."
                    logger.warning("[check_delivery_availability] Location not serviceable for coordinates: lat=%s, lon=%s", delivery_lat, delivery_lon)
                else:
                    msg = svc_result.get("message") or "Delivery not serviceable."
                    logger.warning("[check_delivery_availability] Delivery not serviceable for coordinates: lat=%s, lon=%s, reason: %s", delivery_lat, delivery_lon, msg)
                logger.info("=" * 80)
                return Response({
                    "ok": False,
                    "message": msg,
                    "serviceability": svc_result,
                    "auto_assign_enabled": True
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error("[check_delivery_availability] Exception checking delivery availability for coordinates: lat=%s, lon=%s, error: %s", delivery_lat, delivery_lon, str(e))
                logger.exception("[check_delivery_availability] Full exception traceback:")
                logger.info("=" * 80)
                return Response({
                    "ok": False,
                    "message": "Unable to confirm delivery availability. Please try again.",
                    "auto_assign_enabled": True
                }, status=status.HTTP_502_BAD_GATEWAY)
        else:
            # For non-instant delivery types (self_pickup, general_delivery), no rider check needed
            # Get delivery_mode for response
            from vendor.models import DeliveryMode
            delivery_mode = DeliveryMode.objects.filter(user=vendor_user).first() if vendor_user else None
            logger.info("[check_delivery_availability] Non-instant delivery type (%s) - no rider check needed. Coordinates: lat=%s, lon=%s", delivery_type, delivery_lat, delivery_lon)
            logger.info("=" * 80)
            return Response({
                "ok": True,
                "message": "Delivery check bypassed for non-instant delivery type.",
                "serviceability": {},
                "auto_assign_enabled": delivery_mode.is_auto_assign_enabled if delivery_mode else False
            })

    def create(self, request, *args, **kwargs):
        """
        Create order and immediately initiate Cashfree payment.
        Returns 201 with order payload + payment_session_id/payment_link.
        """
        # Validate items (required for all orders)
        items = request.data.get("items") or []
        if not items or not isinstance(items, list):
            return Response({"detail": "No items provided"}, status=status.HTTP_400_BAD_REQUEST)
        first_item = items[0] or {}
        product_id = first_item.get("product")
        if not product_id:
            return Response({"detail": "Product id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            first_product = product.objects.select_related("user").get(id=product_id)
        except product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Guard: prevent order placement when the vendor store is closed (only for instant_delivery)
        delivery_type = request.data.get("delivery_type") or "self_pickup"
        if delivery_type == "instant_delivery":
            store = vendor_store.objects.filter(user=first_product.user).first()
            if store:
                if not VendorStoreSerializer().get_is_store_open(store):
                    return Response({"detail": "Store is close now"}, status=status.HTTP_400_BAD_REQUEST)

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
        from vendor.models import DeliverySettings, vendor_store, DeliveryDiscount
        from vendor.serializers import DeliveryDiscountSerializer
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
            else:
                # self_pickup or on_shop_order => no shipping
                shipping_fee = Decimal("0.00")
        
        # Get vendor's delivery discount
        delivery_discount = None
        if vendor_user:
            try:
                delivery_discount = DeliveryDiscount.objects.filter(user=vendor_user).first()
            except Exception:
                pass
        
        # Serialize delivery discount if exists
        delivery_discount_data = None
        if delivery_discount:
            delivery_discount_data = DeliveryDiscountSerializer(delivery_discount).data
        
        return Response(
            {   
                "delivery_type": delivery_type,
                "shipping_fee": str(shipping_fee),
                "delivery_days" : str(ds.general_delivery_days) if ds else None,
                "instant_order_prep_time" : str(ds.instant_order_prep_time) if ds else None,
                "distance_km": str(distance_km) if distance_km is not None else None,
                "delivery_discount": delivery_discount_data,
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
        Get all Return/Exchange requests of logged-in user with full product details
        """
        from vendor.models import Offer
        from vendor.serializers import OfferSerializer

        queryset = Offer.objects.filter(request__user=request.user).order_by('-created_at')
        serializer = OfferSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class OnlineOrderInvoiceAPIView(APIView):
    """
    Generate PDF invoice for online orders
    Similar to POS invoice generation but for online orders
    """
    permission_classes = [permissions.AllowAny]  # Allow access via order_id

    def get(self, request, order_id=None):
        """
        Return online order invoice PDF
        """
        from django.http import HttpResponse
        from django.template.loader import get_template
        from django.conf import settings
        import requests
        from num2words import num2words
        from decimal import Decimal
        from customer.models import Order, OrderItem
        from vendor.models import vendor_store, CompanyProfile

        # Accept order_id from URL or query params
        if order_id is None:
            order_id = request.query_params.get("id") if hasattr(request, "query_params") else request.GET.get("id")
        if not order_id:
            return Response({"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get order with related data
        try:
            order = (
                Order.objects
                .prefetch_related('items__product')
                .select_related('user', 'address')
                .get(id=order_id)
            )
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get vendor information from first order item
        first_item = order.items.first()
        if not first_item:
            return Response({"error": "Order has no items"}, status=status.HTTP_400_BAD_REQUEST)

        vendor_user = first_item.product.user
        
        # Get vendor store and company profile
        store = vendor_store.objects.filter(user=vendor_user).first()
        company_profile = CompanyProfile.objects.filter(user=vendor_user).first()

        # Get customer address
        customer_address = order.address
        if not customer_address:
            return Response({"error": "Order has no address"}, status=status.HTTP_400_BAD_REQUEST)

        # Determine GST type (CGST if vendor/customer state matches else IGST)
        vendor_state_name = None
        if company_profile:
            # CompanyProfile.billing_state is CharField, state is ForeignKey - check both
            if hasattr(company_profile, 'billing_state') and company_profile.billing_state:
                vendor_state_name = str(company_profile.billing_state)
            elif hasattr(company_profile, 'state') and company_profile.state:
                if hasattr(company_profile.state, 'name'):
                    vendor_state_name = company_profile.state.name
                else:
                    vendor_state_name = str(company_profile.state)
        
        customer_state_name = None
        if customer_address.state:
            # Address.state is a CharField (string), not ForeignKey
            customer_state_name = str(customer_address.state)
        
        same_state = False
        if vendor_state_name and customer_state_name:
            same_state = vendor_state_name.strip().lower() == customer_state_name.strip().lower()
        store_gst = "cgst" if same_state else "igst"

        # Use existing order totals (no need to recalculate)
        item_total = Decimal(order.item_total or 0)
        tax_total = Decimal(order.tax_total or 0)
        shipping_fee = Decimal(order.shipping_fee or 0)
        delivery_discount = Decimal(order.delivery_discount_amount or 0)
        coupon = Decimal(order.coupon or 0)
        total_amount = Decimal(order.total_amount or 0)
        
        # Round total
        rounded_total = int(total_amount.to_integral_value(rounding="ROUND_HALF_UP"))
        round_off_value = float(Decimal(rounded_total) - total_amount)

        # Process items for display (HSN summary and item details for table)
        # Note: We only calculate display values here, totals come from order instance
        hsn_summary = {}
        total_quantity = 0
        total_sgst = Decimal(0)
        total_cgst = Decimal(0)
        total_igst = Decimal(0)
        items_with_tax = []

        for item in order.items.all():
            if not item.product:
                continue
            
            hsn = getattr(item.product, "hsn", None) or "N/A"
            sgst_rate = Decimal(getattr(item.product, "sgst_rate", None) or 9)
            cgst_rate = Decimal(getattr(item.product, "cgst_rate", None) or 9)
            
            # Use price and quantity from order item (already stored)
            unit_price = Decimal(item.price or 0)
            quantity = int(item.quantity or 0)
            taxable_val = unit_price * quantity

            # Build HSN summary for display
            if hsn not in hsn_summary:
                hsn_summary[hsn] = {"taxable_value": Decimal(0), "sgst_rate": sgst_rate, "cgst_rate": cgst_rate}
            hsn_summary[hsn]["taxable_value"] += taxable_val

            # Calculate tax amounts for display only
            sgst_amt = (taxable_val * sgst_rate / Decimal(100)).quantize(Decimal("0.01"))
            cgst_amt = (taxable_val * cgst_rate / Decimal(100)).quantize(Decimal("0.01"))
            total_sgst += sgst_amt
            total_cgst += cgst_amt
            
            if same_state:
                item_tax = sgst_amt + cgst_amt
            else:
                item_tax = (taxable_val * Decimal(getattr(item.product, "gst", 0) or 0) / Decimal(100)).quantize(Decimal("0.01"))
                total_igst += item_tax
            
            total_quantity += quantity

            items_with_tax.append({
                "name": getattr(item.product, "name", "N/A"),
                "hsn": hsn,
                "price": float(unit_price),
                "quantity": quantity,
                "taxable_value": float(taxable_val),
                "sgst_percent": float(sgst_rate),
                "cgst_percent": float(cgst_rate),
                "sgst_amount": float(sgst_amt),
                "cgst_amount": float(cgst_amt),
                "igst_percent": float(getattr(item.product, "gst", 0) or 0),
                "igst_amount": float(item_tax) if not same_state else 0.0,
                "total_with_tax": float(taxable_val + item_tax),
            })

        # Calculate HSN summary totals for display
        for hsn, data in hsn_summary.items():
            data["sgst_amount"] = (data["taxable_value"] * data["sgst_rate"] / Decimal(100)).quantize(Decimal("0.01"))
            data["cgst_amount"] = (data["taxable_value"] * data["cgst_rate"] / Decimal(100)).quantize(Decimal("0.01"))
            data["total_tax"] = (data["sgst_amount"] + data["cgst_amount"]).quantize(Decimal("0.01"))
            data["igst_rate"] = (data["sgst_rate"] + data["cgst_rate"]).quantize(Decimal("0.01"))
            data["igst_amount"] = data["total_tax"]

        # Convert to INR format: "Rupees [amount] Only"
        try:
            # Use num2words with INR currency
            amount_words = num2words(rounded_total, lang='en_IN').title()
            total_in_words = f"Rupees {amount_words} Only"
        except Exception:
            # Fallback if num2words fails
            total_in_words = f"Rupees {rounded_total} Only"

        # Calculate shipping tax for display (assuming 18% GST on shipping)
        shipping_taxable = shipping_fee / Decimal("1.18") if shipping_fee > 0 else Decimal(0)
        shipping_cgst = Decimal(0)
        shipping_sgst = Decimal(0)
        shipping_igst = Decimal(0)
        
        if shipping_fee > 0:
            if same_state:
                # CGST + SGST (9% each)
                shipping_cgst = (shipping_taxable * Decimal("9") / Decimal("100")).quantize(Decimal("0.01"))
                shipping_sgst = (shipping_taxable * Decimal("9") / Decimal("100")).quantize(Decimal("0.01"))
            else:
                # IGST (18%)
                shipping_igst = (shipping_taxable * Decimal("18") / Decimal("100")).quantize(Decimal("0.01"))

        # Get invoice image URL from media folder
        from django.conf import settings
        invoice_image_url = None
        try:
            # Build full URL for invoice image in media folder
            invoice_image_path = "invoice_image.jpeg"
            if hasattr(settings, 'MEDIA_URL'):
                if request:
                    # Build full absolute URL for the image
                    scheme = 'https' if request.is_secure() else 'http'
                    host = request.get_host()
                    invoice_image_url = f"{scheme}://{host}{settings.MEDIA_URL}{invoice_image_path}"
                else:
                    invoice_image_url = f"{settings.MEDIA_URL}{invoice_image_path}"
        except Exception:
            pass

        # Prepare context - use order fields directly where available
        context = {
            "order": order,
            "company_profile": company_profile,
            "store": store,
            "customer_address": customer_address,
            "vendor_user": vendor_user,
            "total_amount": float(total_amount),  # From order.total_amount
            "rounded_total": rounded_total,
            "round_off_value": round_off_value,
            "hsn_summary": hsn_summary.items(),
            "total_in_words": total_in_words,
            "total_tax": float(tax_total),  # From order.tax_total
            "tax_total": float(tax_total),  # Add tax_total for template check
            "store_gst": store_gst,
            "sum_taxable": float(item_total),  # From order.item_total
            "sum_sgst": float(total_sgst.quantize(Decimal("0.01"))),
            "sum_cgst": float(total_cgst.quantize(Decimal("0.01"))),
            "sum_igst": float(total_igst.quantize(Decimal("0.01"))),
            "total_quantity": total_quantity,
            "item_total": float(item_total),  # From order.item_total
            "tax_total": float(tax_total),  # From order.tax_total
            "shipping_fee": float(shipping_fee),  # From order.shipping_fee
            "shipping_cgst": float(shipping_cgst),
            "shipping_sgst": float(shipping_sgst),
            "shipping_igst": float(shipping_igst),
            "delivery_discount": float(delivery_discount),  # From order.delivery_discount_amount
            "coupon": float(coupon),  # From order.coupon
            "items_with_tax": items_with_tax,
            "payment_mode": order.payment_mode,  # From order
            "is_paid": order.is_paid,  # From order
            "invoice_image": invoice_image_url,  # Invoice image URL
        }

        # Render template to HTML string and convert to PDF
        template_name = "customer_invoice/online_order_invoice.html"
        template = get_template(template_name)
        html_content = template.render(context, request._request if hasattr(request, "_request") else request)

        # Generate PDF using html2pdf.app API
        try:
            api_response = requests.post(
                "https://api.html2pdf.app/v1/generate",
                json={
                    "html": html_content,
                    "apiKey": getattr(settings, "HTML2PDF_API_KEY", ""),
                    "options": {"printBackground": True, "margin": "1cm", "pageSize": "A4"},
                },
                timeout=30,
            )

            if api_response.status_code == 200:
                response = HttpResponse(api_response.content, content_type="application/pdf")
                filename = f"online_order_invoice_{order.order_id}.pdf"
                response["Content-Disposition"] = f'inline; filename="{filename}"'
                return response
            else:
                return Response(
                    {"error": "Error generating PDF", "details": api_response.text},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            return Response(
                {"error": "Error generating PDF", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@csrf_exempt
def cashfree_webhook(request):
    """
    Cashfree webhook to update order status.
    Expects JSON body and header 'x-webhook-signature' (base64 of HMAC-SHA256).
    """
    import logging
    import sys
    from datetime import datetime
    
    # Get logger - try specific logger first, fallback to root logger
    logger = logging.getLogger("cashfree_webhook")
    root_logger = logging.getLogger()
    
    # Also log to root logger as fallback
    def log_both(level, message):
        """Log to both cashfree_webhook logger and root logger"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        try:
            getattr(logger, level)(formatted_msg)
        except Exception:
            pass
        try:
            getattr(root_logger, level)(formatted_msg)
        except Exception:
            pass
        # Also print to stderr as ultimate fallback (this will always work)
        print(f"[CASHFREE_WEBHOOK] {formatted_msg}", file=sys.stderr, flush=True)
    
    from django.http import JsonResponse
    import base64
    import hashlib
    import hmac
    import json
    import os

    log_both("info", "=" * 80)
    log_both("info", "[CASHFREE_WEBHOOK] ========== WEBHOOK RECEIVED ==========")
    log_both("info", f"[CASHFREE_WEBHOOK] Method: {request.method}")
    log_both("info", f"[CASHFREE_WEBHOOK] Headers: {dict(request.headers)}")
    log_both("info", f"[CASHFREE_WEBHOOK] Remote Address: {request.META.get('REMOTE_ADDR', 'Unknown')}")
    log_both("info", f"[CASHFREE_WEBHOOK] Request Path: {request.path}")
    
    if request.method != "POST":
        log_both("warning", f"[CASHFREE_WEBHOOK] Invalid method: {request.method}")
        return JsonResponse({"detail": "method not allowed"}, status=405)

    try:
        raw = request.body
        payload = json.loads(raw.decode("utf-8"))
        log_both("info", f"[CASHFREE_WEBHOOK] Raw payload: {raw.decode('utf-8')}")
        log_both("info", f"[CASHFREE_WEBHOOK] Parsed payload: {json.dumps(payload, indent=2)}")
    except Exception as e:
        log_both("error", f"[CASHFREE_WEBHOOK] Invalid JSON: {e}")
        import traceback
        log_both("error", f"[CASHFREE_WEBHOOK] Traceback: {traceback.format_exc()}")
        return JsonResponse({"detail": "invalid json"}, status=400)

    signature = request.headers.get("x-webhook-signature") or request.headers.get("X-Webhook-Signature")
    timestamp = request.headers.get("x-webhook-timestamp") or request.headers.get("X-Webhook-Timestamp")
    webhook_version = request.headers.get("x-webhook-version") or request.headers.get("X-Webhook-Version")
    secret = os.getenv("CASHFREE_WEBHOOK_SECRET", "test_webhook_secret")
    log_both("info", f"[CASHFREE_WEBHOOK] Signature present: {bool(signature)}")
    log_both("info", f"[CASHFREE_WEBHOOK] Timestamp present: {bool(timestamp)}")
    log_both("info", f"[CASHFREE_WEBHOOK] Webhook version: {webhook_version}")
    log_both("info", f"[CASHFREE_WEBHOOK] Secret configured: {bool(secret)}")

    # Verify signature if present
    # Cashfree signature formats (based on webhook version):
    # - 2021-09-21 and earlier: signature = base64(hmac_sha256(secret, timestamp + raw_body_string))
    # - 2023-08-01: signature = base64(hmac_sha256(secret, timestamp + "." + body_string))
    # - Very old: signature = base64(hmac_sha256(secret, body_bytes))
    try:
        if signature:
            signature_verified = False
            raw_body_str = raw.decode('utf-8')
            
            # Try multiple signature formats to find the correct one
            computed_signatures = {}
            
            # Format 1: 2021-09-21 format (timestamp + raw_body_string, no dot separator)
            # This is the most common format for Cashfree webhooks
            if timestamp:
                message1 = f"{timestamp}{raw_body_str}"  # No dot separator for 2021-09-21
                computed1 = base64.b64encode(hmac.new(secret.encode("utf-8"), message1.encode("utf-8"), hashlib.sha256).digest()).decode()
                computed_signatures["2021-09-21_format"] = computed1
                log_both("info", f"[CASHFREE_WEBHOOK] Computed signature (2021-09-21: timestamp+body): {computed1[:30]}...")
            
            # Format 2: 2023-08-01 format (timestamp + "." + body_string)
            if webhook_version == "2023-08-01" and timestamp:
                message2 = f"{timestamp}.{raw_body_str}"
                computed2 = base64.b64encode(hmac.new(secret.encode("utf-8"), message2.encode("utf-8"), hashlib.sha256).digest()).decode()
                computed_signatures["2023-08-01_format"] = computed2
                log_both("info", f"[CASHFREE_WEBHOOK] Computed signature (2023-08-01: timestamp.body): {computed2[:30]}...")
            
            # Format 3: Body only (very old legacy format)
            computed3 = base64.b64encode(hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()).decode()
            computed_signatures["body_only"] = computed3
            log_both("info", f"[CASHFREE_WEBHOOK] Computed signature (body only): {computed3[:30]}...")
            
            # Format 4: 2021-09-21 with bytes (timestamp_bytes + body_bytes)
            if timestamp:
                message4 = timestamp.encode('utf-8') + raw
                computed4 = base64.b64encode(hmac.new(secret.encode("utf-8"), message4, hashlib.sha256).digest()).decode()
                computed_signatures["2021-09-21_bytes"] = computed4
                log_both("info", f"[CASHFREE_WEBHOOK] Computed signature (2021-09-21 bytes): {computed4[:30]}...")
            
            # Check which format matches
            for format_name, computed_sig in computed_signatures.items():
                if hmac.compare_digest(signature, computed_sig):
                    log_both("info", f"[CASHFREE_WEBHOOK] ✅ Signature verified successfully using format: {format_name}")
                    signature_verified = True
                    break
            
            if not signature_verified:
                log_both("error", f"[CASHFREE_WEBHOOK] ❌ Invalid signature. Received: {signature[:30]}...")
                log_both("error", f"[CASHFREE_WEBHOOK] Webhook version: {webhook_version}")
                log_both("error", f"[CASHFREE_WEBHOOK] Timestamp: {timestamp}")
                log_both("error", f"[CASHFREE_WEBHOOK] Tried formats: {list(computed_signatures.keys())}")
                log_both("error", f"[CASHFREE_WEBHOOK] Full received signature: {signature}")
                log_both("error", f"[CASHFREE_WEBHOOK] Body length: {len(raw)} bytes, Body preview: {raw_body_str[:100]}...")
                
                # Show computed signatures for debugging
                log_both("error", f"[CASHFREE_WEBHOOK] Computed signatures:")
                for fmt, sig in computed_signatures.items():
                    log_both("error", f"[CASHFREE_WEBHOOK]   {fmt}: {sig[:40]}...")
                
                # Check if webhook secret might be wrong
                log_both("warning", f"[CASHFREE_WEBHOOK] ⚠️  Signature mismatch. Possible causes:")
                log_both("warning", f"[CASHFREE_WEBHOOK]    1. CASHFREE_WEBHOOK_SECRET might be incorrect or not set")
                log_both("warning", f"[CASHFREE_WEBHOOK]    2. Webhook secret in Cashfree dashboard doesn't match environment variable")
                log_both("warning", f"[CASHFREE_WEBHOOK]    3. Using default 'test_webhook_secret' - need to set actual secret")
                
                # In sandbox/test mode, proceed anyway but log the error
                # For production, you should return 401 here
                # return JsonResponse({"detail": "invalid signature"}, status=401)
                log_both("warning", "[CASHFREE_WEBHOOK] ⚠️  Proceeding in test mode despite signature mismatch")
        else:
            log_both("warning", "[CASHFREE_WEBHOOK] No signature present, skipping verification")
    except Exception as e:
        log_both("warning", f"[CASHFREE_WEBHOOK] Signature verification error (proceeding): {e}")
        import traceback
        log_both("warning", f"[CASHFREE_WEBHOOK] Traceback: {traceback.format_exc()}")
        pass  # if missing headers, proceed best-effort in sandbox

    # Check webhook event type
    event_type = payload.get("event") or payload.get("type")
    log_both("info", f"[CASHFREE_WEBHOOK] Event type: {event_type}")
    
    # Handle non-payment webhooks (like LOW_BALANCE_ALERT, etc.)
    # List of known non-payment events that should be acknowledged but not processed
    non_payment_events = [
        "LOW_BALANCE_ALERT", "BALANCE_ALERT", "SETTLEMENT", "REFUND", 
        "VENDOR_CREATED", "VENDOR_UPDATED", "VENDOR_VERIFIED"
    ]
    
    # Payment-related events that should have order_id
    payment_events = ["PAYMENT", "ORDER", "PAYMENT_SUCCESS", "PAYMENT_FAILED", "PAYMENT_USER_DROPPED", "PAYMENT_CANCELLED"]
    
    # If it's a known non-payment event, acknowledge and return
    if event_type and event_type in non_payment_events:
        log_both("info", f"[CASHFREE_WEBHOOK] Non-payment webhook event: {event_type}. Acknowledging but not processing.")
        # Return success for non-payment webhooks (balance alerts, etc.) to prevent Cashfree from retrying
        return JsonResponse({
            "success": True, 
            "event": event_type, 
            "message": "Webhook received and acknowledged (non-payment event)"
        }, status=200)
    
    # If event_type exists but is not in payment_events and not in non_payment_events, it's unknown
    # We'll still try to process it if it has order_id, otherwise acknowledge it
    
    # Extract order_id and status robustly (for payment webhooks)
    order_id = (
        payload.get("order_id")
        or payload.get("data", {}).get("order", {}).get("order_id")
        or payload.get("data", {}).get("order_id")
        or payload.get("orderId")  # Alternative field name
    )
    status_cf = (
        payload.get("order_status")
        or payload.get("data", {}).get("order", {}).get("order_status")
        or payload.get("data", {}).get("payment", {}).get("payment_status")
        or payload.get("payment_status")
        or payload.get("status")
    )
    
    log_both("info", f"[CASHFREE_WEBHOOK] Extracted order_id: {order_id}")
    log_both("info", f"[CASHFREE_WEBHOOK] Extracted status: {status_cf}")

    # If no order_id, this might be a non-payment webhook or malformed payload
    if not order_id:
        log_both("warning", f"[CASHFREE_WEBHOOK] Missing order_id in payload. Event type: {event_type}. Payload keys: {list(payload.keys())}")
        # Return 200 for non-payment webhooks to avoid Cashfree retrying
        if event_type:
            log_both("info", f"[CASHFREE_WEBHOOK] Acknowledging non-payment webhook: {event_type}")
            return JsonResponse({"success": True, "event": event_type, "message": "Webhook received (non-payment event)"}, status=200)
        else:
            log_both("error", "[CASHFREE_WEBHOOK] Missing order_id and no event type. This might be a malformed payment webhook.")
            return JsonResponse({"detail": "missing order_id"}, status=400)

    # Update order by cashfree_order_id or order_id
    # Note: Cashfree may send order_id with slashes replaced by dashes (sanitized format)
    # Try multiple lookup strategies
    order = None
    try:
        # First try: exact match on cashfree_order_id
        order = Order.objects.filter(cashfree_order_id=order_id).first()
        if order:
            log_both("info", f"[CASHFREE_WEBHOOK] Order found by cashfree_order_id: {order.order_id} (ID: {order.id})")
        
        # Second try: exact match on order_id
        if not order:
            order = Order.objects.filter(order_id=order_id).first()
            if order:
                log_both("info", f"[CASHFREE_WEBHOOK] Order found by order_id: {order.order_id} (ID: {order.id})")
        
        # Third try: handle sanitized format (dashes vs slashes)
        sanitized_id = None
        if not order:
            # Try replacing dashes with slashes (in case webhook sends sanitized version)
            sanitized_id = order_id.replace("-", "/")
            order = Order.objects.filter(cashfree_order_id=sanitized_id).first()
            if not order:
                order = Order.objects.filter(order_id=sanitized_id).first()
            if order:
                log_both("info", f"[CASHFREE_WEBHOOK] Order found by sanitized order_id (dashes->slashes: {sanitized_id}): {order.order_id} (ID: {order.id})")
        
        # Fourth try: reverse sanitization (slashes to dashes)
        if not order:
            # Try replacing slashes with dashes (in case DB has dashes but webhook sends slashes)
            reverse_sanitized_id = order_id.replace("/", "-")
            if reverse_sanitized_id != order_id:  # Only if there were slashes to replace
                order = Order.objects.filter(cashfree_order_id=reverse_sanitized_id).first()
                if not order:
                    order = Order.objects.filter(order_id=reverse_sanitized_id).first()
                if order:
                    log_both("info", f"[CASHFREE_WEBHOOK] Order found by reverse sanitized order_id (slashes->dashes: {reverse_sanitized_id}): {order.order_id} (ID: {order.id})")
        
        if not order:
            log_both("error", f"[CASHFREE_WEBHOOK] Order not found for order_id: {order_id}")
            log_both("error", f"[CASHFREE_WEBHOOK] Tried: cashfree_order_id={order_id}, order_id={order_id}, sanitized={sanitized_id or 'N/A'}")
            # Log some sample order_ids for debugging
            sample_orders = Order.objects.filter(cashfree_order_id__isnull=False)[:5]
            if sample_orders.exists():
                log_both("info", f"[CASHFREE_WEBHOOK] Sample cashfree_order_ids in DB: {[o.cashfree_order_id for o in sample_orders]}")
            return JsonResponse({"detail": "order not found", "order_id": order_id}, status=404)
        
        log_both("info", f"[CASHFREE_WEBHOOK] Order details: order_id={order.order_id}, cashfree_order_id={order.cashfree_order_id}, status={order.status}, is_paid={order.is_paid}, cashfree_status={order.cashfree_status}")
    except Exception as e:
        log_both("error", f"[CASHFREE_WEBHOOK] Error looking up order: {e}")
        import traceback
        log_both("error", f"[CASHFREE_WEBHOOK] Traceback: {traceback.format_exc()}")
        return JsonResponse({"detail": "error looking up order", "error": str(e)}, status=500)

    if status_cf:
        old_status = order.cashfree_status
        order.cashfree_status = status_cf
        log_both("info", f"[CASHFREE_WEBHOOK] Updating cashfree_status: {old_status} -> {status_cf}")
        
        if str(status_cf).upper() in ("PAID", "SUCCESS", "CAPTURED"):
            log_both("info", f"[CASHFREE_WEBHOOK] Payment successful! Marking order as paid")
            order.is_paid = True
            order.payment_mode = "Cashfree"
        order.save(update_fields=["cashfree_status", "is_paid", "payment_mode"])
        log_both("info", f"[CASHFREE_WEBHOOK] Order updated successfully. New status: cashfree_status={order.cashfree_status}, is_paid={order.is_paid}")
    else:
        log_both("warning", f"[CASHFREE_WEBHOOK] No status found in payload, order not updated")

    log_both("info", "[CASHFREE_WEBHOOK] ========== WEBHOOK PROCESSED SUCCESSFULLY ==========")
    log_both("info", "=" * 80)

    return JsonResponse({"success": True, "order_id": order_id, "status": status_cf}, status=200)


@csrf_exempt
def delivery_webhook(request):
    """
    uEngage delivery webhook to receive real-time status updates.
    Expected payload:
    {
        "status": true,
        "data": {
            "taskId": "UENXXXXXX",
            "rider_name": "Ravit Kumar",
            "rider_contact": "991XXXX131",
            "latitude": "30.712518036454355",
            "longitude": "76.84761827964336",
            "rto_reason": "Customer denied"
        },
        "message": "Ok",
        "status_code": "DELIVERED"
    }
    """
    from django.http import JsonResponse
    import json
    import logging

    # Use dedicated uEngage webhook logger
    logger = logging.getLogger("uengage_webhook")
    root_logger = logging.getLogger()

    # Also log to root logger as fallback
    def log_both(level, message):
        """Log to both uengage_webhook logger and root logger, and print to stderr"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        try:
            getattr(logger, level)(formatted_msg)
        except Exception:
            # Fallback if specific logger fails
            getattr(root_logger, level)(formatted_msg)
        # Always print to stderr as ultimate fallback
        import sys
        print(f"[UENGAGE_WEBHOOK] {formatted_msg}", file=sys.stderr, flush=True)

    log_both("info", "=" * 80)
    log_both("info", "[UENGAGE_WEBHOOK] ========== WEBHOOK RECEIVED ==========")
    log_both("info", f"[UENGAGE_WEBHOOK] Method: {request.method}")
    log_both("info", f"[UENGAGE_WEBHOOK] Full URL: {request.build_absolute_uri()}")
    log_both("info", f"[UENGAGE_WEBHOOK] Path: {request.path}")
    log_both("info", f"[UENGAGE_WEBHOOK] Query String: {request.GET.urlencode()}")
    log_both("info", f"===========================================")
    log_both("info", f"[UENGAGE_WEBHOOK] Body: {request.body}")
    log_both("info", f"===========================================")


    try:
        body_str = request.body.decode('utf-8') if request.body else ''
        log_both("info", f"[UENGAGE_WEBHOOK] Body: {body_str}")
    except (UnicodeDecodeError, AttributeError) as e:
        log_both("info", f"[UENGAGE_WEBHOOK] Body (raw bytes): {request.body}")
        log_both("warning", f"[UENGAGE_WEBHOOK] Could not decode body as UTF-8: {e}")

    log_both("info", f"[UENGAGE_WEBHOOK] Remote Address: {request.META.get('REMOTE_ADDR', 'Unknown')}")
    log_both("info", f"[UENGAGE_WEBHOOK] Headers: {dict(request.headers)}")
    
    # Check Content-Length header to see if body should be present
    content_length = request.META.get('CONTENT_LENGTH', '0')
    log_both("info", f"[UENGAGE_WEBHOOK] Content-Length header: {content_length} bytes")
    
    # Also check request.META for raw body indicators
    log_both("info", f"[UENGAGE_WEBHOOK] Request META keys related to body: {[k for k in request.META.keys() if 'CONTENT' in k or 'BODY' in k or 'HTTP' in k]}")
    
    if request.method != "POST":
        log_both("warning", f"[UENGAGE_WEBHOOK] Invalid method: {request.method}")
        return JsonResponse({"detail": "method not allowed"}, status=405)

    # Read body once (request.body can only be read once in Django)
    try:
        # Try to read body multiple ways to debug
        raw = request.body
        raw_bytes_len = len(raw) if raw else 0
        
        # Also try reading from request._body if it exists (internal Django attribute)
        try:
            if hasattr(request, '_body'):
                log_both("info", f"[UENGAGE_WEBHOOK] Internal _body: {request._body}")
                internal_body_len = len(request._body) if request._body else 0
                log_both("info", f"[UENGAGE_WEBHOOK] Internal _body length: {internal_body_len} bytes")
        except Exception:
            pass
        
        # Try reading from request._stream if it exists
        try:
            if hasattr(request, '_stream'):
                stream_pos = getattr(request._stream, 'tell', lambda: 0)()
                log_both("info", f"[UENGAGE_WEBHOOK] Stream position: {stream_pos}")
        except Exception:
            pass
        
        raw_str = raw.decode("utf-8") if raw else ""
        log_both("info", f"[UENGAGE_WEBHOOK] Raw payload length: {raw_bytes_len} bytes")
        log_both("info", f"[UENGAGE_WEBHOOK] Raw payload hex (first 100 bytes): {raw.hex()[:200] if raw and raw_bytes_len > 0 else 'EMPTY'}")
        
        # If Content-Length says there should be a body but we have 0 bytes, log warning
        try:
            expected_length = int(content_length)
            if expected_length > 0 and raw_bytes_len == 0:
                log_both("error", f"[UENGAGE_WEBHOOK] ⚠️ MISMATCH: Content-Length header says {expected_length} bytes, but request.body is {raw_bytes_len} bytes!")
                log_both("error", f"[UENGAGE_WEBHOOK] ⚠️ Body may have been consumed by middleware or nginx!")
        except (ValueError, TypeError):
            pass
        
        # Print curl command equivalent
        try:
            # Build curl command in readable format
            full_url = request.build_absolute_uri()
            curl_lines = [f"curl -X {request.method} \\"]
            
            # Add headers (excluding some that curl handles automatically)
            skip_headers = {'connection', 'content-length', 'accept-encoding'}
            for header_name, header_value in request.headers.items():
                if header_name.lower() not in skip_headers:
                    # Escape single quotes in header value for shell
                    escaped_value = str(header_value).replace("'", "'\\''")
                    curl_lines.append(f"  -H '{header_name}: {escaped_value}' \\")
            
            # Add body if present
            if raw_str and raw_str.strip():
                # For JSON body, use --data-raw
                # Escape single quotes and backslashes for shell
                escaped_body = raw_str.replace("'", "'\\''").replace("\\", "\\\\")
                curl_lines.append(f"  --data-raw '{escaped_body}' \\")
            
            # Remove trailing backslash from last line
            if curl_lines[-1].endswith(' \\'):
                curl_lines[-1] = curl_lines[-1][:-2]
            
            # Add URL
            escaped_url = full_url.replace("'", "'\\''")
            curl_lines.append(f"  '{escaped_url}'")
            
            curl_cmd = "\n".join(curl_lines)
            log_both("info", f"[UENGAGE_WEBHOOK] ========== CURL COMMAND (Full Request) ==========")
            log_both("info", curl_cmd)
            log_both("info", f"[UENGAGE_WEBHOOK] =================================================")
        except Exception as e:
            log_both("warning", f"[UENGAGE_WEBHOOK] Could not build curl command: {e}")
            import traceback
            log_both("warning", f"[UENGAGE_WEBHOOK] Traceback: {traceback.format_exc()}")
        
    except Exception as e:
        log_both("error", f"[UENGAGE_WEBHOOK] Error reading request body: {e}")
        import traceback
        log_both("error", f"[UENGAGE_WEBHOOK] Traceback: {traceback.format_exc()}")
        return JsonResponse({"detail": "error reading request"}, status=400)

    try:
        
        if not raw_str or not raw_str.strip():
            log_both("warning", "[UENGAGE_WEBHOOK] Empty request body received - might be a health check from uEngage")
            log_both("info", "[UENGAGE_WEBHOOK] Returning 200 OK for empty body (health check)")
            return JsonResponse({"status": "ok", "message": "webhook endpoint active"}, status=200)
        
        log_both("info", f"[UENGAGE_WEBHOOK] Raw payload: {raw_str}")
        
        try:
            payload = json.loads(raw_str)
            log_both("info", f"[UENGAGE_WEBHOOK] Parsed payload: {json.dumps(payload, indent=2)}")
        except json.JSONDecodeError as json_err:
            log_both("error", f"[UENGAGE_WEBHOOK] Invalid JSON: {json_err}")
            log_both("error", f"[UENGAGE_WEBHOOK] Raw body content (first 1000 chars): {raw_str[:1000]}")
            log_both("error", f"[UENGAGE_WEBHOOK] Raw body repr: {repr(raw_str[:500])}")
            import traceback
            log_both("error", f"[UENGAGE_WEBHOOK] JSON Decode Traceback: {traceback.format_exc()}")
            return JsonResponse({"detail": "invalid json", "error": str(json_err)}, status=400)
    except Exception as e:
        log_both("error", f"[UENGAGE_WEBHOOK] Unexpected error parsing payload: {e}")
        import traceback
        log_both("error", f"[UENGAGE_WEBHOOK] Traceback: {traceback.format_exc()}")
        return JsonResponse({"detail": "error parsing request", "error": str(e)}, status=400)

    # Extract taskId and status_code
    data = payload.get("data", {})
    task_id = data.get("taskId") or data.get("task_id")
    status_code = payload.get("status_code", "").upper()
    rider_name = data.get("rider_name")
    rider_contact = data.get("rider_contact")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    rto_reason = data.get("rto_reason")

    if not task_id:
        log_both("warning", "[UENGAGE_WEBHOOK] Missing taskId in payload")
        return JsonResponse({"detail": "missing taskId"}, status=400)

    if not status_code:
        log_both("warning", "[UENGAGE_WEBHOOK] Missing status_code in payload")
        return JsonResponse({"detail": "missing status_code"}, status=400)

    log_both("info", f"[UENGAGE_WEBHOOK] Received webhook for taskId: {task_id}, status_code: {status_code}")
    log_both("info", f"[UENGAGE_WEBHOOK] Rider info - Name: {rider_name}, Contact: {rider_contact}, Location: ({latitude}, {longitude})")
    if rto_reason:
        log_both("info", f"[UENGAGE_WEBHOOK] RTO Reason: {rto_reason}")

    # Find order by uengage_task_id
    try:
        order = Order.objects.get(uengage_task_id=task_id)
        log_both("info", f"[UENGAGE_WEBHOOK] Order found: {order.order_id} (ID: {order.id})")
        log_both("info", f"[UENGAGE_WEBHOOK] Current order status: {order.status}")
    except Order.DoesNotExist:
        log_both("error", f"[UENGAGE_WEBHOOK] Order not found for taskId: {task_id}")
        return JsonResponse({"detail": "order not found"}, status=404)
    except Order.MultipleObjectsReturned:
        log_both("error", f"[UENGAGE_WEBHOOK] Multiple orders found for taskId: {task_id}")
        order = Order.objects.filter(uengage_task_id=task_id).first()

    # Map status_code to OrderItem status
    status_mapping = {
        "ACCEPTED": "ready_to_shipment",
        "ALLOTTED": "ready_to_deliver",
        "ARRIVED": "intransit",
        "DISPATCHED": "intransit",
        "ARRIVED_CUSTOMER_DOORSTEP": "ready_to_deliver",
        "DELIVERED": "delivered",
        "RTO_INIT": "cancelled",
        "RTO_COMPLETE": "cancelled",
    }

    new_item_status = status_mapping.get(status_code)
    if not new_item_status:
        log_both("warning", f"[UENGAGE_WEBHOOK] Unknown status_code: {status_code}")
        return JsonResponse({"detail": f"unknown status_code: {status_code}"}, status=400)
    
    log_both("info", f"[UENGAGE_WEBHOOK] Mapping status_code '{status_code}' to OrderItem status '{new_item_status}'")

    # Update all order items with the new status
    from django.db import transaction
    from integrations.uengage import notify_delivery_event
    
    with transaction.atomic():
        order_items = order.items.all()
        log_both("info", f"[UENGAGE_WEBHOOK] Found {order_items.count()} order item(s) to update")
        for item in order_items:
            previous_item_status = item.status
            log_both("info", f"[UENGAGE_WEBHOOK] OrderItem ID {item.id}: Previous status = '{previous_item_status}', New status = '{new_item_status}'")
            try:
                item.status = new_item_status
                item.save(update_fields=["status"])
                # Refresh from DB to verify save
                item.refresh_from_db()
                log_both("info", f"[UENGAGE_WEBHOOK] OrderItem ID {item.id}: Status updated to '{item.status}' (saved successfully, verified from DB)")
            except Exception as e:
                log_both("error", f"[UENGAGE_WEBHOOK] Failed to update OrderItem ID {item.id}: {e}")
                import traceback
                log_both("error", f"[UENGAGE_WEBHOOK] Traceback: {traceback.format_exc()}")
                raise  # Re-raise to rollback transaction
            
            # Send notification if item status changed to 'intransit' (out for delivery)
            if new_item_status == 'intransit' and previous_item_status != 'intransit':
                try:
                    from customer.serializers import send_order_status_notification
                    send_order_status_notification(order, 'intransit')
                    log_both("info", f"[UENGAGE_WEBHOOK] Sent 'out for delivery' notification to customer")
                except Exception as e:
                    log_both("warning", f"[UENGAGE_WEBHOOK] Failed to send out-for-delivery notification: {e}")

        # Store previous status BEFORE any changes
        previous_order_status = order.status
        
        # Update order status based on status_code
        if status_code == "ACCEPTED":
            order.status = "accepted"
        elif status_code in ("ALLOTTED", "ARRIVED", "DISPATCHED", "ARRIVED_CUSTOMER_DOORSTEP"):
            if order.status != "accepted":
                order.status = "accepted"  # Keep as accepted during transit
            # Send "out for delivery" notification for these status codes
            try:
                from customer.serializers import send_order_status_notification
                send_order_status_notification(order, 'intransit')
            except Exception as e:
                log_both("warning", f"[UENGAGE_WEBHOOK] Failed to send out-for-delivery notification: {e}")
        elif status_code == "DELIVERED":
            # All OrderItems have already been updated to "delivered" in the loop above
            # Refresh order items from DB to get the latest status
            order.items.all()  # Trigger queryset refresh
            all_delivered = all(item.status == "delivered" for item in order.items.all())
            log_both("info", f"[UENGAGE_WEBHOOK] Checking if all items are delivered: {all_delivered}")
            if all_delivered:
                order.status = "completed"
                log_both("info", f"[UENGAGE_WEBHOOK] All items delivered - marking order as completed")
                # For COD orders, mark as paid when order is completed
                payment_mode = str(getattr(order, "payment_mode", "") or "").strip().lower()
                if payment_mode in ("cod", "cash") and not order.is_paid:
                    order.is_paid = True
                    log_both("info", f"[UENGAGE_WEBHOOK] Order {order.order_id} marked as completed (COD/Cash) - setting is_paid=True")
            else:
                # Some items not yet delivered, but keep order status as accepted or ready_to_shipment
                log_both("info", f"[UENGAGE_WEBHOOK] Not all items delivered yet - keeping current order status: {order.status}")
        elif status_code in ("RTO_INIT", "RTO_COMPLETE"):
            # All OrderItems have already been updated to "cancelled" in the loop above
            order.status = "cancelled"
            log_both("info", f"[UENGAGE_WEBHOOK] RTO status received - marking order as cancelled")

        # Prepare update fields for Order
        update_fields = ["status"]
        if hasattr(order, "is_paid") and order.is_paid:
            update_fields.append("is_paid")
        log_both("info", f"[UENGAGE_WEBHOOK] Order status update: Previous = '{previous_order_status}', New = '{order.status}'")
        log_both("info", f"[UENGAGE_WEBHOOK] Updating Order fields: {update_fields}")
        
        # Save order status
        try:
            order.save(update_fields=update_fields)
            # Refresh from DB to verify save
            order.refresh_from_db()
            log_both("info", f"[UENGAGE_WEBHOOK] Order saved successfully. Verified status from DB: '{order.status}'")
            if hasattr(order, "is_paid"):
                log_both("info", f"[UENGAGE_WEBHOOK] Order is_paid status: {order.is_paid}")
        except Exception as e:
            log_both("error", f"[UENGAGE_WEBHOOK] Failed to update Order status: {e}")
            import traceback
            log_both("error", f"[UENGAGE_WEBHOOK] Traceback: {traceback.format_exc()}")
            raise

        # On first accept (ACCEPTED): create ledgers, reduce stock, assign serial/IMEI
        if status_code == "ACCEPTED" and previous_order_status != "accepted":
            try:
                from customer.serializers import on_order_accepted
                on_order_accepted(order)
                log_both("info", "[UENGAGE_WEBHOOK] on_order_accepted executed (ledgers, stock, serial/IMEI)")
            except Exception as e:
                log_both("warning", f"[UENGAGE_WEBHOOK] on_order_accepted failed: {e}")
        
        # Verify all OrderItem statuses were saved correctly
        log_both("info", f"[UENGAGE_WEBHOOK] Verifying all OrderItem statuses after save:")
        for item in order.items.all():
            item.refresh_from_db()  # Get fresh data from DB
            log_both("info", f"[UENGAGE_WEBHOOK]   - OrderItem ID {item.id}: status = '{item.status}' (expected: '{new_item_status}')")
            if item.status != new_item_status:
                log_both("warning", f"[UENGAGE_WEBHOOK]   ⚠️  OrderItem ID {item.id} status mismatch! Expected '{new_item_status}', got '{item.status}'")

        # Send order status notification if order status changed
        # NOTE: Skip notification for 'accepted' here since it's sent via notify_delivery_event below
        # to avoid duplicate notifications
        if order.status != previous_order_status and order.status != "accepted":
            log_both("info", f"[UENGAGE_WEBHOOK] Order status changed: {previous_order_status} -> {order.status}")
            try:
                from customer.serializers import send_order_status_notification
                send_order_status_notification(order, order.status, previous_order_status)
                log_both("info", f"[UENGAGE_WEBHOOK] Sent order status notification: {order.status}")
            except Exception as e:
                log_both("warning", f"[UENGAGE_WEBHOOK] Failed to send order status notification: {e}")

        # Send notifications based on status (SMS via uEngage templates)
        # For "accepted" status, also send push notification here to avoid duplicates
        notification_event_map = {
            "ACCEPTED": "packed",
            "ALLOTTED": "out_for_delivery",
            "ARRIVED": "out_for_delivery",
            "DISPATCHED": "out_for_delivery",
            "ARRIVED_CUSTOMER_DOORSTEP": "out_for_delivery",
            "DELIVERED": "delivered",
            "RTO_INIT": "cancelled",
            "RTO_COMPLETE": "cancelled",
        }
        
        event = notification_event_map.get(status_code)
        if event:
            # For "ACCEPTED" status, send push notification here (SMS is sent via notify_delivery_event)
            if status_code == "ACCEPTED" and order.status == "accepted" and previous_order_status != "accepted":
                try:
                    from customer.serializers import send_order_status_notification
                    send_order_status_notification(order, 'accepted', previous_order_status)
                    log_both("info", f"[UENGAGE_WEBHOOK] Sent 'accepted' push notification")
                except Exception as e:
                    log_both("warning", f"[UENGAGE_WEBHOOK] Failed to send 'accepted' push notification: {e}")
            # Get tracking link if available (could be from order or stored elsewhere)
            tracking_link = getattr(order.items.first(), "tracking_link", None) if order.items.exists() else None
            try:
                notify_delivery_event(
                    order,
                    event=event,
                    tracking_link=tracking_link,
                    rider_name=rider_name,
                    rider_phone=rider_contact
                )
            except Exception as e:
                log_both("warning", f"[UENGAGE_WEBHOOK] Failed to send notification: {e}")

        # Store rider information in Order model
        if rider_name or rider_contact or latitude or longitude:
            from decimal import Decimal, InvalidOperation
            update_fields = []
            if rider_name:
                order.uengage_rider_name = rider_name
                update_fields.append('uengage_rider_name')
            if rider_contact:
                order.uengage_rider_contact = rider_contact
                update_fields.append('uengage_rider_contact')
            if latitude:
                try:
                    order.uengage_rider_latitude = Decimal(str(latitude))
                    update_fields.append('uengage_rider_latitude')
                except (ValueError, TypeError, InvalidOperation):
                    log_both("warning", f"[UENGAGE_WEBHOOK] Invalid latitude value: {latitude}")
            if longitude:
                try:
                    order.uengage_rider_longitude = Decimal(str(longitude))
                    update_fields.append('uengage_rider_longitude')
                except (ValueError, TypeError, InvalidOperation):
                    log_both("warning", f"[UENGAGE_WEBHOOK] Invalid longitude value: {longitude}")
            
            if update_fields:
                order.save(update_fields=update_fields)
                log_both("info", f"[UENGAGE_WEBHOOK] ✅ Rider info stored in Order - Name: {rider_name}, Contact: {rider_contact}, Location: ({latitude}, {longitude})")
            else:
                log_both("info", f"[UENGAGE_WEBHOOK] Rider info received but not stored - Name: {rider_name}, Contact: {rider_contact}, Location: ({latitude}, {longitude})")

        if rto_reason:
            log_both("info", f"[UENGAGE_WEBHOOK] RTO Reason stored: {rto_reason}")

    log_both("info", f"[UENGAGE_WEBHOOK] Successfully updated order {order.order_id} to status {status_code}")
    log_both("info", "[UENGAGE_WEBHOOK] ========== WEBHOOK PROCESSED SUCCESSFULLY ==========")
    log_both("info", "=" * 80)
    return JsonResponse({"success": True, "order_id": order.order_id, "status": status_code}, status=200)


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

    def get_queryset(self):
        qs = vendor_store.objects.filter(is_active=True, is_online=True)
        
        # Filter by customer pincode, but exclude global suppliers from pincode check
        # Use the user's default address (is_default=True)
        user = self.request.user
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        if pincode:
            # Include stores from global suppliers OR stores matching pincode coverage
            # Global suppliers are visible everywhere, regular vendors only in their coverage area
            qs = qs.filter(
                Q(global_supplier=True) |  # Global suppliers: visible everywhere
                Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
            )
        
        return qs.distinct()

    def get(self, request, *args, **kwargs):
        if "id" in kwargs:
            # Track store visit when retrieving a single store
            self._track_store_visit(request, kwargs.get("id"))
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)    # GET /stores/
 
    def _track_store_visit(self, request, store_id):
        """Record a visit to the store"""
        try:
            from vendor.models import StoreVisit
            
            store = vendor_store.objects.get(id=store_id, is_active=True)
            
            # Only track if user is authenticated
            if request.user.is_authenticated:
                StoreVisit.objects.create(
                    store=store,
                    visitor=request.user
                )
                # Send notification to vendor
                try:
                    from customer.serializers import send_vendor_notification
                    vendor_user = store.user
                    visitor_name = request.user.id or request.user.mobile or f"User {request.user.id}"
                    send_vendor_notification(
                        vendor_user=vendor_user,
                        notification_type="shop_visit",
                        title="Shop Visit",
                        body=f"{visitor_name} visited your store",
                        data={"store_id": str(store.id), "visitor_id": str(request.user.id)}
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error sending shop visit notification: {e}")
        except vendor_store.DoesNotExist:
            pass  # Store doesn't exist or is inactive, skip tracking
        except Exception:
            pass  # Silently fail to not break the API
 


from vendor.models import product
from vendor.serializers import product_serializer
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from vendor.filters import ProductFilter


from django.db.models import Exists, OuterRef, Value, BooleanField, F, FloatField, ExpressionWrapper, Q
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
        # Filter by customer pincode, but exclude global suppliers from pincode check
        # Use the user's default address (is_default=True)
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        print(default_addr)
        if pincode:
            # Include products from global suppliers OR products matching pincode coverage
            # Global suppliers are visible everywhere, regular vendors only in their coverage area
            qs = qs.filter(
                Q(user__vendor_store__global_supplier=True) |  # Global suppliers: visible everywhere
                Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
            )

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
        qs = Post.objects.filter(
            user__vendor_store__is_active=True,
            user__vendor_store__is_online=True,
        )
        
        # Filter by customer pincode, but exclude global suppliers from pincode check
        # Use the user's default address (is_default=True)
        user = self.request.user
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        if pincode:
            # Include posts from global suppliers OR posts from vendors matching pincode coverage
            # Global suppliers are visible everywhere, regular vendors only in their coverage area
            qs = qs.filter(
                Q(user__vendor_store__global_supplier=True) |  # Global suppliers: visible everywhere
                Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
            )
        
        return qs.distinct()
    

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
                # Send notification to vendor (target_user is the vendor being followed)
                try:
                    from customer.serializers import send_vendor_notification
                    follower_name = request.user.id or request.user.username or f"User {request.user.id}"
                    send_vendor_notification(
                        vendor_user=target_user,
                        notification_type="follow",
                        title="New Follower",
                        body=f"{follower_name} started following you",
                        data={"follower_id": str(request.user.id)}
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error sending follow notification: {e}")
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
                # Send notification to vendor (target_user is the vendor being unfollowed)
                try:
                    from customer.serializers import send_vendor_notification
                    unfollower_name = request.user.id or request.user.username or f"User {request.user.id}"
                    send_vendor_notification(
                        vendor_user=target_user,
                        notification_type="unfollow",
                        title="Follower Removed",
                        body=f"{unfollower_name} unfollowed you",
                        data={"unfollower_id": str(request.user.id)}
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error sending unfollow notification: {e}")
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
        else:
            # Send notification to vendor when item is first added to cart
            try:
                from customer.serializers import send_vendor_notification
                vendor_user = product_instance.user
                customer_name = self.request.user.id or self.request.user.mobile or f"User {self.request.user.id}"
                send_vendor_notification(
                    vendor_user=vendor_user,
                    notification_type="cart_add",
                    title="Product Added to Cart",
                    body=f"{customer_name} added {product_instance.name} to their cart",
                    data={
                        "product_id": str(product_instance.id),
                        "customer_id": str(self.request.user.id),
                        "quantity": str(quantity)
                    }
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error sending cart add notification: {e}")

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

            # Remove instructions if present (instructions moved to file level)
            print_job_data.pop("instructions", None)

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
                    instructions=self.request.data.get(f"files[{index}].instructions"),
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
        
        # Send notification to vendor
        try:
            from customer.serializers import send_vendor_notification
            vendor_user = product_instance.user
            customer_name = request.user.username or request.user.mobile or f"User {request.user.id}"
            send_vendor_notification(
                vendor_user=vendor_user,
                notification_type="cart_add",
                title="Product Added to Cart",
                body=f"{customer_name} added {product_instance.name} to their cart",
                data={
                    "product_id": str(product_instance.id),
                    "customer_id": str(request.user.id),
                    "quantity": str(quantity)
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending cart add notification: {e}")

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

            # Remove instructions if present (instructions moved to file level)
            print_job_data.pop("instructions", None)

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
                    instructions=request.data.get(f"files[{index}].instructions"),
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
            # Send notification to vendor (product owner)
            try:
                from customer.serializers import send_vendor_notification
                from vendor.models import product
                product_instance = product.objects.get(id=product_id)
                vendor_user = product_instance.user
                liker_name = user.id or user.mobile or f"User {user.id}"
                send_vendor_notification(
                    vendor_user=vendor_user,
                    notification_type="product_like",
                    title="Product Liked",
                    body=f"{liker_name} liked your product {product_instance.name}",
                    data={
                        "product_id": str(product_id),
                        "liker_id": str(user.id)
                    }
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error sending product like notification: {e}")
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
        products = SpotlightProduct.objects.filter(
            user__vendor_store__is_active=True,
            user__vendor_store__is_online=True,
        )
        
        # Filter by customer pincode, but exclude global suppliers from pincode check
        # Use the user's default address (is_default=True)
        user = request.user
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        if pincode:
            # Include spotlight products from global suppliers OR from vendors matching pincode coverage
            # Global suppliers are visible everywhere, regular vendors only in their coverage area
            products = products.filter(
                Q(user__vendor_store__global_supplier=True) |  # Global suppliers: visible everywhere
                Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
            )
        
        serializer = SpotlightProductSerializer(products.distinct(), many=True, context={'request': request})
        return Response(serializer.data)


class reelsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reels = Reel.objects.filter(
            user__vendor_store__is_active=True,
            user__vendor_store__is_online=True,
        )
        
        # Filter by customer pincode, but exclude global suppliers from pincode check
        # Use the user's default address (is_default=True)
        user = request.user
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        if pincode:
            # Include reels from global suppliers OR reels from vendors matching pincode coverage
            # Global suppliers are visible everywhere, regular vendors only in their coverage area
            reels = reels.filter(
                Q(user__vendor_store__global_supplier=True) |  # Global suppliers: visible everywhere
                Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
            )
        
        serializer = ReelSerializer(reels.distinct(), many=True, context={'request': request})
        return Response(serializer.data)


class offersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Reel.objects.filter(
            user__vendor_store__is_active=True,
            user__vendor_store__is_online=True,
        )
        
        # Filter by customer pincode, but exclude global suppliers from pincode check
        # Use the user's default address (is_default=True)
        user = request.user
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        if pincode:
            # Include reels from global suppliers OR reels from vendors matching pincode coverage
            # Global suppliers are visible everywhere, regular vendors only in their coverage area
            products = products.filter(
                Q(user__vendor_store__global_supplier=True) |  # Global suppliers: visible everywhere
                Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
            )
        
        serializer = ReelSerializer(products.distinct(), many=True, context={'request': request})
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
        from django.db.models import Q
        
        # Get cart items for the user
        cart_items = Cart.objects.filter(user=request.user).select_related('product', 'product__user')
        
        # Get unique vendor IDs from cart products
        vendor_ids = set()
        if cart_items.exists():
            for item in cart_items:
                if item.product and item.product.user:
                    vendor_ids.add(item.product.user.id)
        
        # Filter coupons to include:
        # 1. Coupons from vendors whose products are in the cart
        # 2. customer_id logic: 
        #    - If customer_id is NULL/blank → return to all users
        #    - If customer_id is set → only return if it matches request.user.id
        now = timezone.now()
        
        # Base conditions that apply to all coupons
        base_conditions = Q(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        
        # Customer ID filter: 
        # - If customer_id is NULL/blank → return to all users (no restriction)
        # - If customer_id is set → only return if it matches request.user.id
        customer_filter = Q(customer_id__isnull=True) | Q(customer_id=request.user.id)
        
        # Only return coupons if cart has products from vendors
        if not vendor_ids:
            return Response({"coupons": [], "message": "Cart is empty"}, status=200)
        
        # Filter coupons from vendors whose products are in cart
        # AND apply customer_id filter
        coupons = coupon.objects.filter(
            user__id__in=vendor_ids
        ).filter(
            base_conditions & customer_filter
        ).distinct()

        serializer = coupon_serializer(coupons, many=True)
        return Response({"coupons": serializer.data}, status=200)

    def post(self, request):
        coupon_id = request.data.get("coupon_id")
        if not coupon_id:
            return Response({"error": "coupon_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        user, cart_items = self.get_cart_user(request.user)
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            coupon_instance = coupon.objects.get(user=user, id=coupon_id, is_active=True)
        except coupon.DoesNotExist:
            return Response({"error": "Invalid or inactive coupon"}, status=status.HTTP_404_NOT_FOUND)

        # Check validity dates
        if coupon_instance.start_date > timezone.now() or coupon_instance.end_date < timezone.now():
            return Response({"error": "Coupon is not valid at this time."}, status=status.HTTP_400_BAD_REQUEST)

        # Check customer_id: if set, must match request.user.id
        if coupon_instance.customer_id is not None:
            if coupon_instance.customer_id != request.user.id:
                return Response({"error": "This coupon is not available for your account."}, status=status.HTTP_403_FORBIDDEN)

      
        # Calculate total cart value
        total_cart_amount = sum(item.product.sales_price * item.quantity for item in cart_items)

        # Check minimum purchase condition
        if coupon_instance.min_purchase and total_cart_amount < coupon_instance.min_purchase:
            return Response({
                "error": f"Cart value is less to apply this coupon. Minimum cart value required is {coupon_instance.min_purchase}."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate discount
        discount_amount = 0
        if coupon_instance.type == "percent" and coupon_instance.discount_percentage:
            discount_amount = (total_cart_amount * coupon_instance.discount_percentage) / 100
            # Apply max_discount limit if set
            if coupon_instance.max_discount:
                discount_amount = min(discount_amount, coupon_instance.max_discount)
        elif coupon_instance.type == "amount" and coupon_instance.discount_amount:
            discount_amount = coupon_instance.discount_amount
            # Apply max_discount limit if set (for amount type coupons too)
            if coupon_instance.max_discount:
                discount_amount = min(discount_amount, coupon_instance.max_discount)

        # Ensure discount does not exceed cart total
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
        stores = vendor_store.objects.filter(user_id__in=user_ids, is_active=True, is_online=True).distinct()

        # Filter by customer pincode, but exclude global suppliers from pincode check
        # Use the user's default address (is_default=True)
        user = request.user
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        if pincode:
            # Include stores from global suppliers OR stores matching pincode coverage
            # Global suppliers are visible everywhere, regular vendors only in their coverage area
            stores = stores.filter(
                Q(global_supplier=True) |  # Global suppliers: visible everywhere
                Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
            )

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
        stores = vendor_store.objects.filter(user_id__in=user_ids, is_active=True, is_online=True).distinct()

        # Filter by customer pincode, but exclude global suppliers from pincode check
        # Use the user's default address (is_default=True)
        user = request.user
        default_addr = Address.objects.filter(user=user, is_default=True).first()
        pincode = default_addr.pincode if default_addr else None
        if pincode:
            # Include stores from global suppliers OR stores matching pincode coverage
            # Global suppliers are visible everywhere, regular vendors only in their coverage area
            stores = stores.filter(
                Q(global_supplier=True) |  # Global suppliers: visible everywhere
                Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
            )

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
                is_active=True,
                sale_type__in=["online", "both"],
                user__vendor_store__is_active=True,
                user__vendor_store__is_online=True,
            )

            # Apply pincode and distance logic like in ListProducts (using user's default address)
            user = request.user
            default_addr = Address.objects.filter(user=user, is_default=True).only('pincode', 'latitude', 'longitude').first()
            pincode = default_addr.pincode if default_addr else None
            if pincode:
                # Include products from global suppliers OR products matching pincode coverage
                # Global suppliers are visible everywhere, regular vendors only in their coverage area
                products_qs = products_qs.filter(
                    Q(user__vendor_store__global_supplier=True) |  # Global suppliers: visible everywhere
                    Q(user__coverages__pincode__code=pincode)      # Regular vendors: only in coverage area
                )
            
            # Filter out products from private catalog stores if user is not following
            from customer.models import Follower
            if user.is_authenticated:
                # Get all store owners the user is following
                following_store_user_ids = set(
                    Follower.objects.filter(follower=user)
                    .values_list('user_id', flat=True)
                )
                # Exclude products from private catalog stores where user is not following
                products_qs = products_qs.exclude(
                    Q(user__vendor_store__private_catalog=True) & 
                    ~Q(user_id__in=following_store_user_ids)
                )
            else:
                # Anonymous users: exclude all products from private catalog stores
                products_qs = products_qs.exclude(user__vendor_store__private_catalog=True)

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
            
            # Ensure unique products by ID (remove duplicates)
            seen_ids = set()
            unique_products = []
            for p in products:
                if p.id not in seen_ids:
                    seen_ids.add(p.id)
                    unique_products.append(p)
            products = unique_products

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
            stores_qs = vendor_store.objects.filter(user_id__in=user_ids, is_active=True).only('id', 'name', 'profile_image', 'private_catalog', 'user')
            stores_list = list(stores_qs)
            
            # Filter stores based on private_catalog setting
            # If store has private_catalog=True, only show if user is following that store
            filtered_stores = []
            if request.user.is_authenticated:
                # Get all stores the user is following (for private catalog check)
                following_store_user_ids = set(
                    Follower.objects.filter(follower=request.user)
                    .values_list('user_id', flat=True)
                )
                
                for store in stores_list:
                    # If store is private, check if user is following
                    if store.private_catalog:
                        if store.user_id in following_store_user_ids:
                            filtered_stores.append(store)
                        # else: skip this store (not following)
                    else:
                        # Public store, include it
                        filtered_stores.append(store)
            else:
                # Anonymous user: only show public stores (not private_catalog)
                filtered_stores = [s for s in stores_list if not s.private_catalog]
            
            # pick random up to 6 from filtered stores
            random_stores = random.sample(filtered_stores, min(6, len(filtered_stores))) if filtered_stores else []
            
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
        review = serializer.save(user=user)
        
        # Send notification to vendor (product owner)
        try:
            from customer.serializers import send_vendor_notification
            vendor_user = order_item.product.user
            reviewer_name = user.username or user.mobile or f"User {user.id}"
            rating = serializer.validated_data.get('rating', 0)
            send_vendor_notification(
                vendor_user=vendor_user,
                notification_type="review",
                title="New Review",
                body=f"{reviewer_name} left a {rating}-star review for {order_item.product.name}",
                data={
                    "product_id": str(order_item.product.id),
                    "review_id": str(review.id),
                    "rating": str(rating),
                    "reviewer_id": str(user.id)
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending review notification: {e}")



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

            # Get vendor store name if other user is a vendor
            other_name = other.username
            if getattr(other, "is_vendor", False):
                try:
                    store = vendor_store.objects.get(user=other)
                    other_name = store.name if store.name else other.username
                except vendor_store.DoesNotExist:
                    other_name = other.username

            # Create or update the Stream user for the other user (vendor)
            other_user_id_str = str(other.id)
            other_app_role = "customer" if getattr(other, "is_customer", False) else ("vendor" if getattr(other, "is_vendor", False) else "user")
            
            client.upsert_user({
                "id": other_user_id_str,
                "name": other_name,  # Use vendor store name if vendor, otherwise username
                "role": "user",
                "app_role": other_app_role,
            })

            members = [user_id, other_user_id_str]
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


class VendorPincodesAPIView(APIView):
    """
    API to return all pincodes covered by a specific vendor.
    GET /customer/vendor-pincodes/?vendor_id=<user_id>
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vendor_id = request.query_params.get('vendor_id')
        
        if not vendor_id:
            return Response(
                {"detail": "vendor_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vendor_id = int(vendor_id)
        except ValueError:
            return Response(
                {"detail": "vendor_id must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all VendorCoverage entries for this vendor
        coverages = VendorCoverage.objects.filter(
            user_id=vendor_id
        ).select_related('pincode')
        
        # Extract pincodes and serialize them
        pincodes = [coverage.pincode for coverage in coverages]
        serializer = Pincode_serializer(pincodes, many=True)
        
        return Response({
            "vendor_id": vendor_id,
            "pincodes": serializer.data,
            "count": len(serializer.data)
        }, status=status.HTTP_200_OK)


class VendorCampaignsAPIView(APIView):
    """
    API to return all campaigns (Banner and Notification) from all vendors.
    GET /customer/vendor-campaigns/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all banner campaigns (only approved ones for customers)
        from django.utils import timezone
        from datetime import timedelta
        
        # Calculate date 7 days ago
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Filter notification campaigns to only include those created in the last 7 days and not soft-deleted
        notification_campaigns = NotificationCampaign.objects.filter(
            created_at__gte=seven_days_ago,
            is_deleted=False  # Exclude soft-deleted campaigns from customer view
        ).select_related('product', 'store', 'user').order_by('-created_at')
        
        # Serialize the campaigns
        notification_serializer = NotificationCampaignSerializer(notification_campaigns, many=True, context={'request': request})
        
        return Response({
            "notification_campaigns": notification_serializer.data,
           
        }, status=status.HTTP_200_OK)