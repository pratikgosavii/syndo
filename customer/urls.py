from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static




from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'customer-order', CustomerOrderViewSet, basename='CustomerOrderViewSet')
router.register(r'address', AddressViewSet, basename='address')
router.register(r'cart', CartViewSet, basename='cart')

router.register(r'customer-product-review', CustomerProductReviewViewSet, basename='customer_review')

router.register(r'favourites', FavouriteViewSet, basename='favourites')
router.register(r'favourites-store', FavouriteStoreViewSet, basename='favourites_store')

router.register("requests", ProductRequestViewSet, basename="product-request")

router.register(r'support/tickets', SupportTicketViewSet, basename='support-ticket')


urlpatterns = [

path('return-exchange/', ReturnExchangeAPIView.as_view(), name='return-exchange'),
    
path('stores/', VendorStoreListAPIView.as_view(), name='vendor-store-list'),
path('stores/<int:id>/', VendorStoreListAPIView.as_view(), name='vendor-store-detail'),


path('list-products/', ListProducts.as_view(), name='list_products'),
path('list-posts/', ListPosts.as_view(), name='list_posts'),
# path('products-details/<product_id>/', products_details.as_view(), name='products_details'),
path('follow/<int:user_id>/', FollowUserAPIView.as_view(), name='follow-user'),
path('unfollow/<int:user_id>/', UnfollowUserAPIView.as_view(), name='unfollow-user'),
path('follow/', FollowUserAPIView.as_view(), name='following-list'),      # GET = who I'm following
path('unfollow/', UnfollowUserAPIView.as_view(), name='followers-list'),  # GET = who follows me

path('vendor-banner/', RandomBannerAPIView.as_view(), name='RandomBannerAPIView'),  # GET = who follows me
path('spotlight-product/', SpotlightProductView.as_view(), name='SpotlightProduct'),  # GET = who follows me
path('reels/', reelsView.as_view(), name='reelsView'),  # GET = who follows me
path('offers/', offersView.as_view(), name='offersView'),  # GET = who follows me

path('coupons/', CartCouponAPIView.as_view(), name='CartCouponAPIView'),  # GET = who follows me

path('products/search/', ProductSearchAPIView.as_view(), name='search-products'),

path('stores-by-category/', StoreByCategoryView.as_view(), name='stores-by-category'),
path('stores-by-subcategory/', StoreBySubCategoryView.as_view(), name='stores-by-subcategory'),


]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)