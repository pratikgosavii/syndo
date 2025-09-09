from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static




from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'customer-order', CustomerOrderViewSet, basename='CustomerOrderViewSet')



urlpatterns = [

path('stores/', VendorStoreListAPIView.as_view(), name='vendor-store-list'),
path('follow/<int:user_id>/', FollowUserAPIView.as_view(), name='follow-user'),
path('unfollow/<int:user_id>/', UnfollowUserAPIView.as_view(), name='unfollow-user'),
 

]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)