from django.urls import path

from .views import *

from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static





from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='user-profile')
# router.register(r'user-kyc', User_KYCViewSet, basename='user-kyc')


urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('register-device-token/', RegisterDeviceTokenAPIView.as_view(), name='RegisterDeviceTokenAPIView'),
    path('login-admin/', login_admin, name='login_admin'),
    path('login-vendor/', login_vendor, name='login_vendor'),
    path('update-user/', UserUpdateView.as_view(), name='UserUpdateView'),
    path('get-user/', UsergetView.as_view(), name='UsergetView'),
    path('delete-user/', DeleteUserAPIView.as_view(), name='DeleteUserAPIView'),
    path('reset-password/', ResetPasswordView.as_view(), name='ResetPasswordView'),
    path('logout/', logout_page, name='logout'),
    
    path('user_list/', user_list, name='user_list'),
    path('list-user-customer/', list_user_customer, name='list_user_customer'),
    path('list-user-vendor/', list_user_vendor, name='list_user_vendor'),

    path('roles/create/', role_create, name='role_create'),
    path('roles/<int:pk>/edit/', role_update, name='role_update'),
    path('roles-list/', role_list, name='role_list'),

    path('users/add/', create_user_with_roles, name='add_user_with_roles'),
    path('users/<int:user_id>/assign-roles/', assign_roles_to_user, name='assign_roles_to_user'),
    
    # Toggle APIs
    path('toggle-user-status/', toggle_user_status, name='toggle_user_status'),
    path('toggle-global-supplier/', toggle_global_supplier, name='toggle_global_supplier'),

] + router.urls
