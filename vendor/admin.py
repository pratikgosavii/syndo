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
admin.site.register(Sale)
admin.site.register(DeliveryBoy)
admin.site.register(DeliveryMode)
admin.site.register(CompanyProfile)
admin.site.register(pos_wholesale)
admin.site.register(Purchase)
admin.site.register(vendor_bank)
admin.site.register(Expense)
admin.site.register(vendor_customers)
admin.site.register(vendor_vendors)
admin.site.register(NotificationCampaign)
admin.site.register(coupon)