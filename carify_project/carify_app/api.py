from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Category, Product, ProductMedia, Order, OrderItem, Payment
from .serializers import (
    CategorySerializer, ProductSerializer, ProductMediaSerializer,
    OrderSerializer, OrderItemSerializer, PaymentSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related('media')
    serializer_class = ProductSerializer

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