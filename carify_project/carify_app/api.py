from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductMedia, Order, OrderItem, Payment, SellerProfile, Service, Wishlist
from .serializers import (
    CategorySerializer, ProductSerializer, ProductMediaSerializer,
    OrderSerializer, OrderItemSerializer, PaymentSerializer,
    SellerProfileSerializer, ServiceSerializer, WishlistSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related('media')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'seller']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    @action(detail=True, methods=['post'])
    def create_checkout(self, request, pk=None):
        """Create Stripe checkout session for a product"""
        product = self.get_object()

        # This would integrate with Stripe to create a checkout session
        # For now, return a placeholder response
        return Response({
            'message': f'Checkout session for {product.name} would be created here',
            'product_id': product.id,
            'price': product.price
        })


class ProductMediaViewSet(viewsets.ModelViewSet):
    queryset = ProductMedia.objects.all()
    serializer_class = ProductMediaSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related('items__product')
    serializer_class = OrderSerializer


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class SellerProfileViewSet(viewsets.ModelViewSet):
    queryset = SellerProfile.objects.all()
    serializer_class = SellerProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['shop_name', 'description']

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'seller']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    
    def get_queryset(self):
        # Users should only see their own wishlists ideally, but for now we'll allow all for admin simplicity
        # or we could scope it: return self.queryset.filter(user=self.request.user) if self.request.user.is_authenticated else Wishlist.objects.none()
        return super().get_queryset()