from django.contrib import admin

# Register your models here.

from .models import *


admin.site.register(product)
admin.site.register(ProductSerial)
admin.site.register(addon)
admin.site.register(product_addon)