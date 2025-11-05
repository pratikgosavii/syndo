from rest_framework import serializers
from users.serializer import UserProfileSerializer
from .models import *
from masters.serializers import *



class coupon_serializer(serializers.ModelSerializer):
    class Meta:
        model = coupon
        fields = '__all__'




class vendor_customers_serializer(serializers.ModelSerializer):
    
    class Meta:
        model = vendor_customers
        fields = '__all__'
        read_only_fields = ['user']  



class vendor_vendors_serializer(serializers.ModelSerializer):
    
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
    class Meta:
        model = product_addon
        fields = '__all__'



class OnlineStoreSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineStoreSetting
        fields = '__all__'
        read_only_fields = ['user']  


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = '__all__'
        read_only_fields = ['user']  



class PurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseItem
        fields = ['product']  # exclude 'purchase'

    





class vendor_serializer(serializers.ModelSerializer):
    class Meta:
        model = vendor_vendors
        fields = '__all__'
        read_only_fields = ['user']




class StoreWorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreWorkingHour
        fields = ['day', 'open_time', 'close_time', 'is_open']




    


class BannerCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerCampaign
        fields = '__all__'
        read_only_fields = ['user', 'is_approved', 'created_at']
  

        

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'



class CashBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBalance
        fields = ['balance', 'updated_at']


class CashAdjustHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CashAdjustHistory
        fields = ['id', 'previous_balance', 'new_balance', 'delta_amount', 'note', 'created_at']

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

    class Meta:
        model = vendor_store
        fields = '__all__'



import json
from rest_framework import serializers

class product_serializer(serializers.ModelSerializer):
    size_details = size_serializer(read_only=True, source='size')
    addons = ProductAddonSerializer(many=True, required=False)
    print_variants = PrintVariantSerializer(many=True, required=False)
    customize_print_variants = CustomizePrintVariantSerializer(many=True, required=False)
    is_favourite = serializers.BooleanField(read_only=True)
    # variants = ProductVariantSerializer(many=True, read_only=True)
    variants = serializers.SerializerMethodField()
    store = serializers.SerializerMethodField()

    # Add reviews as nested read-only field
    avg_rating = serializers.SerializerMethodField()    
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = product
        fields = '__all__'

    def _parse_json_field(self, data, key):
        """Safely parse a JSON string from multipart form-data."""
        value = data.get(key)
        if not value:
            return []
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []  # fallback to empty list if malformed JSON

    def create(self, validated_data):
        request = self.context.get('request')
        data = request.data

        addons_data = self._parse_json_field(data, 'addons')
        variants_data = self._parse_json_field(data, 'print_variants')
        customize_data = self._parse_json_field(data, 'customize_print_variants')

        instance = product.objects.create(**validated_data)

        for addon in addons_data:
            product_addon.objects.create(product=instance, **addon)

        for variant in variants_data:
            PrintVariant.objects.create(product=instance, **variant)

        for custom in customize_data:
            CustomizePrintVariant.objects.create(product=instance, **custom)

        return instance

    def update(self, instance, validated_data):
        request = self.context.get('request')
        data = request.data

        addons_data = self._parse_json_field(data, 'addons')
        variants_data = self._parse_json_field(data, 'print_variants')
        customize_data = self._parse_json_field(data, 'customize_print_variants')

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle related nested data
        if addons_data:
            product_addon.objects.filter(product=instance).delete()
            for addon in addons_data:
                product_addon.objects.create(product=instance, **addon)

        if variants_data:
            PrintVariant.objects.filter(product=instance).delete()
            for variant in variants_data:
                PrintVariant.objects.create(product=instance, **variant)

        if customize_data:
            CustomizePrintVariant.objects.filter(product=instance).delete()
            for custom in customize_data:
                CustomizePrintVariant.objects.create(product=instance, **custom)

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
        

    def get_variants(self, obj):
        # ✅ Pass context so request is available inside ProductVariantSerializer
        serializer = ProductVariantSerializer(
            obj.variants.all(),
            many=True,
            context=self.context  # <-- this is the key fix
        )
        return serializer.data

