import django_filters
from .models import *

class productFilter(django_filters.FilterSet):
    class Meta:
        model = product
        exclude = ['image', 'gallery_images', 'user']  # ⛔ Exclude unsupported field



class couponFilter(django_filters.FilterSet):
    class Meta:
        model = coupon
        exclude = ['image']  # ⛔ Exclude unsupported field




class ProductFilter(django_filters.FilterSet):
    # Extra handy filters
    name = django_filters.CharFilter(lookup_expr="icontains")
    brand_name = django_filters.CharFilter(lookup_expr="icontains")
    color = django_filters.CharFilter(lookup_expr="icontains")
    size = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")

    min_price = django_filters.NumberFilter(field_name="sales_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="sales_price", lookup_expr="lte")

    expiry_before = django_filters.DateFilter(field_name="expiry_date", lookup_expr="lte")
    expiry_after = django_filters.DateFilter(field_name="expiry_date", lookup_expr="gte")

    class Meta:
        model = product
        exclude = ["image", "gallery_images"]  