import uuid
import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subcategories')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    shop_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='seller_logos/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # Percentage fee
    revenue_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.shop_name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def first_media_image_url(self):
        """Helper property to get the first image URL from related media or the main image field."""
        try:
            if self.image:
                return self.image.url
        except ValueError:
            pass # The file doesn't exist

        # Fallback to related ProductMedia if no main image exists
        first_img = self.media.filter(media_type='image').first()
        if first_img and first_img.image:
            try:
                return first_img.image.url
            except ValueError:
                pass
        return None

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text="e.g., Small, Large, Blue, Red")
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    price_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.name}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5)  # 1-5
    comment = models.TextField()
    helpful_votes = models.ManyToManyField(User, related_name='helpful_reviews', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"

class ProductMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='image')
    image = models.ImageField(upload_to='product_media/images/', blank=True, null=True)
    video = models.FileField(upload_to='product_media/videos/', blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def clean(self):
        if self.media_type == 'image' and not self.image:
            raise ValidationError('Image file is required for image media.')
        if self.media_type == 'video' and not self.video:
            raise ValidationError('Video file is required for video media.')
        if self.image and self.video:
            raise ValidationError('Only one media file type can be uploaded per entry.')

    def __str__(self):
        return f"{self.product.name} {self.media_type} ({self.caption or 'media'})"

class ProductQuestion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Q: {self.question[:50]}..."

class ProductAnswer(models.Model):
    question = models.ForeignKey(ProductQuestion, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.TextField()
    is_seller_response = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_seller_response', 'created_at']

    def __str__(self):
        return f"A: {self.answer[:50]}..."

class Service(models.Model):
    """For listing car care services like detailing, maintenance, etc."""
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Starting price")
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True, related_name='wishlisted_by')
    services = models.ManyToManyField(Service, blank=True, related_name='wishlisted_by')
    
    def __str__(self):
        return f"{self.user.username}'s Wishlist"

class OTPToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_tokens')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.otp_code:
            # Generate a secure 6-digit code
            self.otp_code = f"{secrets.randbelow(1000000):06d}"
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.user.username} (Code: {self.otp_code})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            # Generate a production-grade tracking ID
            self.tracking_id = f"CA-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} by {self.buyer.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        # Add more payment methods as needed
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, completed, failed, refunded
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order {self.order.id}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)  # For guest carts
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.filter(is_saved_for_later=False))

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    is_saved_for_later = models.BooleanField(default=False)

    def get_cost(self):
        base_price = self.product.price
        if self.variant:
            base_price += self.variant.price_extra
        return base_price * self.quantity
