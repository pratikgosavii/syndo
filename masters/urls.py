from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static




from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'customer-address', customer_address_ViewSet, basename='pet-test-booking')
router.register(r'company', CompanyViewSet, basename='company')



urlpatterns = [


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

    path('add-expense-category/', add_expense_category, name='add_expense_category'),  # create or fetch list of admins
    path('update-expense-category/<expense_category_id>', update_expense_category, name='update_expense_category'),  # create or fetch list of admins
    path('list-expense-category/', list_expense_category, name='list_expense_category'),  # create or fetch list of admins
    path('delete-expense-category/<expense_category_id>', delete_expense_category, name='delete_expense_category'),  # create or fetch list of admins

    # path('add-customer-address/', add_customer_address.as_view(), name='add_customer_address'),  # create or fetch list of admins
    path('update-customer-address/<customer_address_id>', update_customer_address, name='update_customer_address'),  # create or fetch list of admins
    path('list-customer-address/', list_customer_address, name='list_customer_address'),  # create or fetch list of admins
    path('delete-customer-address/<customer_address_id>', delete_customer_address, name='delete_customer_address'),  # create or fetch list of admins
    # path('get-customer-address/', get_customer_address.as_view() , name='get_customer_address '), 

    
    path('add-home-banner/', add_home_banner, name='add_home_banner'),  # create or fetch list of admins
    path('update-home-banner/<home_banner_id>', update_home_banner, name='update_home_banner'),  # create or fetch list of admins
    path('list-home-banner/', list_home_banner, name='list_home_banner'),  # create or fetch list of admins
    path('delete-home-banner/<home_banner_id>', delete_home_banner, name='delete_home_banner'),  # create or fetch list of admins
    path('get-home-banner/', get_home_banner, name='get_home_banner'), 

]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)