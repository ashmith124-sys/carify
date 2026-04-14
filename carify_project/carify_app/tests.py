from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Product, Service, Category, Cart, CartItem, Order
from django.urls import reverse
from django.test import override_settings

class CartCheckoutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            price=100.00,
            quantity=10,
            seller=self.user,
            category=self.category
        )
        self.service = Service.objects.create(
            name='Test Service',
            price=50.00,
            seller=self.user,
            category=self.category
        )
        self.client.login(username='testuser', password='password')

    @override_settings(STRIPE_SECRET_KEY='sk_test_your_stripe_secret_key_here')
    def test_checkout_with_service_succeeds(self):
        # Create a cart with a service
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, service=self.service, quantity=1)
        
        # Try to initialize checkout
        response = self.client.get(reverse('carify_app:create_checkout'))
        
        # It should redirect to success page (due to dummy keys in test environment)
        self.assertEqual(response.status_code, 302)
        self.assertIn('payment/success', response.url)
        
        # Check if an order was created and has the service
        order = Order.objects.filter(buyer=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_amount, 50.00)
        self.assertTrue(order.items.filter(service=self.service).exists())
