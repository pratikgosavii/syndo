from rest_framework import serializers
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


class SpotlightProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotlightProduct
        fields = '__all__'
        read_only_fields = ['user']  

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['user']  

class ReelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reel
        fields = '__all__'
        read_only_fields = ['user']  


class BannerCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerCampaign
        fields = '__all__'
        read_only_fields = ['user', 'is_approved', 'created_at']

    def validate(self, data):
        if data.get('boost_post') and not data.get('budget'):
            raise serializers.ValidationError({"budget": "Budget is required when boost post is enabled."})
        if data.get('budget') and data.get('budget') < 10:
            raise serializers.ValidationError({"budget": "Minimum budget is 10 Rupees."})
        return data



class VendorStoreSerializer(serializers.ModelSerializer):
    # Nested child serializers
    working_hours = StoreWorkingHourSerializer(source='user.working_hours', many=True, read_only=True)
    spotlight_products = SpotlightProductSerializer(source='user.spotlightproduct_set', many=True, read_only=True)
    posts = PostSerializer(source='user.post_set', many=True, read_only=True)
    reels = ReelSerializer(source='user.reel_set', many=True, read_only=True)
    banners = BannerCampaignSerializer(source='user.banners', many=True, read_only=True)

    class Meta:
        model = vendor_store
        fields = [
            'id', 'user',
            'working_hours',
            'spotlight_products',
            'posts',
            'reels',
            'banners',
        ]

        

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'



class CashBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBalance
        fields = ['balance', 'updated_at']

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


class product_serializer(serializers.ModelSerializer):
    addons = ProductAddonSerializer(many=True, required=False)
    print_variants = PrintVariantSerializer(many=True, required=False)
    customize_print_variants = CustomizePrintVariantSerializer(many=True, required=False)

    class Meta:
        model = product
        fields = '__all__'  # or list fields + 'addons', 'print_variants', 'customize_print_variants'

    def create(self, validated_data):
        addons_data = validated_data.pop('addons', [])
        variants_data = validated_data.pop('print_variants', [])
        customize_data = validated_data.pop('customize_print_variants', [])

        instance = product.objects.create(**validated_data)

        for addon in addons_data:
            product_addon.objects.create(product=instance, **addon)

        for variant in variants_data:
            PrintVariant.objects.create(product=instance, **variant)

        for custom in customize_data:
            CustomizePrintVariant.objects.create(product=instance, **custom)

        return instance

    def update(self, instance, validated_data):
        ## Pop nested data
        addons_data = validated_data.pop('addons', [])
        variants_data = validated_data.pop('print_variants', [])
        customize_data = validated_data.pop('customize_print_variants', [])

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle addons: clear old and add new
        if addons_data:
            product_addon.objects.filter(product=instance).delete()
            for addon in addons_data:
                product_addon.objects.create(product=instance, **addon)

        # Handle print variants
        if variants_data:
            PrintVariant.objects.filter(product=instance).delete()
            for variant in variants_data:
                PrintVariant.objects.create(product=instance, **variant)

        # Handle customize print variants
        if customize_data:
            CustomizePrintVariant.objects.filter(product=instance).delete()
            for custom in customize_data:
                CustomizePrintVariant.objects.create(product=instance, **custom)

        return instance




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
    items = SaleItemSerializer(many=True)
    wholesale_invoice = PosWholesaleSerializer(write_only=True, required=False)  # Add this line
    bank_details = vendor_bank_serializer(source="bank", read_only=True)
    customer_details = vendor_customers_serializer(source="customer", read_only=True)

    wholesale_invoice_details = serializers.SerializerMethodField(read_only=True)

    company_profile_detials = CompanyProfileSerializer(source="company_profile", read_only=True)
    customer_detials = vendor_customers_serializer(source="customer", read_only=True)
    advance_bank_details = vendor_bank_serializer(source="advance_bank", read_only=True)

    # Read-only totals
    total_items = serializers.IntegerField(read_only=True)
    total_amount_before_discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'payment_method', 'company_profile', 'customer', 'company_profile_detials', 'customer_detials',
            'discount_percentage', 'advance_amount', 'advance_bank', 'advance_bank_details', 'balance_amount',  'credit_date', 'is_wholesale_rate',
            'items', 'total_items', 'total_amount_before_discount',
            'discount_amount', 'total_amount', 'wholesale_invoice_details', 'wholesale_invoice', 'bank_details', 'customer_details'
        ]

    def get_wholesale_invoice_details(self, obj):
        invoice = obj.wholesales.first()  # fetch first linked wholesale invoice
        if invoice:
            return PosWholesaleSerializer(invoice).data
        return None

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        wholesale_data = validated_data.pop('wholesale_invoice', None)
        validated_data.pop('user', None)

        try:
            with transaction.atomic():
                # Create Sale
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

                # Update totals AFTER items are created
                total_items = sum(item.quantity for item in sale.items.all())
                total_amount_before_discount = sum(item.quantity * item.price for item in sale.items.all())
                discount_amount = total_amount_before_discount * (sale.discount_percentage or 0) / 100
                total_amount = total_amount_before_discount - discount_amount
                advance_amount = validated_data.get('advance_amount', 0)
                balance_amount = total_amount - advance_amount

                sale.total_items = total_items
                sale.total_amount_before_discount = total_amount_before_discount
                sale.discount_amount = discount_amount
                sale.total_amount = total_amount
                sale.balance_amount = balance_amount
                sale.save()

                if sale.is_wholesale_rate and wholesale_data:
                    print('-------------------1------------------')
                else:
                    print('-------------------2------------------')

                # Create Wholesale Invoice if applicable
                if sale.is_wholesale_rate and wholesale_data:
                    pos_wholesale.objects.create(
                        user=sale.user,
                        sale=sale,
                        **wholesale_data
                    )

                return sale

        except IntegrityError as e:
            raise ValidationError({"detail": str(e)})
        except Exception as e:
            raise ValidationError({"detail": f"An unexpected error occurred: {str(e)}"})


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
        fields = ["id", "transaction_type", "reference_id", "description", "amount", "created_at"]

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
        items_data = validated_data.pop('items', [])

        # Update Purchase fields except purchase_code
        for attr, value in validated_data.items():
            if attr != 'purchase_code':  # prevent manual change
                setattr(instance, attr, value)
        instance.save()

        # Replace all purchase items
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
    
    