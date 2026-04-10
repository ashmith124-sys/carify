from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Category, Product, ProductMedia, Order, OrderItem, Payment, 
    SellerProfile, Service, Wishlist, ProductVariant, Review, Cart, CartItem
)
from .serializers import (
    CategorySerializer, ProductSerializer, ProductMediaSerializer,
    OrderSerializer, OrderItemSerializer, PaymentSerializer,
    SellerProfileSerializer, ServiceSerializer, WishlistSerializer,
    ProductVariantSerializer, ReviewSerializer, CartSerializer, CartItemSerializer,
    ProductQuestionSerializer, ProductAnswerSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related('media', 'variants', 'reviews')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category': ['exact'],
        'seller': ['exact'],
        'price': ['gte', 'lte'],
    }
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'reviews__rating']

    @action(detail=True, methods=['post'])
    def create_checkout(self, request, pk=None):
        """Create Stripe checkout session for a product"""
        product = self.get_object()
        return Response({
            'message': f'Checkout session for {product.name} would be created here',
            'product_id': product.id,
            'price': product.price
        })

class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_helpful(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response({'error': 'Must be logged in'}, status=status.HTTP_401_UNAUTHORIZED)
        review = self.get_object()
        if request.user in review.helpful_votes.all():
            review.helpful_votes.remove(request.user)
            added = False
        else:
            review.helpful_votes.add(request.user)
            added = True
        return Response({'helpful_votes_count': review.helpful_votes.count(), 'added': added})

class ProductQuestionViewSet(viewsets.ModelViewSet):
    queryset = ProductQuestion.objects.all()
    serializer_class = ProductQuestionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProductAnswerViewSet(viewsets.ModelViewSet):
    queryset = ProductAnswer.objects.all()
    serializer_class = ProductAnswerSerializer

    def perform_create(self, serializer):
        is_seller = getattr(self.request.user, 'seller_profile', None) is not None
        serializer.save(user=self.request.user, is_seller_response=is_seller)

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
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return Wishlist.objects.none()

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_id=session_id)
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))

        # Get or create cart
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            cart, _ = Cart.objects.get_or_create(session_id=session_id)

        # Check for existing item
        item = CartItem.objects.filter(cart=cart, product_id=product_id, variant_id=variant_id).first()
        if item:
            item.quantity += quantity
            item.save()
            serializer = self.get_serializer(item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Create new item
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cart=cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def toggle_saved(self, request, pk=None):
        item = self.get_object()
        item.is_saved_for_later = not item.is_saved_for_later
        item.save()
        return Response({'status': 'success', 'is_saved_for_later': item.is_saved_for_later})