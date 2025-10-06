from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static




from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'customer-order', CustomerOrderViewSet, basename='CustomerOrderViewSet')
router.register(r'address', AddressViewSet, basename='address')
router.register(r'cart', CartViewSet, basename='cart')

router.register(r'favourites', FavouriteViewSet, basename='favourites')

urlpatterns = [
    
path('stores/', VendorStoreListAPIView.as_view(), name='vendor-store-list'),
path('stores/<int:id>/', VendorStoreListAPIView.as_view(), name='vendor-store-detail'),

path('list-products/', list_products.as_view(), name='list_products'),
path('follow/<int:user_id>/', FollowUserAPIView.as_view(), name='follow-user'),
path('unfollow/<int:user_id>/', UnfollowUserAPIView.as_view(), name='unfollow-user'),
path('follow/', FollowUserAPIView.as_view(), name='following-list'),      # GET = who I'm following
path('unfollow/', UnfollowUserAPIView.as_view(), name='followers-list'),  # GET = who follows me

path('vendor-banner/', RandomBannerAPIView.as_view(), name='RandomBannerAPIView'),  # GET = who follows me
path('spotlight-product/', SpotlightProductView.as_view(), name='SpotlightProduct'),  # GET = who follows me
path('reels/', reelsView.as_view(), name='reelsView'),  # GET = who follows me
path('offers/', offersView.as_view(), name='offersView'),  # GET = who follows me

path('coupons/', CartCouponAPIView.as_view(), name='CartCouponAPIView'),  # GET = who follows me


]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)