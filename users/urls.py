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
    path('login-admin/', login_admin, name='login_admin'),
    path('update-user/', UserUpdateView.as_view(), name='UserUpdateView'),
    path('get-user/', UsergetView.as_view(), name='UsergetView'),
    path('reset-password/', ResetPasswordView.as_view(), name='ResetPasswordView'),
    path('logout/', logout_page, name='logout'),
    
    path('user_list/', user_list, name='user_list'),

    path('roles/create/', role_create, name='role_create'),
    path('roles/<int:pk>/edit/', role_update, name='role_update'),
    path('roles-list/', role_list, name='role_list'),

    path('users/<int:user_id>/assign-roles/', assign_roles_to_user, name='assign_roles_to_user'),

] + router.urls
