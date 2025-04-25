from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static




from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'customer-address', customer_address_ViewSet, basename='pet-test-booking')


urlpatterns = [


    

    path('add-coupon/', add_coupon, name='add_coupon'),
    path('update-coupon/<coupon_id>', update_coupon, name='update_coupon'),
    path('delete-coupon/<coupon_id>', delete_coupon, name='delete_coupon'),
    path('list-coupon/', list_coupon, name='list_coupon'),
    path('get-coupon/', get_coupon.as_view(), name='get_coupon'),

    path('add-event/', add_event, name='add_event'),
    path('update-event/<event_id>', update_event, name='update_event'),
    path('delete-event/<event_id>', delete_event, name='delete_event'),
    path('list-event/', list_event, name='list_event'),
    path('get-event/', get_event.as_view(), name='get_event'),

    path('add-testimonials/', add_testimonials, name='add_testimonials'),  # create or fetch list of admins
    path('update-testimonials/<testimonials_id>', update_testimonials, name='update_testimonials'),  # create or fetch list of admins
    path('list-testimonials/', list_testimonials, name='list_testimonials'),  # create or fetch list of admins
    path('delete-testimonials/<testimonials_id>', delete_testimonials, name='delete_testimonials'),  # create or fetch list of admins
    path('get-testimonials/', get_testimonials.as_view(), name='get_testimonials'), 

    path('add-product-category/', add_product_category, name='add_product_category'),  # create or fetch list of admins
    path('update-product-category/<product_category_id>', update_product_category, name='update_product_category'),  # create or fetch list of admins
    path('list-product-category/', list_product_category, name='list_product_category'),  # create or fetch list of admins
    path('delete-product-category/<product_category_id>', delete_product_category, name='delete_product_category'),  # create or fetch list of admins
    path('get-product-category/', get_product_category.as_view() , name='get_product_category '), 

    # path('add-customer-address/', add_customer_address.as_view(), name='add_customer_address'),  # create or fetch list of admins
    path('update-customer-address/<customer_address_id>', update_customer_address, name='update_customer_address'),  # create or fetch list of admins
    path('list-customer-address/', list_customer_address, name='list_customer_address'),  # create or fetch list of admins
    path('delete-customer-address/<customer_address_id>', delete_customer_address, name='delete_customer_address'),  # create or fetch list of admins
    # path('get-customer-address/', get_customer_address.as_view() , name='get_customer_address '), 

    path('add-product/', add_product, name='add_product'),
    path('update-product/<product_id>', update_product, name='update_product'),
    path('delete-product/<product_id>', delete_product, name='delete_product'),
    path('list-product/', list_product, name='list_product'),
    path('get-product/', get_product.as_view(), name='get_product'),

    
    path('add-home-banner/', add_home_banner, name='add_home_banner'),  # create or fetch list of admins
    path('update-home-banner/<home_banner_id>', update_home_banner, name='update_home_banner'),  # create or fetch list of admins
    path('list-home-banner/', list_home_banner, name='list_home_banner'),  # create or fetch list of admins
    path('delete-home-banner/<home_banner_id>', delete_home_banner, name='delete_home_banner'),  # create or fetch list of admins
    path('get-home-banner/', get_home_banner, name='get_home_banner'), 

]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)