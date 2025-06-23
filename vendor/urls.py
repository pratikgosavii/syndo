from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static




from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'Coupon', CouponViewSet, basename='CouponViewSet')
router.register(r'OnlineStoreSetting', OnlineStoreSettingViewSet, basename='OnlineStoreSettingViewSet')
router.register(r'company-profile', CompanyProfileViewSet, basename='CompanyProfileViewSet')
router.register(r'product', ProductViewSet, basename='product')
router.register(r'productSetting', ProductSettingsViewSet, basename='ProductSettingsViewSet')
router.register(r'addon', AddonViewSet, basename='AddonViewSet')
router.register(r'product-addon', ProductAddonViewSet, basename='ProductAddonViewSet')
router.register(r'spotlight-product', SpotlightProductViewSet, basename='ProductAddon')
router.register(r'post', PostViewSet, basename='PostViewSet')
router.register(r'reel', ReelViewSet, basename='ReelViewSet')
router.register(r'expense', ExpenseViewSet, basename='ExpenseViewSet')



urlpatterns = [


    path('add-company-profile/', add_company_profile, name='add_company_profile'),
    path('update-company-profile/<company_profile_id>', update_company_profile, name='update_company_profile'),
    path('delete-company-profile/<company_profile_id>', delete_company_profile, name='delete_company_profile'),
    path('list-company-profile/', list_company_profile, name='list_company_profile'),
    
    path('add-coupon/', add_coupon, name='add_coupon'),
    path('update-coupon/<coupon_id>', update_coupon, name='update_coupon'),
    path('delete-coupon/<coupon_id>', delete_coupon, name='delete_coupon'),
    path('list-coupon/', list_coupon, name='list_coupon'),

    path('add-vendor/', add_vendor, name='add_vendor'),
    path('update-vendor/<vendor_id>', update_vendor, name='update_vendor'),
    path('delete-vendor/<vendor_id>', delete_vendor, name='delete_vendor'),
    path('list-vendor/', list_vendor, name='list_vendor'),

    path('add-party/', add_party, name='add_party'),
    path('update-party/<party_id>', update_party, name='update_party'),
    path('delete-party/<party_id>', delete_party, name='delete_party'),
    path('list-party/', list_party, name='list_party'),

    path('add-bank/', add_bank, name='add_bank'),
    path('update-bank/<bank_id>', update_bank, name='update_bank'),
    path('delete-bank/<bank_id>', delete_bank, name='delete_bank'),
    path('list-bank/', list_bank, name='list_bank'),
    
    path('add-customer/', add_customer, name='add_customer'),
    path('update-customer/<customer_id>', update_customer, name='update_customer'),
    path('delete-customer/<customer_id>', delete_customer, name='delete_customer'),
    path('list-customer/', list_customer, name='list_customer'),
    
    path('add-super-catalogue/', add_super_catalogue, name='add_super_catalogue'),
    path('add-to-super-catalogue/<product_id>', add_to_super_catalogue, name='add_to_super_catalogue'),
    path('update-super-catalogue/<int:super_catalogue_id>/', update_super_catalogue, name='update_super_catalogue'),
    path('delete_super-catalogue/<int:super_catalogue_id>/', delete_super_catalogue, name='delete_super_catalogue'),
    path('list-super-catalogue/', list_super_catalogue, name='list_super_catalogue'),
    
    path('add-product/', add_product, name='add_product'),
    path('update-product/<int:product_id>/', update_product, name='update_product'),
    path('delete_product/<int:product_id>/', delete_product, name='delete_product'),
    path('list-product/', list_product, name='list_product'),
    path('product-setting/', product_setting, name='product_settings'),
    
    path('add-expense/', add_expense, name='add_expense'),
    path('update-expense/<int:expense_id>/', update_expense, name='update_expense'),
    path('delete_expense/<int:expense_id>/', delete_expense, name='delete_expense'),
    path('list-expense/', list_expense, name='list_expense'),

    path('add-purchase/', add_purchase, name='add_purchase'),
    path('update-purchase/<int:purchase_id>/', update_purchase, name='update_purchase'),
    path('delete_purchase/<int:purchase_id>/', delete_purchase, name='delete_purchase'),
    path('list-purchase/', list_purchase, name='list_purchase'),

    
    path('add-addon/', add_addon, name='add_addon'),
    path('update-addon/<addon_id>', update_addon, name='update_addon'),
    path('delete_addon/<addon_id>', delete_addon, name='delete_addon'),
    path('list-addon/', list_addon, name='list_addon'),

    path('store-working-hours/', store_hours_view, name='store_hours'),
    path('online-store-setting/', online_store_setting, name='online_store_setting'),

    path('pos/', pos, name='create-sale'),
    path('list-sale/', list_sale, name='list_sale'),
    path('get_product_price/', get_product_price, name='get_product_price'),

    path('pos-wholesale/', pos_wholesale, name='pos_wholesale'),
    path('order-details/<order_id>', order_details, name='order_details'),
    path('order-list/', order_list, name='order_list'),
    # path('order-list/', pos, name='create-sale'),
    
    path('accept-order/<order_id>', accept_order, name='accept_order'),
    path('assign-delivery-boy/<order_id>', assign_delivery_boy, name='assign_delivery_boy'),
    



]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)