class ReelSerializer(serializers.ModelSerializer):

    product_details = product_serializer(source = 'product', read_only = True)
    store = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Reel
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
        
    def get_is_following(self, obj):

        from customer.models import Follower

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if request.user is following obj.user
            return Follower.objects.filter(user=obj.user, follower=request.user).exists()
        return False

    
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



class PosWholesaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = pos_wholesale
        fields = [
            'invoice_type', 'invoice_number', 'date',
            'dispatch_address', 'delivery_city', 'signature',
            'references', 'notes', 'terms',
            'delivery_charges', 'packaging_charges', 'reverse_charges',
            'eway_bill_number', 'lr_number', 'vehicle_number',
            'transport_name', 'number_of_parcels'
        ]

from rest_framework.exceptions import ValidationError
from django.db import IntegrityError, transaction

class SaleItemSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField(read_only=True)
    product_details = product_serializer(source = "product", read_only=True)
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'price', 'amount', 'product_details']

    def get_amount(self, obj):
        return round(obj.quantity * obj.price, 2)


class PosWholesaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = pos_wholesale
        fields = [
            'invoice_type', 'invoice_number', 'date',
            'dispatch_address', 'delivery_city', 'signature',
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

    total_items = serializers.IntegerField(read_only=True)
    total_amount_before_discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'payment_method', 'company_profile', 'customer', 'company_profile_detials', 'customer_detials',
            'discount_percentage', 'advance_amount', 'advance_bank', 'advance_bank_details',
            'balance_amount', 'credit_date', 'is_wholesale_rate',
            'items', 'total_items', 'total_amount_before_discount',
            'discount_amount', 'total_amount', 'wholesale_invoice_details',
            'wholesale_invoice', 'bank_details', 'customer_details', 'created_at'
        ]

    def get_wholesale_invoice_details(self, obj):
        invoice = obj.wholesales.first()
        return PosWholesaleSerializer(invoice).data if invoice else None

    def _normalize(self, data):
        """Convert empty strings to None for nullable fields."""
        for k, v in list(data.items()):
            if v == "":
                data[k] = None
        return data

    def create(self, validated_data):
        validated_data = self._normalize(validated_data)
        items_data = validated_data.pop('items', [])
        wholesale_data = validated_data.pop('wholesale_invoice', None)
        validated_data.pop('user', None)

        with transaction.atomic():
            sale = Sale.objects.create(
                user=self.context['request'].user,
                **validated_data
            )

            # Create Sale Items
            for item in items_data:
                SaleItem.objects.create(
                    user=sale.user,
                    sale=sale,
                    **item
                )

            # Totals
            self._recalculate_totals(sale)

            # Wholesale
            if sale.is_wholesale_rate and wholesale_data:
                pos_wholesale.objects.create(
                    user=sale.user,
                    sale=sale,
                    **wholesale_data
                )

        return sale

    def update(self, instance, validated_data):
        validated_data = self._normalize(validated_data)
        items_data = validated_data.pop('items', None)
        wholesale_data = validated_data.pop('wholesale_invoice', None)

        # Update base fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Replace items if sent
        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                SaleItem.objects.create(
                    user=instance.user,
                    sale=instance,
                    **item
                )

        # Recalculate totals
        self._recalculate_totals(instance)

        # Wholesale
        if instance.is_wholesale_rate and wholesale_data is not None:
            invoice, _ = pos_wholesale.objects.get_or_create(
                user=instance.user, sale=instance
            )
            for attr, value in wholesale_data.items():
                setattr(invoice, attr, value)
            invoice.save()

        return instance

    def _recalculate_totals(self, sale):
        total_items = sum(item.quantity for item in sale.items.all())
        total_amount_before_discount = sum(item.quantity * item.price for item in sale.items.all())
        discount_amount = total_amount_before_discount * (sale.discount_percentage or 0) / 100
        total_amount = total_amount_before_discount - discount_amount
        advance_amount = sale.advance_amount or 0

        sale.total_items = total_items
        sale.total_amount_before_discount = total_amount_before_discount
        sale.discount_amount = discount_amount
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
    banners = BannerCampaignSerializer(source='user.banners', many=True, read_only=True)

    is_store_open = serializers.SerializerMethodField() 

    class Meta:
        model = vendor_store
        fields = [
            'id', 'user',
            'working_hours',
            'spotlight_products',
            'name',
            'about',
            'profile_image',
            'banner_image',
            'posts',
            'reels',
            'banners',
            'storetag',
            'latitude',
            'longitude',
            'is_location',
            'is_active',
            'is_store_open',
        ]
    
    def get_is_store_open(self, obj):
         # Store-level active check ✅
        if not obj.is_active:
            return False

        now = timezone.localtime()
        today = now.strftime('%A').lower()
        current_time = now.time()

        working_hour = obj.user.working_hours.filter(day=today).first()
        if not working_hour or not working_hour.is_open:
            return False  # closed today fully

        if working_hour.open_time and working_hour.close_time:
            return working_hour.open_time <= current_time <= working_hour.close_time

        return True  # If no time is set but marked open

    
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


    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['user']

        

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
        ]


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
                  "description", "amount", "created_at"]


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





