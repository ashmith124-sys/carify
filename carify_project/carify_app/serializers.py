from rest_framework import serializers
from .models import Category, Product, ProductMedia, Order, OrderItem, Payment, SellerProfile, Service, Wishlist


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ['id', 'media_type', 'image', 'video', 'caption', 'sort_order', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    media = ProductMediaSerializer(many=True, read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'category', 'image', 'media', 'first_image', 'created_at', 'updated_at']

    def get_first_image(self, obj):
        first_media = obj.media.filter(media_type='image').first()
        if first_media and first_media.image:
            return first_media.image.url
        return None


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