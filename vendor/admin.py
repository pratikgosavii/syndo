from django.contrib import admin

# Register your models here.

from .models import *


admin.site.register(product)
admin.site.register(ProductSerial)
admin.site.register(addon)
admin.site.register(vendor_store)
admin.site.register(product_addon)
admin.site.register(StoreWorkingHour)
admin.site.register(OnlineStoreSetting)
admin.site.register(ProductSettings)