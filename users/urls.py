from django.urls import path

from .views import *

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('login-admin/', login_admin, name='login_admin'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('update-user/', UserUpdateView.as_view(), name='UserUpdateView'),
    path('get-user/', UsergetView.as_view(), name='UsergetView'),
    path('reset-password/', ResetPasswordView.as_view(), name='ResetPasswordView'),
    path('logout/', logout_page, name='logout'),
    
    path('user_list/', user_list, name='user_list'),
]
