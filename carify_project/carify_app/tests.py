from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Product, Service, Category, Cart, CartItem, Order, SellerProfile
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
        
        # It should redirect to the demo payment page when Stripe is in placeholder mode
        self.assertEqual(response.status_code, 302)
        self.assertIn('payment/demo', response.url)
        
        # Check if an order was created and has the service
        order = Order.objects.filter(buyer=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_amount, 50.00)
        self.assertTrue(order.items.filter(service=self.service).exists())

        confirm = self.client.post(reverse('carify_app:complete_demo_payment'), {'payment_method': 'card'})
        self.assertEqual(confirm.status_code, 302)
        self.assertIn('payment/success', confirm.url)

        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')

    @override_settings(STRIPE_SECRET_KEY='', DEBUG=True)
    def test_checkout_with_missing_stripe_key_uses_demo_mode(self):
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        response = self.client.get(reverse('carify_app:create_checkout'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('payment/demo', response.url)

        confirm = self.client.post(reverse('carify_app:complete_demo_payment'), {'payment_method': 'affirm'})
        self.assertEqual(confirm.status_code, 302)
        self.assertIn('payment/success', confirm.url)

        order = Order.objects.filter(buyer=self.user).first()
        self.assertIsNotNone(order)
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class PublicSellerProfileTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='seller', password='password')
        SellerProfile.objects.create(user=self.seller, shop_name='Seller Garage')

    def test_public_seller_profile_renders(self):
        response = self.client.get(reverse('carify_app:public_seller_profile', args=[self.seller.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seller Garage')


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class CategoryAdminPageTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.client.login(username='admin', password='password')

    def test_manage_categories_shows_create_catalog_button(self):
        response = self.client.get(reverse('carify_app:manage_categories'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Catalog')
        self.assertContains(response, reverse('carify_app:add_category'))
