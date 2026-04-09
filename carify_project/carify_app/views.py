from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import stripe
from .models import Product, ProductMedia, Order, OrderItem, Payment
from .forms import ProductForm, ProductMediaFormset, SellerRegistrationForm

stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):
    """Render the landing page with featured products."""
    products = Product.objects.all().prefetch_related('media')
    return render(request, 'home.html', {'products': products})


def product_list(request):
    """Display list of products"""
    products = Product.objects.all().prefetch_related('media')
    return render(request, 'product_list.html', {'products': products})

def product_detail(request, product_id):
    """Display product detail with gallery and video"""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})

def seller_register(request):
    """Register a new seller account."""
    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('carify_app:product_list')
    else:
        form = SellerRegistrationForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def seller_add_product(request):
    """Allow a seller to add a new product with images and video"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = ProductMediaFormset(request.POST, request.FILES, queryset=ProductMedia.objects.none())
        if form.is_valid() and formset.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            for media_form in formset:
                if media_form.cleaned_data and not media_form.cleaned_data.get('DELETE', False):
                    media = media_form.save(commit=False)
                    media.product = product
                    media.save()
            return redirect('carify_app:product_detail', product_id=product.id)
    else:
        form = ProductForm()
        formset = ProductMediaFormset(queryset=ProductMedia.objects.none())

    return render(request, 'product_create.html', {
        'form': form,
        'formset': formset,
    })

@login_required
def seller_dashboard(request):
    """Main dashboard overview for sellers."""
    # Ensure user has a profile or basic products
    products = Product.objects.filter(seller=request.user)
    return render(request, 'seller_dashboard_home.html', {
        'products': products
    })

@login_required
def seller_products(request):
    """List seller products in the dashboard."""
    products = Product.objects.filter(seller=request.user).prefetch_related('media', 'category')
    return render(request, 'seller_dashboard_products.html', {
        'products': products
    })

@login_required
def create_checkout_session(request, product_id):
    """Create a Stripe checkout session for a single product"""
    product = get_object_or_404(Product, id=product_id)
    
    order = Order.objects.create(
        buyer=request.user,
        total_amount=product.price
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        price=product.price
    )
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                        'description': product.description[:200],
                    },
                    'unit_amount': int(product.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/payment/success/'),
            cancel_url=request.build_absolute_uri('/payment/cancel/'),
            metadata={
                'order_id': order.id
            }
        )
        
        return JsonResponse({'checkout_url': checkout_session.url})
    except Exception as e:
        order.delete()
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def payment_success(request):
    """Handle successful payment"""
    return render(request, 'payment_success.html')

@login_required
def payment_cancel(request):
    """Handle cancelled payment"""
    return render(request, 'payment_cancel.html')

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    if event.type == 'checkout.session.completed':
        session = event.data.object
        order_id = session.metadata.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.status = 'paid'
                order.save()
                
                Payment.objects.create(
                    order=order,
                    payment_method='stripe',
                    transaction_id=session.payment_intent,
                    amount=order.total_amount,
                    status='completed'
                )
            except Order.DoesNotExist:
                pass
    return JsonResponse({'status': 'success'})

