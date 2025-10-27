from django.forms import ValidationError
from django.shortcuts import render

# Create your views here.


from masters.models import MainCategory, product_category, product_subcategory
from users.models import *

from rest_framework import viewsets, permissions
from vendor.models import BannerCampaign, Post, Reel, SpotlightProduct, coupon, vendor_store
from vendor.serializers import BannerCampaignSerializer, PostSerializer, ReelSerializer, SpotlightProductSerializer, VendorStoreSerializer, coupon_serializer
from .models import *
from .serializers import AddressSerializer, CartSerializer, OrderSerializer

from rest_framework import viewsets, permissions

class CustomerOrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return orders for the logged-in user
        user = self.request.user
        return Order.objects.prefetch_related('items').filter(user=user).order_by('-id')

    def perform_create(self, serializer):
        # Automatically set the user when saving
        serializer.save(user=self.request.user)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

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
    queryset = vendor_store.objects.all()
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


from django.db.models import Exists, OuterRef, Value, BooleanField


class ListProducts(ListAPIView):
    serializer_class = product_serializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        user = self.request.user
        qs = product.objects.filter(is_active=True)

        # Filter by customer pincode
          # Get pincode from ?pincode=XXXX in URL
        pincode = self.request.GET.get("pincode")

        if pincode:
            qs = qs.filter(vendor__coverages__pincode=pincode)

        # Annotate favourites
        if user.is_authenticated:
            favs = Favourite.objects.filter(user=user, product=OuterRef('pk'))
            qs = qs.annotate(is_favourite=Exists(favs))
        else:
            qs = qs.annotate(is_favourite=Value(False, output_field=BooleanField()))

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
        products = Reel.objects.all()
        serializer = ReelSerializer(products, many=True)
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
        qs = product.objects.all()

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
        return qs



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
            product.objects.filter(sub_category_id=subcategory_id)
            .values_list('user_id', flat=True)
            .distinct()
        )

        # Get all vendor stores of those users
        stores = vendor_store.objects.filter(user_id__in=user_ids).distinct()

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
            product.objects.filter(category_id=category_id)
            .values_list('user_id', flat=True)
            .distinct()
        )

        # Get all vendor stores of those users
        stores = vendor_store.objects.filter(user_id__in=user_ids).distinct()

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
            products_qs = product.objects.filter(
                category_id__in=category_ids,
                is_active=True
            ).select_related(
                'user', 'category', 'sub_category'
            ).prefetch_related(
                'variants',                           # product.variants (if you have related_name 'variants')
                'variants__size',                     # size on variants
                'product_addon_set__addon',           # product_addon -> addon
                'print_variants',                     # PrintVariant (related_name)
                'customize_print_variants',           # CustomizePrintVariant (related_name)
                'user__vendor_store'                  # prefetch vendor_store of the user
            ).order_by('?')[:6]  # random 6 products for this main category

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

            # Serialize stores minimally (id, name, image)
            stores_data = [
                {
                    'id': s.id,
                    'name': s.name,
                    'image': s.profile_image.url if s.profile_image else None
                } for s in random_stores
            ]

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