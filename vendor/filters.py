import django_filters
from .models import *

class productFilter(django_filters.FilterSet):
    class Meta:
        model = product
        exclude = ['image', 'gallery_images', 'user']  # ⛔ Exclude unsupported field
