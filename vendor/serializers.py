from rest_framework import serializers
from vendor.models import ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "created_at"]
from users.serializer import UserProfileSerializer
from .models import *
from masters.serializers import *



class coupon_serializer(serializers.ModelSerializer):
    class Meta:
        model = coupon
        fields = '__all__'




class vendor_customers_serializer(serializers.ModelSerializer):
    
    state_details = StateSerializer(source = "state", read_only = True)
    class Meta:
        model = vendor_customers
        fields = '__all__'
        read_only_fields = ['user']  



class vendor_vendors_serializer(serializers.ModelSerializer):
    state_details = StateSerializer(source = "state", read_only = True)
    
    class Meta:
        model = vendor_vendors
        fields = '__all__'
        read_only_fields = ['user']  



class ProductSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSettings
        exclude = ['user']


class AddonSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = addon
        fields = '__all__'

class ProductAddonSerializer(serializers.ModelSerializer):
    addon_details = AddonSerializer(source = "addon", read_only = True)
    class Meta:
        model = product_addon
        fields = '__all__'



class OnlineStoreSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineStoreSetting
        fields = '__all__'
        read_only_fields = ['user']  


class CompanyProfileSerializer(serializers.ModelSerializer):
    state_details = StateSerializer(source = "state", read_only = True)
    shipping_state_details = StateSerializer(source="shipping_state", read_only=True)


    class Meta:
        model = CompanyProfile
        fields = '__all__'
        read_only_fields = ['user']


class DeliveryDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryDiscount
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']



class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseItem
        fields = ['product', 'product_name', 'quantity', 'price', 'total', 'amount', 'tax_amount', 'total_with_tax']  # include all needed fields including GST
        read_only_fields = ['total', 'amount', 'tax_amount', 'total_with_tax', 'product_name']  # these are calculated automatically
    
    def get_product_name(self, obj):
        """Return the product name"""
        if obj.product:
            return obj.product.name
        return None

    





class vendor_serializer(serializers.ModelSerializer):
    class Meta:
        model = vendor_vendors
        fields = '__all__'
        read_only_fields = ['user']




class StoreWorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreWorkingHour
        fields = ['day', 'open_time', 'close_time', 'is_open']




    


    
        

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'



class CashBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBalance
        fields = ['balance', 'updated_at']



class OnlineOrderLedgerSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    order_item_id = serializers.IntegerField(source='order_item.id', read_only=True)

    class Meta:
        model = OnlineOrderLedger
        fields = [
            'id', 'order_item_id', 'order_id', 'product', 'product_name',
            'quantity', 'amount', 'status', 'note', 'created_at'
        ]
        read_only_fields = fields


class ExpenseLedgerSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    expense_id = serializers.IntegerField(source='expense.id', read_only=True)

    class Meta:
        model = ExpenseLedger
        fields = [
            'id', 'expense_id', 'expense', 'category', 'category_name',
            'amount', 'payment_method', 'bank', 'bank_name',
            'expense_date', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class vendor_bank_serializer(serializers.ModelSerializer):
    class Meta:
        model = vendor_bank
        fields = '__all__'


class CashTransferSerializer(serializers.ModelSerializer):
   
    current_balance = serializers.SerializerMethodField()  # <-- FIX
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        model = CashTransfer
        fields = ['id', 'bank_account', 'amount', 'created_at', 'current_balance']
        read_only_fields = ['created_at', 'current_balance']

    def get_current_balance(self, obj):
        balance_obj, _ = CashBalance.objects.get_or_create(user=obj.user)
        return str(balance_obj.balance)



class BankTransferSerializer(serializers.ModelSerializer):
    from_bank = vendor_bank_serializer(read_only=True)
    to_bank = vendor_bank_serializer(read_only=True)

    from_bank_id = serializers.PrimaryKeyRelatedField(
        queryset=vendor_bank.objects.all(), source="from_bank", write_only=True
    )
    to_bank_id = serializers.PrimaryKeyRelatedField(
        queryset=vendor_bank.objects.all(), source="to_bank", write_only=True
    )

    class Meta:
        model = BankTransfer
        fields = [
            "id",
            "user",
            "from_bank",
            "to_bank",
            "from_bank_id",
            "to_bank_id",
            "amount",
            "date",
            "notes",
        ]
        read_only_fields = ["id", "date", "user", "from_bank", "to_bank"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
    
    
class PrintVariantSerializer(serializers.ModelSerializer):
    color_type_display = serializers.CharField(source='get_color_type_display', read_only=True)
    sided_display = serializers.CharField(source='get_sided_display', read_only=True)
    paper_display = serializers.CharField(source='get_paper_display', read_only=True)

    class Meta:
        model = PrintVariant
        fields = [
            'id',
            'product',
            'paper',
            'paper_display',
            'color_type',
            'color_type_display',
            'sided',
            'sided_display',
            'min_quantity',
            'max_quantity',
            'price',
        ]


class CustomizePrintVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizePrintVariant
        exclude = ['product']

class ProductVariantSerializer(serializers.ModelSerializer):
    size_detials = size_serializer(source='size', read_only=True)

    avg_rating = serializers.SerializerMethodField()    
    reviews = serializers.SerializerMethodField()

    is_favourite = serializers.SerializerMethodField()  # ✅ dynamic now

    class Meta:
        model = product
        fields = '__all__'
        # Prevent DRF from trying to bind M2M field from request (we handle files manually)
        extra_kwargs = {
            'gallery_images': {'read_only': True},
        }

    def _get_reviews_queryset(self, obj):
        """ Reuse same queryset to avoid double DB hit """
        if not hasattr(self, '_cached_reviews'):
            self._cached_reviews = Review.objects.filter(order_item__product=obj)
        return self._cached_reviews

    def get_reviews(self, obj):
        from customer.serializers import ReviewSerializer
        reviews = self._get_reviews_queryset(obj)
        return ReviewSerializer(reviews, many=True).data

    def get_avg_rating(self, obj):
        from django.db.models import Avg
        reviews = self._get_reviews_queryset(obj)
        avg = reviews.aggregate(avg=Avg('rating'))['avg']
        return round(avg, 1) if avg else 0.0
    

    def get_is_favourite(self, obj):
        from customer.models import Favourite

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        # ✅ Cache favourite IDs (only one DB query per request)
        if not hasattr(self, "_user_fav_ids"):
            self._user_fav_ids = set(
                Favourite.objects.filter(user=request.user)
                .values_list("product_id", flat=True)
            )

        return obj.id in self._user_fav_ids


class VendorStoreSerializer2(serializers.ModelSerializer):
    is_store_open = serializers.SerializerMethodField()

    class Meta:
        model = vendor_store
        fields = '__all__'
    
    def get_is_store_open(self, obj):
        # Store-level active check ✅
        if not obj.is_offline:
            return False

        now = timezone.localtime()
        # Get day name - try both lowercase and capitalized to handle case mismatch
        today_lower = now.strftime('%A').lower()  # 'monday'
        today_capitalized = now.strftime('%A')  # 'Monday'
        current_time = now.time()

        # Try both lowercase and capitalized day names to handle any case mismatch
        working_hour = obj.user.working_hours.filter(day=today_capitalized).first()
        if not working_hour:
            # Try with lowercase
            working_hour = obj.user.working_hours.filter(day=today_lower).first()
        
        if not working_hour or not working_hour.is_open:
            return False  # closed today fully

        if working_hour.open_time and working_hour.close_time:
            # Check if current time is within working hours
            return working_hour.open_time <= current_time <= working_hour.close_time

        return True  # If no time is set but marked open



import json
import math
from rest_framework import serializers

class product_serializer(serializers.ModelSerializer):
    size_details = size_serializer(read_only=True, source='size')
    addons = serializers.SerializerMethodField()
    print_variants = PrintVariantSerializer(many=True, required=False)
    customize_print_variants = CustomizePrintVariantSerializer(many=True, required=False)
    is_favourite = serializers.SerializerMethodField()
    # variants = ProductVariantSerializer(many=True, read_only=True)
    variants = serializers.SerializerMethodField()
    store = serializers.SerializerMethodField()
    gallery_images_details = serializers.SerializerMethodField()
    serial_imei_list = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    # Add reviews as nested read-only field
    avg_rating = serializers.SerializerMethodField()    
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = product
        fields = '__all__'

    def get_addons(self, obj):
        """
        Return product_addon rows linked to this product.
        """
        try:
            qs = obj.product_addon.filter(addon__is_active=True, user = self.context.get('request').user)  # related_name on product_addon model
        except Exception:
            return []
        return ProductAddonSerializer(qs, many=True).data

    def get_gallery_images_details(self, obj):
        gi = getattr(obj, "gallery_images")
        # New schema (ManyToMany): serialize related images
        print('-------------------')
        print('-------------------')
        print('-------------------')
        print(gi)
        print('-------------------')
        print('-------------------')
        if hasattr(gi, "all"):
            return ProductImageSerializer(gi.all(), many=True, context=self.context).data
        # Legacy schema (ImageField): return single image entry if present
        url = gi.url if getattr(gi, "name", None) else None
        return [] if not url else [{"id": None, "image": url, "created_at": None}]

    def get_serial_imei_list(self, obj):
        try:
            return list(obj.serial_imei_list.values_list("value", flat=True))
        except Exception:
            return []

    def get_distance_km(self, obj):
        """
        Returns approximate distance in kilometers if annotated by the view as _dist
        where _dist = (Δlat^2 + Δlon^2). Converts degrees to km using ~111.32 km/degree.
        """
        dist = getattr(obj, "_dist", None)
        if dist is None:
            return None
        try:
            km = (float(dist) ** 0.5) * 111.32
            return round(km, 2)
        except Exception:
            return None

    def _parse_json_field(self, data, key):
        """
        Safely parse a JSON-like field from request.data for both JSON and form-data:
        - Already parsed lists/objects (application/json) are returned as-is
        - Stringified JSON (form-data Text) is parsed
        - For 'addons', also accept CSV like '14,22'
        """
        value = data.get(key)
        if value is None or value == "":
            return []
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            try:
                return json.loads(s)
            except Exception:
                if key == "addons":
                    import re
                    return [int(x) for x in re.findall(r"\d+", s)]
                return []
        return []

    def _normalize_addons_payload(self, addons_data):
        """
        Normalize addons into a list of dicts acceptable by product_addon.create:
          - [ {"addon": 14}, {"addon": 22} ]  → [{ "addon_id":14 }, { "addon_id":22 }]
          - [14, 22]                           → [{ "addon_id":14 }, { "addon_id":22 }]
        """
        normalized = []
        for entry in addons_data or []:
            if isinstance(entry, int):
                normalized.append({"addon_id": entry})
                continue
            if isinstance(entry, dict):
                if "addon" in entry and isinstance(entry.get("addon"), int):
                    e = {**entry}
                    e["addon_id"] = e.pop("addon")
                    normalized.append(e)
                else:
                    normalized.append(entry)
        return normalized

    def create(self, validated_data):
        request = self.context.get('request')
        data = request.data

        # Ensure M2M is not passed into model.create()
        validated_data.pop('gallery_images', None)

        addons_data = self._normalize_addons_payload(self._parse_json_field(data, 'addons'))
        variants_data = self._parse_json_field(data, 'print_variants')
        customize_data = self._parse_json_field(data, 'customize_print_variants')
        gallery_image_ids = self._parse_json_field(data, 'gallery_image_ids')  # optional list of existing IDs
        imeis = self._parse_json_field(data, 'serial_imei_no') or self._parse_json_field(data, 'serial_imei_nos')

        instance = product.objects.create(**validated_data)

        for addon in addons_data:
            product_addon.objects.create(product=instance, **addon)

        # Only allow model fields for PrintVariant, ignore display keys
        allowed_variant_keys = {"paper", "color_type", "sided", "min_quantity", "max_quantity", "price"}
        for variant in variants_data:
            if isinstance(variant, dict):
                variant = {k: v for k, v in variant.items() if k in allowed_variant_keys}
            PrintVariant.objects.create(product=instance, **variant)

        for custom in customize_data:
            CustomizePrintVariant.objects.create(product=instance, **custom)

        # Save serial/IMEI numbers (deduplicate, ignore blanks)
        try:
            from vendor.models import serial_imei_no as SerialImei
            seen = set()
            for v in imeis or []:
                val = str(v).strip()
                if not val or val in seen:
                    continue
                seen.add(val)
                SerialImei.objects.create(product=instance, value=val)
        except Exception:
            pass

        # Attach gallery images: support both uploaded files and existing image ids
        # Collect uploads from common frontend patterns: gallery_images, gallery_images[], gallery_images[0], gallery_image, gallery_image[0]
        upload_list = []
        try:
            mf = request.FILES
            candidate_keys = set()
            for k in mf.keys():
                if k in ("gallery_images", "gallery_images[]", "gallery_image"):
                    candidate_keys.add(k)
                if k.startswith("gallery_images[") or k.startswith("gallery_image["):
                    candidate_keys.add(k)
            for k in candidate_keys:
                upload_list.extend(mf.getlist(k))
        except Exception:
            upload_list = []
        for f in upload_list or []:
            img = ProductImage.objects.create(image=f)
            gi = getattr(instance, "gallery_images", None)
            # Support both M2M (new) and legacy ImageField (old server without reload)
            if hasattr(gi, "add"):
                gi.add(img)
            else:
                # Legacy fallback: keep only the first upload
                if not getattr(instance, "gallery_images", None):
                    instance.gallery_images = img.image
                    instance.save(update_fields=["gallery_images"])
        if gallery_image_ids:
            existing = ProductImage.objects.filter(id__in=[int(i) for i in gallery_image_ids if str(i).isdigit()])
            gi = getattr(instance, "gallery_images", None)
            if hasattr(gi, "add"):
                gi.add(*list(existing))
            else:
                # If legacy ImageField, set the first existing image (best-effort)
                first = existing.first()
                if first:
                    instance.gallery_images = first.image
                    instance.save(update_fields=["gallery_images"])

        return instance

    def update(self, instance, validated_data):
        request = self.context.get('request')
        data = request.data

        # Ensure M2M is not assigned directly
        validated_data.pop('gallery_images', None)

        addons_data = self._normalize_addons_payload(self._parse_json_field(data, 'addons'))
        variants_data = self._parse_json_field(data, 'print_variants')
        customize_data = self._parse_json_field(data, 'customize_print_variants')
        gallery_image_ids = self._parse_json_field(data, 'gallery_image_ids')
        imeis = self._parse_json_field(data, 'serial_imei_no') or self._parse_json_field(data, 'serial_imei_nos')

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle related nested data
        if 'addons' in data:
            product_addon.objects.filter(product=instance).delete()
            for addon in addons_data or []:
                product_addon.objects.create(product=instance, **addon)

        if variants_data:
            PrintVariant.objects.filter(product=instance).delete()
            allowed_variant_keys = {"paper", "color_type", "sided", "min_quantity", "max_quantity", "price"}
            for variant in variants_data:
                if isinstance(variant, dict):
                    variant = {k: v for k, v in variant.items() if k in allowed_variant_keys}
                PrintVariant.objects.create(product=instance, **variant)

        if customize_data:
            CustomizePrintVariant.objects.filter(product=instance).delete()
            for custom in customize_data:
                CustomizePrintVariant.objects.create(product=instance, **custom)

        # Replace gallery images only if provided in this request
        files_provided = False
        try:
            mf = request.FILES
            upload_list = []
            candidate_keys = set()
            for k in mf.keys():
                if k in ("gallery_images", "gallery_images[]", "gallery_image"):
                    candidate_keys.add(k)
                if k.startswith("gallery_images[") or k.startswith("gallery_image["):
                    candidate_keys.add(k)
            for k in candidate_keys:
                upload_list.extend(mf.getlist(k))
            files_provided = bool(upload_list)
        except Exception:
            upload_list = []
        ids_provided = 'gallery_image_ids' in data
        if files_provided or ids_provided:
            gi = getattr(instance, "gallery_images", None)
            # Clear existing (M2M) or null out legacy ImageField
            if hasattr(gi, "clear"):
                gi.clear()
            else:
                instance.gallery_images = None
                instance.save(update_fields=["gallery_images"])
            for f in upload_list or []:
                img = ProductImage.objects.create(image=f)
                gi = getattr(instance, "gallery_images", None)
                if hasattr(gi, "add"):
                    gi.add(img)
                else:
                    if not getattr(instance, "gallery_images", None):
                        instance.gallery_images = img.image
                        instance.save(update_fields=["gallery_images"])
            if gallery_image_ids:
                existing = ProductImage.objects.filter(id__in=[int(i) for i in gallery_image_ids if str(i).isdigit()])
                gi = getattr(instance, "gallery_images", None)
                if hasattr(gi, "add"):
                    gi.add(*list(existing))
                else:
                    first = existing.first()
                    if first:
                        instance.gallery_images = first.image
                        instance.save(update_fields=["gallery_images"])

        # Replace serial/IMEI numbers if provided
        if imeis is not None:
            try:
                from vendor.models import serial_imei_no as SerialImei
                instance.serial_imei_list.all().delete()
                seen = set()
                for v in imeis or []:
                    val = str(v).strip()
                    if not val or val in seen:
                        continue
                    seen.add(val)
                    SerialImei.objects.create(product=instance, value=val)
            except Exception:
                pass

        return instance

        
    def _get_reviews_queryset(self, obj):
        if not hasattr(self, '_reviews_cache'):
            self._reviews_cache = {}
        if obj.id not in self._reviews_cache:
            self._reviews_cache[obj.id] = Review.objects.filter(order_item__product=obj)
        return self._reviews_cache[obj.id]


    def get_reviews(self, obj):
        from customer.serializers import ReviewSerializer
        reviews = self._get_reviews_queryset(obj)
        return ReviewSerializer(reviews, many=True).data

    def get_addons(self, obj):
        from .serializers import ProductAddonSerializer
        addon = product_addon.objects.filter(product = obj)
        return ProductAddonSerializer(addon, many=True).data

    def get_avg_rating(self, obj):
        from django.db.models import Avg
        reviews = self._get_reviews_queryset(obj)
        avg = reviews.aggregate(avg=Avg('rating'))['avg']
        return round(avg, 1) if avg else 0.0

    def get_store(self, obj):
        try:
            # Assuming one store per user
            store = obj.user.vendor_store.first()  # related_name='vendor_store'
            if store:
                from .serializers import VendorStoreSerializer2
                return VendorStoreSerializer2(store).data
        except:
            return None

    def get_is_favourite(self, obj):
        from customer.models import Favourite

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        # ✅ Cache favourite IDs (only one DB query per request)
        if not hasattr(self, "_user_fav_ids"):
            self._user_fav_ids = set(
                Favourite.objects.filter(user=request.user)
                .values_list("product_id", flat=True)
            )

        return obj.id in self._user_fav_ids
        

    def get_variants(self, obj):
        # Always show full family: root (parent if any) + all its children
        root = obj if getattr(obj, "parent_id", None) is None else obj.parent
        family = [root] + list(root.variants.all())
        # Remove potential duplicates while preserving order
        seen = set()
        unique_family = []
        for p in family:
            if p.id not in seen:
                seen.add(p.id)
                unique_family.append(p)
        # Do not include the current product in its own variants list
        unique_family = [p for p in unique_family if p.id != obj.id]
        serializer = ProductVariantSerializer(unique_family, many=True, context=self.context)
        return serializer.data



class BannerCampaignSerializer(serializers.ModelSerializer):

    product_details = product_serializer(source = "product", read_only = True)
    store_details = VendorStoreSerializer2(source = "store", read_only = True)
    class Meta:
        model = BannerCampaign
        fields = '__all__'
        read_only_fields = ['user', 'is_approved', 'created_at']

    def validate(self, data):
        redirect_to = data.get('redirect_to')

        if redirect_to == 'product' and not data.get('product'):
            raise serializers.ValidationError({"product": "Product ID is required when redirect_to = 'product'."})
        if redirect_to == 'store' and data.get('product'):
            raise serializers.ValidationError({"product": "Do not pass product when redirect_to = 'store'."})

        return data
    
    
class ReelSerializer(serializers.ModelSerializer):

    product_details = product_serializer(source = 'product', read_only = True)
    store = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    total_likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Reel
        fields = '__all__'
        read_only_fields = ['user']  

    def validate_media(self, value):
        """Validate reel media file size (max 100MB)"""
        max_size = 100 * 1024 * 1024  # 100MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size too large. Maximum allowed size is {max_size / (1024 * 1024):.0f}MB. '
                f'Your file is {value.size / (1024 * 1024):.2f}MB.'
            )
        return value  


    def get_store(self, obj):
        try:
            # Assuming one store per user
            store = obj.user.vendor_store.first()  # related_name='vendor_store'
            if store:
                from .serializers import VendorStoreSerializer2
                return VendorStoreSerializer2(store).data
        except:
            return None
        
    def get_is_following(self, obj):

        from customer.models import Follower

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if request.user is following obj.user
            return Follower.objects.filter(user=obj.user, follower=request.user).exists()
        return False
    
    def get_total_likes_count(self, obj):
        """Get total likes count for the reel"""
        from django.db.models import Count
        
        try:
            # Try to import FavouriteReel model if it exists
            from customer.models import FavouriteReel
            return FavouriteReel.objects.filter(reel=obj).count()
        except (ImportError, AttributeError):
            # If FavouriteReel model doesn't exist yet, check for alternative
            # Check if there's a related_name on Reel model for likes
            try:
                # Try accessing through a related_name if it exists
                if hasattr(obj, 'favourited_by'):
                    return obj.favourited_by.count()
            except:
                pass
            # Return 0 if no like system exists yet
            return 0

    
class SpotlightProductSerializer(serializers.ModelSerializer):

    product_details = product_serializer(source = "product", read_only=True)
    store = serializers.SerializerMethodField()

    class Meta:
        model = SpotlightProduct
        fields = '__all__'
        read_only_fields = ['user', 'product_details']  


    def get_store(self, obj):
        try:
            # Assuming one store per user
            store = obj.user.vendor_store.first()  # related_name='vendor_store'
            if store:
                from .serializers import VendorStoreSerializer2
                return VendorStoreSerializer2(store).data
        except:
            return None
    
        
    
class PostSerializer(serializers.ModelSerializer):

    product_details = product_serializer(source = 'product', read_only = True)
    store = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['user']  


    def get_store(self, obj):
        try:
            # Assuming one store per user
            store = obj.user.vendor_store.first()  # related_name='vendor_store'
            if store:
                from .serializers import VendorStoreSerializer2
                return VendorStoreSerializer2(store).data
        except:
            return None
     


from rest_framework import serializers

class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'price']



