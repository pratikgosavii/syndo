from rest_framework import serializers
from .models import *



class coupon_serializer(serializers.ModelSerializer):
    class Meta:
        model = coupon
        fields = '__all__'




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
        

class product_serializer(serializers.ModelSerializer):
    
    class Meta:
        model = product
        fields = '__all__'
        read_only_fields = ['user']  


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


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'
        read_only_fields = ['user']


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['user']




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



class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'amount']

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)
    total_items = serializers.ReadOnlyField()
    total_amount = serializers.ReadOnlyField()
    total_tax = serializers.ReadOnlyField()
    final_amount = serializers.ReadOnlyField()

    class Meta:
        model = Sale
        fields = ['id', 'party', 'discount_percentage', 'credit_time_days', 'created_at',
                  'items', 'total_items', 'total_amount', 'total_tax', 'final_amount']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(user=self.context['request'].user, **validated_data)
        for item in items_data:
            SaleItem.objects.create(user=self.context['request'].user, sale=sale, **item)
        return sale

        
class StoreWorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreWorkingHour
        fields = ['id', 'day', 'open_time', 'close_time', 'is_open']



class CashBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBalance
        fields = ['balance', 'updated_at']

class vendor_bank_serializer(serializers.ModelSerializer):
    class Meta:
        model = vendor_bank
        fields = '__all__'


class CashTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashTransfer
        fields = ['id', 'bank_account', 'amount', 'created_at', 'status']
        read_only_fields = ['created_at', 'status']
        



from rest_framework import serializers

class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'price']


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'payment_method', 'company_profile', 'party', 'customer',
            'discount_percentage', 'credit_time_days', 'is_wholesale_rate',
            'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(**validated_data)

        for item in items_data:
            SaleItem.objects.create(user=sale.user, sale=sale, **item)
        return sale



class DeliverySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliverySettings
        fields = '__all__'



class DeliveryBoySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryBoy
        fields = '__all__'


class DeliveryModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryMode
        fields = ['is_auto_assign_enabled', 'is_self_delivery_enabled']

    def validate(self, attrs):
        user = self.context['request'].user
        if DeliveryMode.objects.filter(user=user).exists():
            raise serializers.ValidationError("DeliveryMode for this user already exists.")
        return attrs

    # 👇 This is safe: don't set user again, just return default create
    def create(self, validated_data):
        return super().create(validated_data)



class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'date', 'time', 'description']  # adjust fields as per your model

        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['user']