class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)
    bank_details = vendor_bank_serializer(source="advance_bank", read_only=True)
    vendor_details = vendor_vendors_serializer(source="vendor", read_only=True)


    class Meta:
        model = Purchase
        fields = '__all__'
        read_only_fields = ['user', 'purchase_code']  # ignore incoming purchase_code

    def create(self, validated_data):
        request = self.context['request']
        validated_data.pop('user', None)  
        user = request.user
        items_data = validated_data.pop('items', [])

        # Generate sequential purchase_code (global)
        last_purchase = Purchase.objects.order_by('-id').first()
        if last_purchase and last_purchase.purchase_code:
            try:
                last_number = int(last_purchase.purchase_code.split('-')[-1])
            except (IndexError, ValueError):
                last_number = 0
        else:
            last_number = 0
        prefix = "PUR"
        new_code = f"{prefix}-{last_number + 1:05d}"

        print(new_code)

        purchase = Purchase.objects.create(
            user=user,
            purchase_code=new_code,
            **validated_data
        )

        for item_data in items_data:
            PurchaseItem.objects.create(purchase=purchase, **item_data)

        return purchase

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update Purchase fields except purchase_code
        for attr, value in validated_data.items():
            if attr != 'purchase_code':  # prevent manual change
                setattr(instance, attr, value)
        instance.save()

        # Replace items only if provided
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                PurchaseItem.objects.create(purchase=instance, **item_data)

        return instance



class NotificationCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationCampaign
        fields = "__all__"
        read_only_fields = ["user", "status", "views", "clicks", "created_at"]

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

    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ["seller", "created_at", "valid_till"]

    def get_store(self, obj):
        try:
            # Assuming one store per user
            store = obj.seller.vendor_store.first()  # related_name='vendor_store'
            if store:
                from .serializers import VendorStoreSerializer2
                return VendorStoreSerializer2(store).data
        except:
            return None
        

class StoreRatingSerializer(serializers.ModelSerializer):
    vendor_user_id = serializers.IntegerField(write_only=True)
    user_details = UserProfileSerializer(source = 'seller', read_only = True)

    class Meta:
        model = StoreRating
        fields = [
            'id',
            'vendor_user_id',
            'user',
            'user_details',
            'store',
            'rating',
            'comment',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'user', 'user_details', 'store']

    def validate(self, data):
        """Ensure vendor_user_id corresponds to a valid store."""
        vendor_user_id = data.get('vendor_user_id')
        if not vendor_user_id:
            raise serializers.ValidationError({"vendor_user_id": "This field is required."})

        try:
            store = vendor_store.objects.get(user_id=vendor_user_id)
        except vendor_store.DoesNotExist:
            raise serializers.ValidationError({"vendor_user_id": "Store not found for this user"})

        # Attach store to validated data so viewset doesn’t complain
        data['store'] = store
        return data