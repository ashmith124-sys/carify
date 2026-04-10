from rest_framework import serializers
from .models import (
    Category, Product, ProductMedia, Order, OrderItem, Payment, 
    SellerProfile, Service, Wishlist, ProductVariant, Review, Cart, CartItem,
    ProductQuestion, ProductAnswer
)

class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ['id', 'media_type', 'image', 'video', 'caption', 'sort_order', 'created_at']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'sku', 'price_extra', 'stock']

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    helpful_votes_count = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'username', 'rating', 'comment', 'helpful_votes_count', 'created_at']

    def get_helpful_votes_count(self, obj):
        return obj.helpful_votes.count()

class ProductAnswerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductAnswer
        fields = ['id', 'question', 'user', 'username', 'answer', 'is_seller_response', 'created_at']

class ProductQuestionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    answers = ProductAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = ProductQuestion
        fields = ['id', 'product', 'user', 'username', 'question', 'answers', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    media = ProductMediaSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    first_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'quantity', 'category', 
            'image', 'media', 'variants', 'reviews', 'first_image', 
            'average_rating', 'created_at', 'updated_at'
        ]

    def get_first_image(self, obj):
        if obj.image:
            return obj.image.url
        first_media = obj.media.filter(media_type='image').first()
        if first_media and first_media.image:
            return first_media.image.url
        return None

    def get_average_rating(self, obj):
        from django.db.models import Avg
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'products']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'buyer', 'items', 'total_amount', 'status', 'created_at', 'updated_at']

    def get_total_amount(self, obj):
        return sum(item.price * item.quantity for item in obj.items.all())

class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'order', 'amount', 'payment_method', 'transaction_id', 'status', 'created_at']

class SellerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SellerProfile
        fields = ['id', 'user', 'username', 'shop_name', 'description', 'logo', 'is_approved', 'created_at']

class ServiceSerializer(serializers.ModelSerializer):
    seller_shop = serializers.CharField(source='seller.seller_profile.shop_name', read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'image', 'seller', 'seller_shop', 'category', 'created_at', 'updated_at']

class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'products', 'services']

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product')
    variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), source='variant', required=False)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'variant', 'variant_id', 'quantity', 'is_saved_for_later', 'get_cost']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'session_id', 'items', 'get_total_price', 'created_at', 'updated_at']