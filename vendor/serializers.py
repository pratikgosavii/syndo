from rest_framework import serializers
from .models import *


class product_serializer(serializers.ModelSerializer):
    
    class Meta:
        model = product
        fields = '__all__'
        read_only_fields = ['user']  




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


