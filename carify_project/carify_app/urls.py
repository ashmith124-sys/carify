from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api

app_name = 'carify_app'

# Create a router for API endpoints
router = DefaultRouter()
router.register(r'categories', api.CategoryViewSet)
router.register(r'products', api.ProductViewSet)
router.register(r'product-media', api.ProductMediaViewSet)
router.register(r'orders', api.OrderViewSet)
router.register(r'order-items', api.OrderItemViewSet)
router.register(r'payments', api.PaymentViewSet)
router.register(r'seller-profiles', api.SellerProfileViewSet)
router.register(r'services', api.ServiceViewSet)
router.register(r'wishlists', api.WishlistViewSet)

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),

    # Web interface endpoints
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/products/', views.seller_products, name='seller_products'),
    path('seller/product/add/', views.seller_add_product, name='seller_add_product'),
    path('accounts/signup/', views.seller_register, name='seller_register'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/checkout/', views.create_checkout_session, name='create_checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]