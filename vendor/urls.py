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



urlpatterns = [


    path('add-company-profile/', add_company_profile, name='add_company_profile'),
    path('update-company-profile/<company_profile_id>', update_company_profile, name='update_company_profile'),
    path('delete-company-profile/<company_profile_id>', delete_company_profile, name='delete_company_profile'),
    path('list-company-profile/', list_company_profile, name='list_company_profile'),
    
    path('add-product/', add_product, name='add_product'),
    path('update-product/<int:product_id>/', update_product, name='update_product'),
    path('delete_product/<int:product_id>/', delete_product, name='delete_product'),
    path('list-product/', list_product, name='list_product'),
    # path('get-product/', get_product.as_view(), name='get_product'),

    
    path('add-addon/', add_addon, name='add_addon'),
    path('update-addon/<addon_id>', update_addon, name='update_addon'),
    path('delete_addon/<addon_id>', delete_addon, name='delete_addon'),
    path('list-addon/', list_addon, name='list_addon'),



]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)