from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static




from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'company-profile', CompanyProfileViewSet, basename='CompanyProfileViewSet')
router.register(r'product', ProductViewSet, basename='product')
router.register(r'addon', AddonViewSet, basename='AddonViewSet')
router.register(r'product-addon', ProductAddonViewSet, basename='ProductAddonViewSet')
router.register(r'spotlight-product', SpotlightProductViewSet, basename='ProductAddon')
router.register(r'expense', ExpenseViewSet, basename='ExpenseViewSet')



urlpatterns = [


    path('add-company-profile/', add_company_profile, name='add_company_profile'),
    path('update-company-profile/<company_profile_id>', update_company_profile, name='update_company_profile'),
    path('delete-company-profile/<company_profile_id>', delete_company_profile, name='delete_company_profile'),
    path('list-company-profile/', list_company_profile, name='list_company_profile'),
    
    path('add-vendor/', add_vendor, name='add_vendor'),
    path('update-vendor/<vendor_id>', update_vendor, name='update_vendor'),
    path('delete-vendor/<vendor_id>', delete_vendor, name='delete_vendor'),
    path('list-vendor/', list_vendor, name='list_vendor'),
    
    path('add-customer/', add_customer, name='add_customer'),
    path('update-customer/<customer_id>', update_customer, name='update_customer'),
    path('delete-customer/<customer_id>', delete_customer, name='delete_customer'),
    path('list-customer/', list_customer, name='list_customer'),
    
    path('add-product/', add_product, name='add_product'),
    path('update-product/<int:product_id>/', update_product, name='update_product'),
    path('delete_product/<int:product_id>/', delete_product, name='delete_product'),
    path('list-product/', list_product, name='list_product'),
    
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



]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)