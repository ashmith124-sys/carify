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
router.register(r'reviews', api.ReviewViewSet)
router.register(r'carts', api.CartViewSet)
router.register(r'cart-items', api.CartItemViewSet)
router.register(r'variants', api.ProductVariantViewSet)
router.register(r'product-questions', api.ProductQuestionViewSet)
router.register(r'product-answers', api.ProductAnswerViewSet)

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),

    # Web interface endpoints
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/products/', views.seller_products, name='seller_products'),
    path('seller/product/add/', views.seller_add_product, name='seller_add_product'),
    
    # NEW Auth Flow
    path('accounts/signup/buyer/', views.buyer_register, name='buyer_register'),
    path('accounts/signup/seller/', views.seller_register, name='seller_register'),
    path('accounts/verify-otp/', views.verify_otp, name='verify_otp'),
    
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('checkout/initialize/', views.create_checkout_session, name='create_checkout'),
    
    # NEW Tracking
    path('order/track/', views.track_order, name='track_order'),
    
    # NEW Informational Pages
    path('about/', views.static_page, {'page_type': 'about'}, name='about'),
    path('services/', views.static_page, {'page_type': 'services'}, name='services'),
    path('manifesto/', views.static_page, {'page_type': 'manifesto'}, name='manifesto'),
    path('privacy/', views.static_page, {'page_type': 'privacy'}, name='privacy'),

    # Seller Dashboard Extensions
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/analytics/', views.seller_analytics, name='seller_analytics'),
    path('seller/settings/', views.seller_settings, name='seller_settings'),
    
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]