from rest_framework.exceptions import ValidationError
from django.db import IntegrityError, transaction

class SaleItemSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField(read_only=True)
    product_details = product_serializer(source = "product", read_only=True)
    serial_imei_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Serial/IMEI number value to link to this sale item (OneToOne)"
    )
    serial_imei_value = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'price', 'amount', 'product_details', 'serial_imei_number', 'serial_imei_value']

    def get_amount(self, obj):
        return round(obj.quantity * obj.price, 2)
    
    def get_serial_imei_value(self, obj):
        """Return serial/IMEI value for this sale item"""
        if obj.serial_imei_number:
            return obj.serial_imei_number.value
        return None
    
    def create(self, validated_data):
        """Create SaleItem and link serial/IMEI number"""
        serial_imei_value = validated_data.pop('serial_imei_number', None)
        sale_item = super().create(validated_data)
        
        # Link serial/IMEI number if provided
        if serial_imei_value:
            from vendor.models import serial_imei_no
            # Find serial_imei_no record by value for this product
            serial_obj = serial_imei_no.objects.filter(
                product=sale_item.product,
                value=serial_imei_value,
                is_sold=False
            ).first()
            if serial_obj:
                sale_item.serial_imei_number = serial_obj
                sale_item.save()
        
        return sale_item
    
    def update(self, instance, validated_data):
        """Update SaleItem and handle serial/IMEI number"""
        serial_imei_value = validated_data.pop('serial_imei_number', None)
        sale_item = super().update(instance, validated_data)
        
        # Update serial/IMEI number if provided
        if serial_imei_value is not None:
            if serial_imei_value:
                from vendor.models import serial_imei_no
                # Find serial_imei_no record by value for this product
                serial_obj = serial_imei_no.objects.filter(
                    product=sale_item.product,
                    value=serial_imei_value,
                    is_sold=False
                ).first()
                if serial_obj:
                    sale_item.serial_imei_number = serial_obj
                else:
                    sale_item.serial_imei_number = None
            else:
                # Clear the link if empty string or None
                sale_item.serial_imei_number = None
            sale_item.save()
        
        return sale_item


class PosWholesaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = pos_wholesale
        fields = [
            'invoice_type', 'invoice_number', 'date',
            'dispatch_address', 'delivery_city',
            'references', 'notes', 'terms',
            'delivery_charges', 'packaging_charges', 'reverse_charges',
            'eway_bill_number', 'lr_number', 'vehicle_number',
            'transport_name', 'number_of_parcels'
        ]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, required=False)
    wholesale_invoice = PosWholesaleSerializer(write_only=True, required=False)
    bank_details = vendor_bank_serializer(source="bank", read_only=True)
    customer_details = vendor_customers_serializer(source="customer", read_only=True)

    wholesale_invoice_details = serializers.SerializerMethodField(read_only=True)
    company_profile_detials = CompanyProfileSerializer(source="company_profile", read_only=True)
    customer_detials = vendor_customers_serializer(source="customer", read_only=True)
    advance_bank_details = vendor_bank_serializer(source="advance_bank", read_only=True)
    
    # Explicitly define advance_payment_method to ensure it's always included in response
    advance_payment_method = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    total_items = serializers.IntegerField(read_only=True)
    total_amount_before_discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'payment_method', 'bank', 'company_profile', 'customer', 'company_profile_detials', 'customer_detials',
            'discount_percentage', 'advance_amount', 'advance_payment_method', 'advance_bank', 'advance_bank_details',
            'balance_amount', 'credit_date', 'is_wholesale_rate',
            'items', 'total_items', 'total_amount_before_discount',
            'discount_amount', 'total_amount', 'total_taxable_amount', 'total_gst_amount',
            'wholesale_invoice_details', 'wholesale_invoice', 'bank_details', 'customer_details', 'created_at'
        ]

    def get_wholesale_invoice_details(self, obj):
        invoice = obj.wholesales.first()
        return PosWholesaleSerializer(invoice).data if invoice else None

    def _normalize(self, data):
        """Convert empty strings to None for nullable fields."""
        for k, v in list(data.items()):
            if v == "":
                data[k] = None
        # Ensure advance_payment_method is preserved (don't convert to None if it's a valid choice)
        if 'advance_payment_method' in data and data['advance_payment_method'] in ['cash', 'bank']:
            # Keep the value as is
            pass
        return data

    def create(self, validated_data):
        validated_data = self._normalize(validated_data)
        items_data = validated_data.pop('items', [])
        wholesale_data = validated_data.pop('wholesale_invoice', None)
        validated_data.pop('user', None)
        
        # Log validated_data to debug advance_payment_method
        import logging
        logger = logging.getLogger('vendor.signals')
        logger.debug(f"[SALE_SERIALIZER] Creating sale with validated_data keys: {list(validated_data.keys())}")
        logger.debug(f"[SALE_SERIALIZER] advance_payment_method in validated_data: {'advance_payment_method' in validated_data}")
        if 'advance_payment_method' in validated_data:
            logger.debug(f"[SALE_SERIALIZER] advance_payment_method value: {validated_data.get('advance_payment_method')}")

        with transaction.atomic():
            sale = Sale.objects.create(
                user=self.context['request'].user,
                **validated_data
            )
            logger.debug(f"[SALE_SERIALIZER] Sale created with ID: {sale.id}")
            logger.debug(f"[SALE_SERIALIZER] Sale advance_payment_method after create: {sale.advance_payment_method}")

            # Create Sale Items
            for item in items_data:
                SaleItem.objects.create(
                    user=sale.user,
                    sale=sale,
                    **item
                )

            # Wholesale - create before recalculating totals so charges are included
            if sale.is_wholesale_rate and wholesale_data:
                # IMPORTANT:
                # For *create* flow we should NOT reuse an existing pos_wholesale row based on invoice_number.
                # Reusing causes `created=False` and can even re-link an old invoice to a new sale.
                # Instead:
                # - if invoice_number is provided, it must be UNIQUE for (user, invoice_number) or we raise an error
                # - if invoice_number is not provided, we create a new pos_wholesale and let model generate it
                invoice_number = wholesale_data.get('invoice_number')
                if invoice_number:
                    exists = pos_wholesale.objects.filter(user=sale.user, invoice_number=invoice_number).exists()
                    if exists:
                        raise serializers.ValidationError({
                            "wholesale_invoice": {
                                "invoice_number": f"Invoice number '{invoice_number}' is already used."
                            }
                        })
                    invoice = pos_wholesale.objects.create(
                        user=sale.user,
                        sale=sale,
                        **wholesale_data
                    )
                else:
                    # No invoice_number provided: always create a new record (invoice_number auto-generated in save())
                    invoice = pos_wholesale.objects.create(
                        user=sale.user,
                        sale=sale,
                        **wholesale_data
                    )

            # Totals - recalculate after wholesale is created
            self._recalculate_totals(sale)

        return sale

    def update(self, instance, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 80)
        logger.info(f"[SALE_SERIALIZER] ========== UPDATE METHOD CALLED ==========")
        logger.info(f"[SALE_SERIALIZER] Sale ID: {instance.id}")
        logger.info(f"[SALE_SERIALIZER] Invoice Number: {instance.invoice_number}")
        logger.info(f"[SALE_SERIALIZER] Current Bank: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.info(f"[SALE_SERIALIZER] Validated Data Keys: {list(validated_data.keys())}")
        
        validated_data = self._normalize(validated_data)
        items_data = validated_data.pop('items', None)
        wholesale_data = validated_data.pop('wholesale_invoice', None)
        
        # Get original request data to check for explicit None/null values
        request = self.context.get('request')
        if request and hasattr(request, 'data'):
            request_data = request.data
            logger.info(f"[SALE_SERIALIZER] Request Data Keys: {list(request_data.keys()) if isinstance(request_data, dict) else 'Not a dict'}")
        else:
            request_data = {}
            logger.warning("[SALE_SERIALIZER] No request in context!")
        
        # Handle bank field explicitly - check if it's in request_data (even if None)
        if 'bank' in request_data:
            bank_value = request_data.get('bank')
            logger.info(f"[SALE_SERIALIZER] Bank in request_data: {bank_value} (type: {type(bank_value).__name__})")
            # Convert empty string or 'null' string to None
            if bank_value in (None, '', 'null', 'None'):
                validated_data['bank'] = None
                logger.info("[SALE_SERIALIZER] Setting bank to None")
            else:
                # Let validated_data handle it (it will have the proper bank object or ID)
                if 'bank' not in validated_data:
                    validated_data['bank'] = bank_value
                    logger.info(f"[SALE_SERIALIZER] Adding bank to validated_data: {bank_value}")
                else:
                    logger.info(f"[SALE_SERIALIZER] Bank already in validated_data: {validated_data.get('bank')}")
        else:
            logger.info("[SALE_SERIALIZER] Bank not in request_data")
        
        # Log validated_data to debug advance_payment_method
        logger.info(f"[SALE_SERIALIZER] advance_payment_method in validated_data: {'advance_payment_method' in validated_data}")
        if 'advance_payment_method' in validated_data:
            logger.info(f"[SALE_SERIALIZER] advance_payment_method value: {validated_data.get('advance_payment_method')}")

        # Update base fields
        logger.info(f"[SALE_SERIALIZER] Updating fields: {list(validated_data.keys())}")
        for attr, value in validated_data.items():
            old_value = getattr(instance, attr, None)
            logger.info(f"[SALE_SERIALIZER] Setting {attr}: {old_value} -> {value}")
            setattr(instance, attr, value)
        logger.info("[SALE_SERIALIZER] Saving instance...")
        instance.save()
        logger.info(f"[SALE_SERIALIZER] Instance saved. Bank after save: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.debug(f"[SALE_SERIALIZER] Sale advance_payment_method after update: {instance.advance_payment_method}")

        # Replace items if sent
        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                SaleItem.objects.create(
                    user=instance.user,
                    sale=instance,
                    **item
                )

        # Wholesale - update before recalculating totals so charges are included
        if instance.is_wholesale_rate and wholesale_data is not None:
            logger.info(f"[SALE_SERIALIZER] Updating wholesale invoice with data: {list(wholesale_data.keys())}")
            invoice, _ = pos_wholesale.objects.get_or_create(
                user=instance.user, sale=instance
            )
            logger.info(f"[SALE_SERIALIZER] Wholesale invoice: {invoice.invoice_number if invoice else 'New'}")
            # Handle delivery_charges and packaging_charges explicitly
            # Check request_data for aliases (delivery_charges, packing_charges)
            if 'wholesale_invoice' in request_data:
                wholesale_request = request_data.get('wholesale_invoice', {})
                if isinstance(wholesale_request, dict):
                    logger.info(f"[SALE_SERIALIZER] Wholesale request data keys: {list(wholesale_request.keys())}")
                    # Handle delivery_charges alias
                    if 'delivery_charges' in wholesale_request and 'delivery_charges' not in wholesale_data:
                        wholesale_data['delivery_charges'] = wholesale_request.get('delivery_charges')
                        logger.info(f"[SALE_SERIALIZER] Added delivery_charges from request: {wholesale_data['delivery_charges']}")
                    # Handle packing_charges alias
                    if 'packing_charges' in wholesale_request and 'packaging_charges' not in wholesale_data:
                        wholesale_data['packaging_charges'] = wholesale_request.get('packing_charges')
                        logger.info(f"[SALE_SERIALIZER] Added packaging_charges from request: {wholesale_data['packaging_charges']}")
            
            for attr, value in wholesale_data.items():
                old_value = getattr(invoice, attr, None)
                logger.info(f"[SALE_SERIALIZER] Setting wholesale {attr}: {old_value} -> {value}")
                setattr(invoice, attr, value)
            invoice.save()
            logger.info(f"[SALE_SERIALIZER] Wholesale invoice saved. Delivery: {invoice.delivery_charges}, Packaging: {invoice.packaging_charges}")

        # Recalculate totals - recalculate after wholesale is updated
        logger.info("[SALE_SERIALIZER] Recalculating totals...")
        self._recalculate_totals(instance)
        logger.info(f"[SALE_SERIALIZER] Final Total Amount: {instance.total_amount}")
        logger.info("=" * 80)
        logger.info("[SALE_SERIALIZER] ========== UPDATE METHOD COMPLETED ==========")
        logger.info("=" * 80)

        return instance

    def _recalculate_totals(self, sale):
        from decimal import Decimal
        
        total_items = sum(item.quantity for item in sale.items.all())
        # Use item.amount (taxable value) from database, which is already calculated in SaleItem.save()
        total_amount_before_discount = sum(Decimal(item.amount or 0) for item in sale.items.all())
        discount_amount = total_amount_before_discount * (sale.discount_percentage or 0) / 100
        base_total_amount = total_amount_before_discount - discount_amount
        
        # Calculate GST totals from SaleItems
        total_taxable_amount = Decimal(0)
        total_gst_amount = Decimal(0)
        
        for item in sale.items.all():
            # Sum taxable amounts (amount field from SaleItem)
            total_taxable_amount += Decimal(item.amount or 0)
            # Sum GST amounts (tax_amount field from SaleItem)
            total_gst_amount += Decimal(item.tax_amount or 0)
        
        # Add delivery and packaging charges from pos_wholesale if it exists
        delivery_charges = Decimal(0)
        packaging_charges = Decimal(0)
        wholesale = sale.wholesales.first()
        if wholesale:
            delivery_charges = Decimal(wholesale.delivery_charges or 0)
            packaging_charges = Decimal(wholesale.packaging_charges or 0)
        
        # Final total includes: items (after discount) + GST + delivery + packaging
        total_amount = base_total_amount + total_gst_amount + delivery_charges + packaging_charges
        advance_amount = sale.advance_amount or 0

        sale.total_items = total_items
        sale.total_amount_before_discount = total_amount_before_discount
        sale.discount_amount = discount_amount
        sale.total_taxable_amount = total_taxable_amount
        sale.total_gst_amount = total_gst_amount
        sale.total_amount = total_amount
        sale.balance_amount = total_amount - advance_amount
        sale.save()


from django.utils import timezone

class VendorStoreSerializer(serializers.ModelSerializer):
    # Nested child serializers
    working_hours = StoreWorkingHourSerializer(source='user.working_hours', many=True, read_only=True)
    spotlight_products = SpotlightProductSerializer(source='user.spotlightproduct_set', many=True, read_only=True)
    posts = PostSerializer(source='user.post_set', many=True, read_only=True)
    reels = ReelSerializer(source='user.reel_set', many=True, read_only=True)
    banners = serializers.SerializerMethodField()

    is_store_open = serializers.SerializerMethodField() 
    store_rating = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    total_visits = serializers.SerializerMethodField()  # ✅ NEW: Total store visits

    class Meta:
        model = vendor_store
        fields = '__all__'
    
    def get_is_store_open(self, obj):
         # Store-level active check ✅
        if not obj.is_offline:
            return False

        now = timezone.localtime()
        # Get day name - try both lowercase and capitalized to handle case mismatch
        today_lower = now.strftime('%A').lower()  # 'monday'
        today_capitalized = now.strftime('%A')  # 'Monday'
        current_time = now.time()

        # Try both lowercase and capitalized day names to handle any case mismatch
        working_hour = obj.user.working_hours.filter(day=today_capitalized).first()
        if not working_hour:
            # Try with lowercase
            working_hour = obj.user.working_hours.filter(day=today_lower).first()
        
        if not working_hour or not working_hour.is_open:
            return False  # closed today fully

        if working_hour.open_time and working_hour.close_time:
            # Check if current time is within working hours
            return working_hour.open_time <= current_time <= working_hour.close_time

        return True  # If no time is set but marked open

    def get_store_rating(self, obj):
        """Average product rating for this store (all reviews, visible or not)."""
        try:
            from customer.models import Review
            from django.db.models import Avg
            avg = (Review.objects
                   .filter(order_item__product__user=obj.user)
                   .aggregate(a=Avg('rating'))['a'])
            return round(avg or 0.0, 1)
        except Exception:
            return 0.0

    def get_reviews(self, obj):
        """Return only visible reviews for this store's products."""
        try:
            from customer.models import Review
            from customer.serializers import ReviewSerializer
            qs = Review.objects.filter(order_item__product__user=obj.user, is_visible=True).order_by('-created_at')
            # pass through request if available for nested serializer context
            context = getattr(self, 'context', {})
            return ReviewSerializer(qs, many=True, context=context).data
        except Exception:
            return []

    def get_banners(self, obj):
        """Return only approved banners for this store."""
        try:
            from vendor.models import BannerCampaign
            qs = BannerCampaign.objects.filter(user=obj.user, is_approved=True).order_by('-created_at')
            # pass through request if available for nested serializer context
            context = getattr(self, 'context', {})
            return BannerCampaignSerializer(qs, many=True, context=context).data
        except Exception:
            return []
    
    def get_total_visits(self, obj):
        """Get total number of visits to this store."""
        try:
            from vendor.models import StoreVisit
            return StoreVisit.objects.filter(store=obj).count()
        except Exception:
            return 0

    
class DeliverySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliverySettings
        fields = '__all__'
        read_only_fields = ["user"]   # 👈 Important



class DeliveryBoySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryBoy
        fields = '__all__'
        read_only_fields = ["user"]   # 👈 Important


class DeliveryModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryMode
        fields = ['is_auto_assign_enabled', 'is_self_delivery_enabled']

   

    # 👇 This is safe: don't set user again, just return default create
    def create(self, validated_data):
        return super().create(validated_data)



class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'date', 'time', 'description']  # adjust fields as per your model

        
class PaymentSerializer(serializers.ModelSerializer):

    customer_details = vendor_customers_serializer(source="customer", read_only=True)
    vendor_details = vendor_vendors_serializer(source="vendor", read_only=True)
    bank_details = vendor_bank_serializer(source="bank", read_only=True)


    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['user']
    
    def update(self, instance, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 80)
        logger.info(f"[PAYMENT_SERIALIZER] ========== UPDATE METHOD CALLED ==========")
        logger.info(f"[PAYMENT_SERIALIZER] Payment ID: {instance.id}")
        logger.info(f"[PAYMENT_SERIALIZER] Payment Number: {instance.payment_number}")
        logger.info(f"[PAYMENT_SERIALIZER] Current Bank: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.info(f"[PAYMENT_SERIALIZER] Current Amount: {instance.amount}")
        logger.info(f"[PAYMENT_SERIALIZER] Validated Data Keys: {list(validated_data.keys())}")
        
        # Get original request data to check for explicit None/null values
        request = self.context.get('request')
        if request and hasattr(request, 'data'):
            request_data = request.data
            logger.info(f"[PAYMENT_SERIALIZER] Request Data Keys: {list(request_data.keys()) if isinstance(request_data, dict) else 'Not a dict'}")
        else:
            request_data = {}
            logger.warning("[PAYMENT_SERIALIZER] No request in context!")
        
        # Handle bank field explicitly - check if it's in request_data (even if None)
        if 'bank' in request_data:
            bank_value = request_data.get('bank')
            logger.info(f"[PAYMENT_SERIALIZER] Bank in request_data: {bank_value} (type: {type(bank_value).__name__})")
            # Convert empty string or 'null' string to None
            if bank_value in (None, '', 'null', 'None'):
                validated_data['bank'] = None
                logger.info("[PAYMENT_SERIALIZER] Setting bank to None")
            else:
                # Let validated_data handle it (it will have the proper bank object or ID)
                if 'bank' not in validated_data:
                    validated_data['bank'] = bank_value
                    logger.info(f"[PAYMENT_SERIALIZER] Adding bank to validated_data: {bank_value}")
                else:
                    logger.info(f"[PAYMENT_SERIALIZER] Bank already in validated_data: {validated_data.get('bank')}")
        else:
            logger.info("[PAYMENT_SERIALIZER] Bank not in request_data")
        
        # Update all fields
        logger.info(f"[PAYMENT_SERIALIZER] Updating fields: {list(validated_data.keys())}")
        for attr, value in validated_data.items():
            old_value = getattr(instance, attr, None)
            logger.info(f"[PAYMENT_SERIALIZER] Setting {attr}: {old_value} -> {value}")
            setattr(instance, attr, value)
        logger.info("[PAYMENT_SERIALIZER] Saving instance...")
        instance.save()
        logger.info(f"[PAYMENT_SERIALIZER] Instance saved. Bank after save: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.info("=" * 80)
        logger.info("[PAYMENT_SERIALIZER] ========== UPDATE METHOD COMPLETED ==========")
        logger.info("=" * 80)
        
        return instance

        

class ReminderSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderSetting
        fields = [
            'credit_bill_reminder',
            'credit_bill_days',
            'pending_invoice_reminder',
            'pending_invoice_days',
            'low_stock_reminder',
            'expiry_stock_reminder',
            'expiry_stock_days',
        ]


class SMSSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSSetting
        fields = [
            'available_credits',
            'used_credits',
            'enable_purchase_message',
            'enable_quote_message',
            'enable_credit_reminder_message',
        ]
        read_only_fields = ['created_at', 'updated_at', 'available_credits', 'used_credits']


class ReminderSerializer(serializers.ModelSerializer):
    reminder_type_display = serializers.CharField(source='get_reminder_type_display', read_only=True)
    
    class Meta:
        model = Reminder
        fields = [
            'id',
            'reminder_type',
            'reminder_type_display',
            'title',
            'message',
            'purchase',
            'sale',
            'product',
            'due_date',
            'amount',
            'stock_quantity',
            'expiry_date',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['user', 'created_at']


class TaxSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxSettings
        fields = '__all__'
        read_only_fields = ['user']


class InvoiceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceSettings
        fields = '__all__'
        read_only_fields = ['user']




class BankLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankLedger
        fields = ["id", "transaction_type", "reference_id", "balance_after", "description", "amount", "created_at"]

class BankWithLedgerSerializer(serializers.ModelSerializer):
    ledger_entries = BankLedgerSerializer(many=True, read_only=True)

    class Meta:
        model = vendor_bank
        fields = [
            "id",
            "name",
            "account_holder",
            "account_number",
            "opening_balance",
            "balance",
            "ledger_entries",
        ]

    def get_current_balance(self, obj):
        return obj.balance()
    
    
class CashLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashLedger
        fields = ["id", "transaction_type", "reference_id", "description", "amount", "balance_after", "created_at"]
    
class CustomerLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerLedger
        fields = ["id", "customer", "transaction_type", "reference_id",
                  "description", "amount", "total_bill_amount", "created_at"]


class VendorLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorLedger
        fields = ["id", "vendor", "transaction_type", "reference_id",
                  "description", "amount", "created_at"]
        

        
class ExpenseSerializer(serializers.ModelSerializer):
    bank_details = vendor_bank_serializer(source="bank", read_only=True)
    category_details = expense_category_serializer(source="category", read_only=True)


    class Meta:
        model = Expense
        fields = [
            "id", "bank", "bank_details", 
            "user", "amount", "expense_date", 
            "category", "category_details", 
            "is_paid", "payment_method", 
            "payment_date", "description", "attachment"
        ]
        read_only_fields = ["user"]
    
    def update(self, instance, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 80)
        logger.info(f"[EXPENSE_SERIALIZER] ========== UPDATE METHOD CALLED ==========")
        logger.info(f"[EXPENSE_SERIALIZER] Expense ID: {instance.id}")
        logger.info(f"[EXPENSE_SERIALIZER] Current Bank: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.info(f"[EXPENSE_SERIALIZER] Current Amount: {instance.amount}")
        logger.info(f"[EXPENSE_SERIALIZER] Validated Data Keys: {list(validated_data.keys())}")
        
        # Get original request data to check for explicit None/null values
        request = self.context.get('request')
        if request and hasattr(request, 'data'):
            request_data = request.data
            logger.info(f"[EXPENSE_SERIALIZER] Request Data Keys: {list(request_data.keys()) if isinstance(request_data, dict) else 'Not a dict'}")
        else:
            request_data = {}
            logger.warning("[EXPENSE_SERIALIZER] No request in context!")
        
        # Handle bank field explicitly - check if it's in request_data (even if None)
        if 'bank' in request_data:
            bank_value = request_data.get('bank')
            logger.info(f"[EXPENSE_SERIALIZER] Bank in request_data: {bank_value} (type: {type(bank_value).__name__})")
            # Convert empty string or 'null' string to None
            if bank_value in (None, '', 'null', 'None'):
                validated_data['bank'] = None
                logger.info("[EXPENSE_SERIALIZER] Setting bank to None")
            else:
                # Let validated_data handle it (it will have the proper bank object or ID)
                if 'bank' not in validated_data:
                    validated_data['bank'] = bank_value
                    logger.info(f"[EXPENSE_SERIALIZER] Adding bank to validated_data: {bank_value}")
                else:
                    logger.info(f"[EXPENSE_SERIALIZER] Bank already in validated_data: {validated_data.get('bank')}")
        else:
            logger.info("[EXPENSE_SERIALIZER] Bank not in request_data")
        
        # Update all fields
        logger.info(f"[EXPENSE_SERIALIZER] Updating fields: {list(validated_data.keys())}")
        for attr, value in validated_data.items():
            old_value = getattr(instance, attr, None)
            logger.info(f"[EXPENSE_SERIALIZER] Setting {attr}: {old_value} -> {value}")
            setattr(instance, attr, value)
        logger.info("[EXPENSE_SERIALIZER] Saving instance...")
        instance.save()
        logger.info(f"[EXPENSE_SERIALIZER] Instance saved. Bank after save: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.info("=" * 80)
        logger.info("[EXPENSE_SERIALIZER] ========== UPDATE METHOD COMPLETED ==========")
        logger.info("=" * 80)
        
        return instance





class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)
    bank_details = vendor_bank_serializer(source="bank", read_only=True)
    advance_bank_details = vendor_bank_serializer(source="advance_bank", read_only=True)
    vendor_details = vendor_vendors_serializer(source="vendor", read_only=True)
    # Backward-compatible aliases from some clients
    delivery_charges = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)
    packing_charges = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)


    class Meta:
        model = Purchase
        fields = '__all__'
        read_only_fields = ['user', 'purchase_code']  # ignore incoming purchase_code

    def create(self, validated_data):
        request = self.context['request']
        validated_data.pop('user', None)  
        user = request.user
        items_data = validated_data.pop('items', [])
        # Aliases -> model fields
        if 'delivery_shipping_charges' not in validated_data and 'delivery_charges' in validated_data:
            validated_data['delivery_shipping_charges'] = validated_data.pop('delivery_charges')
        else:
            validated_data.pop('delivery_charges', None)
        if 'packaging_charges' not in validated_data and 'packing_charges' in validated_data:
            validated_data['packaging_charges'] = validated_data.pop('packing_charges')
        else:
            validated_data.pop('packing_charges', None)

        # purchase_code will be generated in Purchase.save() method
        purchase = Purchase.objects.create(
            user=user,
            **validated_data
        )

        # Create purchase items
        from decimal import Decimal
        for item_data in items_data:
            # Ensure quantity and price have defaults if not provided
            quantity = item_data.get('quantity', 1)
            price = item_data.get('price', 0)
            # Calculate total for this item (quantity * price)
            item_data['total'] = Decimal(str(quantity)) * Decimal(str(price))
            PurchaseItem.objects.create(purchase=purchase, **item_data)
        
        # Calculate and save total_amount from all items + delivery + packaging charges
        # IMPORTANT: Call calculate_total() AFTER items are created so delivery_shipping_charges 
        # and packaging_charges are included in total_amount (just like POS sales)
        purchase.calculate_total()
        # Save to persist the calculated total and trigger signal with correct total_amount
        purchase.save()
        # Refresh instance to get updated total_amount in response
        purchase.refresh_from_db()

        return purchase

    def update(self, instance, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 80)
        logger.info(f"[PURCHASE_SERIALIZER] ========== UPDATE METHOD CALLED ==========")
        logger.info(f"[PURCHASE_SERIALIZER] Purchase ID: {instance.id}")
        logger.info(f"[PURCHASE_SERIALIZER] Purchase Code: {instance.purchase_code}")
        logger.info(f"[PURCHASE_SERIALIZER] Current Bank: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.info(f"[PURCHASE_SERIALIZER] Current Delivery Charges: {instance.delivery_shipping_charges}")
        logger.info(f"[PURCHASE_SERIALIZER] Current Packaging Charges: {instance.packaging_charges}")
        logger.info(f"[PURCHASE_SERIALIZER] Validated Data Keys: {list(validated_data.keys())}")
        
        items_data = validated_data.pop('items', None)
        
        # Get original request data to check for explicit None/null values
        request = self.context.get('request')
        if request and hasattr(request, 'data'):
            request_data = request.data
            logger.info(f"[PURCHASE_SERIALIZER] Request Data Keys: {list(request_data.keys()) if isinstance(request_data, dict) else 'Not a dict'}")
        else:
            request_data = {}
            logger.warning("[PURCHASE_SERIALIZER] No request in context!")
        
        # Handle aliases -> model fields
        # Check request_data first to see if the user sent delivery_charges or packing_charges
        if 'delivery_charges' in request_data:
            logger.info(f"[PURCHASE_SERIALIZER] Found delivery_charges alias in request: {request_data.get('delivery_charges')}")
            if 'delivery_shipping_charges' not in validated_data:
                # User sent delivery_charges, convert to delivery_shipping_charges
                validated_data['delivery_shipping_charges'] = request_data.get('delivery_charges')
                logger.info(f"[PURCHASE_SERIALIZER] Converted delivery_charges -> delivery_shipping_charges: {validated_data['delivery_shipping_charges']}")
            # Remove alias from validated_data if present
            validated_data.pop('delivery_charges', None)
        
        if 'packing_charges' in request_data:
            logger.info(f"[PURCHASE_SERIALIZER] Found packing_charges alias in request: {request_data.get('packing_charges')}")
            if 'packaging_charges' not in validated_data:
                # User sent packing_charges, convert to packaging_charges
                validated_data['packaging_charges'] = request_data.get('packing_charges')
                logger.info(f"[PURCHASE_SERIALIZER] Converted packing_charges -> packaging_charges: {validated_data['packaging_charges']}")
            # Remove alias from validated_data if present
            validated_data.pop('packing_charges', None)
        
        # Handle bank field explicitly - check if it's in request_data (even if None)
        if 'bank' in request_data:
            bank_value = request_data.get('bank')
            logger.info(f"[PURCHASE_SERIALIZER] Bank in request_data: {bank_value} (type: {type(bank_value).__name__})")
            # Convert empty string or 'null' string to None
            if bank_value in (None, '', 'null', 'None'):
                validated_data['bank'] = None
                logger.info("[PURCHASE_SERIALIZER] Setting bank to None")
            else:
                # Let validated_data handle it (it will have the proper bank object or ID)
                if 'bank' not in validated_data:
                    validated_data['bank'] = bank_value
                    logger.info(f"[PURCHASE_SERIALIZER] Adding bank to validated_data: {bank_value}")
                else:
                    logger.info(f"[PURCHASE_SERIALIZER] Bank already in validated_data: {validated_data.get('bank')}")
        else:
            logger.info("[PURCHASE_SERIALIZER] Bank not in request_data")
        
        # Check if delivery_shipping_charges or packaging_charges are being updated
        charges_updated = 'delivery_shipping_charges' in validated_data or 'packaging_charges' in validated_data
        logger.info(f"[PURCHASE_SERIALIZER] Charges Updated: {charges_updated}")
        if 'delivery_shipping_charges' in validated_data:
            logger.info(f"[PURCHASE_SERIALIZER] New Delivery Charges: {validated_data['delivery_shipping_charges']}")
        if 'packaging_charges' in validated_data:
            logger.info(f"[PURCHASE_SERIALIZER] New Packaging Charges: {validated_data['packaging_charges']}")

        # Update Purchase fields except purchase_code
        # Explicitly handle all fields, including None values
        logger.info(f"[PURCHASE_SERIALIZER] Updating fields: {list(validated_data.keys())}")
        for attr, value in validated_data.items():
            if attr != 'purchase_code':  # prevent manual change
                old_value = getattr(instance, attr, None)
                logger.info(f"[PURCHASE_SERIALIZER] Setting {attr}: {old_value} -> {value}")
                setattr(instance, attr, value)

        # Replace items only if provided
        if items_data is not None:
            logger.info(f"[PURCHASE_SERIALIZER] Replacing {len(items_data)} items")
            instance.items.all().delete()
            from decimal import Decimal
            for item_data in items_data:
                # Ensure quantity and price have defaults if not provided
                quantity = item_data.get('quantity', 1)
                price = item_data.get('price', 0)
                # Calculate total for this item (quantity * price)
                item_data['total'] = Decimal(str(quantity)) * Decimal(str(price))
                PurchaseItem.objects.create(purchase=instance, **item_data)
        else:
            logger.info("[PURCHASE_SERIALIZER] No items data provided, keeping existing items")
        
        # Totals - recalculate after items are created/updated and charges are set
        # This ensures delivery_shipping_charges and packaging_charges are included in total_amount
        # IMPORTANT: Call calculate_total() BEFORE save() so the signal uses the correct total_amount
        # (Just like POS sales where _recalculate_totals() is called after wholesale is created)
        logger.info("[PURCHASE_SERIALIZER] Calling calculate_total()...")
        instance.calculate_total()
        logger.info(f"[PURCHASE_SERIALIZER] Calculated Total Amount: {instance.total_amount}")
        
        # Save instance (this will trigger the signal which uses the updated total_amount)
        logger.info("[PURCHASE_SERIALIZER] Saving instance...")
        instance.save()
        logger.info(f"[PURCHASE_SERIALIZER] Instance saved. Bank after save: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.info(f"[PURCHASE_SERIALIZER] Delivery Charges after save: {instance.delivery_shipping_charges}")
        logger.info(f"[PURCHASE_SERIALIZER] Packaging Charges after save: {instance.packaging_charges}")
        
        # Refresh instance to get updated total_amount in response
        instance.refresh_from_db()
        logger.info(f"[PURCHASE_SERIALIZER] Instance refreshed. Final Bank: {instance.bank} (ID: {instance.bank_id if instance.bank else None})")
        logger.info("=" * 80)
        logger.info("[PURCHASE_SERIALIZER] ========== UPDATE METHOD COMPLETED ==========")
        logger.info("=" * 80)

        return instance



class NotificationCampaignSerializer(serializers.ModelSerializer):
    store_details = serializers.SerializerMethodField()
    product_details = product_serializer(source = "product", read_only = True)

    class Meta:
        model = NotificationCampaign
        fields = "__all__"
        read_only_fields = ["user", "status", "views", "clicks", "created_at"]

    def get_store_details(self, obj):
        """Return vendor store filtered by user."""
        try:
            from .models import vendor_store
            store = vendor_store.objects.filter(user=obj.user).first()
            if store:
                context = getattr(self, 'context', {})
                return VendorStoreSerializer2(store, context=context).data
        except Exception:
            pass
        return None

    def validate(self, data):
        """
        Validate that:
        - If redirect_to is 'store', store must belong to the requesting user
        - If redirect_to is 'product', product_id must be provided
        """
        request = self.context.get('request')
        redirect_to = data.get('redirect_to')
        store = data.get('store')
        product = data.get('product')
        
        if redirect_to == 'store':
            # If store is provided, ensure it belongs to the requesting user
            if store:
                if request and store.user != request.user:
                    raise serializers.ValidationError({
                        'store': 'You can only select stores that belong to you.'
                    })
            # If no store provided, we'll auto-assign in perform_create
        elif redirect_to == 'product':
            # Product ID must be provided when redirect_to is 'product'
            if not product:
                raise serializers.ValidationError({
                    'product': 'Product ID is required when redirect_to is "product".'
                })
            # Ensure product belongs to the requesting user
            if request and product.user != request.user:
                raise serializers.ValidationError({
                    'product': 'You can only select products that belong to you.'
                })
        elif redirect_to == 'custom':
            # For custom, clear both product and store
            data['product'] = None
            data['store'] = None
        
        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
    
    


from customer.models import ReturnExchange, Review

class ReturnExchangeVendorSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)
    customer_name = serializers.CharField(source='user.first_name', read_only=True)

    class Meta:
        model = ReturnExchange
        fields = ['id', 'product_name', 'customer_name', 'type', 'reason', 'status', 'created_at']




        

        
class VendorCoverageSerializer(serializers.ModelSerializer):
    # Instead of single FK input, allow multiple pincodes
    
    pincode_details = Pincode_serializer(source="pincode")

    class Meta:
        model = VendorCoverage
        fields = ["id", "user", "pincode", "pincode_details"]

    

    
class OfferSerializer(serializers.ModelSerializer):
    from customer.serializers import ProductRequestSerializer

    seller = serializers.StringRelatedField(read_only=True)
    request_details = ProductRequestSerializer(source = "request", read_only = True)
    seller_user_details = UserProfileSerializer(source = 'seller', read_only = True)
    store = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    # New FK product details (structured)
    details = product_serializer(source="product", read_only=True)

    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ["seller", "created_at", "valid_till"]

    def get_media(self, obj):
        """Return list of media URLs for this offer"""
        from .models import OfferMedia
        media_files = OfferMedia.objects.filter(offer=obj)
        return [media.media.url for media in media_files]

    def get_store(self, obj):
        try:
            # Assuming one store per user
            store = obj.seller.vendor_store.first()  # related_name='vendor_store'
            if store:
                from .serializers import VendorStoreSerializer2
                return VendorStoreSerializer2(store).data
        except:
            return None
    
    def get_product_details(self, obj):
        """Return full product details matching the request's category/sub_category from seller's products"""
        try:
            request = obj.request
            if not request:
                return None
            
            # Get products from the seller that match the request's category and sub_category
            matching_products = product.objects.filter(
                user=obj.seller,
                category=request.category,
                sub_category=request.sub_category,
                is_active=True
            )[:10]  # Limit to 10 products
            
            if matching_products.exists():
                # Use product_serializer to get full product details
                context = getattr(self, 'context', {})
                return product_serializer(matching_products, many=True, context=context).data
            else:
                # If no exact match, try to find products by category only
                category_products = product.objects.filter(
                    user=obj.seller,
                    category=request.category,
                    is_active=True
                )[:10]
                
                if category_products.exists():
                    context = getattr(self, 'context', {})
                    return product_serializer(category_products, many=True, context=context).data
                else:
                    return []
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting product details for Offer {obj.id}: {e}")
            return None

    def create(self, validated_data):
        """Create Offer and handle multiple media uploads"""
        from .models import OfferMedia
        
        # Seller is passed from perform_create via serializer.save(seller=...)
        # If not provided, fallback to request.user
        seller = validated_data.pop('seller', None)
        if not seller:
            request_obj = self.context.get('request')
            seller = request_obj.user if request_obj else None
        
        # Create the Offer instance
        offer_instance = Offer.objects.create(seller=seller, **validated_data)
        
        # Handle multiple media uploads
        request_obj = self.context.get('request')
        if request_obj and hasattr(request_obj, 'FILES'):
            # Support multiple field names: media, media[], medias, medias[]
            media_files = []
            for key in request_obj.FILES.keys():
                if key in ('media', 'media[]', 'medias', 'medias[]'):
                    media_files.extend(request_obj.FILES.getlist(key))
                elif key.startswith('media[') or key.startswith('medias['):
                    media_files.extend(request_obj.FILES.getlist(key))
            
            # Create OfferMedia for each uploaded file
            for media_file in media_files:
                OfferMedia.objects.create(
                    offer=offer_instance,
                    media=media_file
                )
        
        return offer_instance

    def update(self, instance, validated_data):
        """Update Offer and handle media uploads"""
        from .models import OfferMedia
        
        # Update the Offer instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle new media uploads
        request_obj = self.context.get('request')
        if request_obj and hasattr(request_obj, 'FILES'):
            # Support multiple field names: media, media[], medias, medias[]
            media_files = []
            for key in request_obj.FILES.keys():
                if key in ('media', 'media[]', 'medias', 'medias[]'):
                    media_files.extend(request_obj.FILES.getlist(key))
                elif key.startswith('media[') or key.startswith('medias['):
                    media_files.extend(request_obj.FILES.getlist(key))
            
            # Create OfferMedia for each uploaded file
            for media_file in media_files:
                OfferMedia.objects.create(
                    offer=instance,
                    media=media_file
                )
        
        return instance


class OrderNotificationMessageSerializer(serializers.ModelSerializer):
    """Serializer for Order Notification Message"""
    
    class Meta:
        model = OrderNotificationMessage
        fields = ['id', 'message', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        


# -------------------------------
# Super Catalogue (API Serializer)
# -------------------------------
class SuperCatalogueSerializer(serializers.ModelSerializer):
    category_details = product_category_serializer(source="category", read_only=True)
    sub_category_id = serializers.PrimaryKeyRelatedField(
        source="sub_category", queryset=product_subcategory.objects.all(), write_only=True, required=False, allow_null=True
    )
    sub_category_details = serializers.SerializerMethodField(read_only=True)
    size_details = size_serializer(source="size", read_only=True)

    class Meta:
        model = super_catalogue
        fields = "__all__"
        read_only_fields = ["created_at", "user"]

    def get_sub_category_details(self, obj):
        """
        super_catalogue.sub_category is a CharField. It may store either a numeric id (as string)
        or the subcategory name. Resolve to product_subcategory instance if possible; otherwise
        return a minimal dict with the raw value.
        """
        from masters.models import product_subcategory as PS
        from masters.serializers import product_subcategory_serializer as PSS

        raw = getattr(obj, "sub_category", None)
        if not raw:
            return None

        sub = None
        # Try by id (raw could be "12")
        try:
            sub = PS.objects.filter(pk=int(raw)).first()
        except Exception:
            sub = None
        # Fallback by name
        if not sub:
            sub = PS.objects.filter(name=raw).first()

        if sub:
            return PSS(sub).data
        # Fallback: return raw string
        return {"id": None, "name": str(raw)}
# class StoreRatingSerializer(serializers.ModelSerializer):
#     vendor_user_id = serializers.IntegerField(write_only=True)
#     user_details = UserProfileSerializer(source = 'seller', read_only = True)

#     class Meta:
#         model = StoreRating
#         fields = [
#             'id',
#             'vendor_user_id',
#             'user',
#             'user_details',
#             'store',
#             'rating',
#             'comment',
#             'is_active',
#             'created_at',
#         ]
#         read_only_fields = ['id', 'created_at', 'user', 'user_details', 'store']

#     def validate(self, data):
#         """Ensure vendor_user_id corresponds to a valid store."""
#         vendor_user_id = data.get('vendor_user_id')
#         if not vendor_user_id:
#             raise serializers.ValidationError({"vendor_user_id": "This field is required."})

#         try:
#             store = vendor_store.objects.get(user_id=vendor_user_id)
#         except vendor_store.DoesNotExist:
#             raise serializers.ValidationError({"vendor_user_id": "Store not found for this user"})

#         # Attach store to validated data so viewset doesn’t complain
#         data['store'] = store
#         return data