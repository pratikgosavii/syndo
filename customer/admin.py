from django.contrib import admin

# Register your models here.


from .models import *


admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Address)
admin.site.register(ReturnExchange)
admin.site.register(Cart)
admin.site.register(PrintJob)
admin.site.register(PrintFile)
admin.site.register(Review)
admin.site.register(Follower)
admin.site.register(Favourite)
admin.site.register(FavouriteStore)
admin.site.register(SupportTicket)
admin.site.register(TicketMessage)
admin.site.register(ProductRequest)
admin.site.register(OrderPrintFile)