from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import stripe
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
import json
from .models import (
    Product, ProductMedia, Order, OrderItem, Payment, OTPToken, 
    SellerProfile, Cart, CartItem, ProductVariant, Category
)
from .forms import (
    ProductForm, ProductMediaFormset, SellerRegistrationForm, 
    BuyerRegistrationForm, OTPVerifyForm
)

stripe.api_key = settings.STRIPE_SECRET_KEY

def get_current_cart(request):
    """Helper to get current user/session cart."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart

def home(request):
    """Render the landing page with featured products."""
    products = Product.objects.all().prefetch_related('media', 'reviews').order_by('-created_at')[:8]
    categories = Category.objects.all()
    return render(request, 'home.html', {'products': products, 'categories': categories})

def product_list(request):
    """Display list of products with discovery infrastructure."""
    categories = Category.objects.all()
    return render(request, 'product_list.html', {'categories': categories})

def product_detail(request, product_id):
    """Display product detail with gallery, variants, and reviews."""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})

def buyer_register(request):
    """Register a new buyer account."""
    if request.method == 'POST':
        form = BuyerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = True
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome to CARIFY! Account created successfully.")
            return redirect('carify_app:home')
    else:
        form = BuyerRegistrationForm()
    return render(request, 'registration/signup.html', {'form': form, 'user_type': 'Buyer'})

def seller_register(request):
    """Register a new seller account."""
    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = True
            user.save()
            # Create Seller Profile
            SellerProfile.objects.create(
                user=user,
                shop_name=form.cleaned_data['shop_name'],
                description=form.cleaned_data.get('description', '')
            )
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Partner account initialized successfully.")
            return redirect('carify_app:seller_dashboard')
    else:
        form = SellerRegistrationForm()
    return render(request, 'registration/signup.html', {'form': form, 'user_type': 'Seller'})

def verify_otp(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('carify_app:home')
    
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if 'resend' in request.POST:
            # Resend OTP
            OTPToken.objects.filter(user=user, is_verified=False).update(is_expired=True)
            otp_token = OTPToken.objects.create(user=user)
            send_otp_email(user, otp_token.otp_code)
            messages.success(request, f"A new access key has been transmitted to {user.email}.")
            return redirect('carify_app:verify_otp')

        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            otp_token = OTPToken.objects.filter(user=user, otp_code=otp_code, is_verified=False).last()
            
            if otp_token and not otp_token.is_expired:
                otp_token.is_verified = True
                otp_token.save()
                user.is_active = True
                user.save()
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                del request.session['otp_user_id']
                messages.success(request, "OTP Verified! Welcome to Carify.")
                return redirect('carify_app:home')
            else:
                messages.error(request, "Invalid or expired OTP.")
    else:
        form = OTPVerifyForm()
    
    return render(request, 'registration/verify_otp.html', {'form': form, 'email': user.email})

def send_otp_email(user, code):
    """Helper to send OTP via email."""
    subject = "Verify your Carify account"
    message = f"Your OTP for verification is: {code}. It will expire in 10 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)
    print(f"DEBUG OTP SENT TO {user.email}: {code}")

def track_order(request):
    """Track an order by tracking ID."""
    order = None
    query = request.GET.get('tracking_id')
    if query:
        order = Order.objects.filter(tracking_id=query).first()
        if not order:
            messages.error(request, "Order not found. Please check your tracking ID.")
            
    return render(request, 'order_tracking.html', {'order': order, 'query': query})

@login_required
def create_checkout_session(request):
    """Create a Stripe checkout session for the entire current cart."""
    cart = get_current_cart(request)
    active_items = cart.items.filter(is_saved_for_later=False)
    if not active_items.exists():
        messages.error(request, "Empty_Cart_Cache. Please add items to initialize checkout.")
        return redirect('carify_app:product_list')

    # Create Order
    order = Order.objects.create(
        buyer=request.user,
        total_amount=cart.get_total_price()
    )

    line_items = []
    for item in active_items:
        # Create OrderItem
        unit_price = item.get_cost() / item.quantity
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=unit_price
        )

        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"{item.product.name} ({item.variant.name if item.variant else 'Standard'})",
                    'description': item.product.description[:200],
                },
                'unit_amount': int(unit_price * 100),
            },
            'quantity': item.quantity,
        })
    
    try:
        # DEV BYPASS: If using the default dummy keys, simulate a successful redirect
        if settings.STRIPE_SECRET_KEY == 'sk_test_your_stripe_secret_key_here':
            active_items.delete()
            order.status = 'paid'
            order.save()
            return redirect('/payment/success/')

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/payment/success/'),
            cancel_url=request.build_absolute_uri('/payment/cancel/'),
            metadata={'order_id': order.id}
        )
        
        return redirect(checkout_session.url)
    except Exception as e:
        order.delete()
        messages.error(request, f"Stripe_Error: {str(e)}")
        return redirect('carify_app:home')

@login_required
def payment_success(request):
    return render(request, 'payment_success.html')

@login_required
def payment_cancel(request):
    return render(request, 'payment_cancel.html')

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
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

                # Deduct inventory quantities
                for item in order.orderitem_set.all():
                    if item.product.quantity >= item.quantity:
                        item.product.quantity -= item.quantity
                        item.product.save()

                # Clear the buyer's ACTIVE cart items now that order is securely paid
                try:
                    cart = order.buyer.cart
                    if cart:
                        cart.items.filter(is_saved_for_later=False).delete()
                except Exception as ce:
                    pass

            except Order.DoesNotExist:
                pass
    return JsonResponse({'status': 'success'})

@login_required
def seller_dashboard(request):
    """Main dashboard overview for sellers with real metrics."""
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    # Check if user has a seller profile
    seller_profile = getattr(request.user, 'seller_profile', None)
    if not seller_profile:
        messages.error(request, "Seller profile not found. Please register as a seller.")
        return redirect('carify_app:home')

    products = Product.objects.filter(seller=request.user)
    
    # Calculate Metrics
    seller_order_items = OrderItem.objects.filter(product__seller=request.user)
    total_revenue = seller_order_items.filter(order__status='paid').aggregate(Sum('price'))['price__sum'] or 0
    total_orders = seller_order_items.values('order').distinct().count()
    low_stock_count = products.filter(quantity__lt=5).count() + ProductVariant.objects.filter(product__seller=request.user, stock__lt=5).count()

    # Generate 7-day rolling revenue data
    today = timezone.now().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    chart_labels = [d.strftime('%a') for d in days]
    chart_data = []

    for d in days:
        day_sum = seller_order_items.filter(
            order__status__in=['paid', 'shipped', 'delivered'],
            order__created_at__date=d
        ).aggregate(Sum('price'))['price__sum'] or 0
        chart_data.append(float(day_sum))

    context = {
        'products': products,
        'profile': seller_profile,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'low_stock_count': low_stock_count,
        'recent_orders': seller_order_items.order_by('-order__created_at')[:5],
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'seller_dashboard_home.html', context)

@login_required
def seller_products(request):
    products = Product.objects.filter(seller=request.user).prefetch_related('media', 'category')
    return render(request, 'seller_dashboard_products.html', {'products': products})

@login_required
def seller_add_product(request):
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
    return render(request, 'product_create.html', {'form': form, 'formset': formset})

def static_page(request, page_type):
    """Render informational pages with premium luxury content."""
    pages = {
        'about': {
            'title': 'THE_LEGACY',
            'subtitle': 'Founded on Precision',
            'content': 'Carify represents the pinnacle of automotive preservation. We are more than a marketplace; we are the stewards of automotive heritage.'
        },
        'manifesto': {
            'title': 'THE_MANIFESTO',
            'subtitle': 'Our Guiding Principles',
            'content': 'We believe that preservation is a form of art. Every vehicle tells a story, and every product we select is chosen to ensure that story continues for generations.'
        },
        'services': {
            'title': 'ELITE_SOLUTIONS',
            'subtitle': 'Professional Preservation',
            'content': 'From nanoscopic ceramic application to high-impact film solutions, our network of certified partners delivers the gold standard in vehicle protection.'
        },
        'privacy': {
            'title': 'THE_PROTOCOL',
            'subtitle': 'Privacy & Security',
            'content': 'Your data, like your vehicle, is protected by the highest standards of safety and integrity.'
        }
    }
    context = pages.get(page_type, pages['about'])
    return render(request, 'static_page.html', context)

@login_required
def seller_orders(request):
    order_items = OrderItem.objects.filter(product__seller=request.user).select_related('order', 'order__buyer', 'product').order_by('-order__created_at')
    return render(request, 'seller_dashboard_orders.html', {'order_items': order_items})

@login_required
def seller_analytics(request):
    import datetime
    from django.utils.timezone import now

    thirty_days_ago = now() - datetime.timedelta(days=30)
    
    # Base query for paid orders belonging to this seller
    paid_items = OrderItem.objects.filter(
        product__seller=request.user,
        order__status='paid'
    )
    
    # 1. Macro Totals
    totals = paid_items.aggregate(
        total_revenue=Sum(F('price') * F('quantity')),
        total_orders=Count('order', distinct=True)
    )
    total_revenue = totals['total_revenue'] or 0
    total_orders = totals['total_orders'] or 0
    aov = total_revenue / total_orders if total_orders > 0 else 0

    # 2. Time-Series Data (Last 30 Days)
    daily_sales = paid_items.filter(order__created_at__gte=thirty_days_ago) \
        .annotate(date=TruncDate('order__created_at')) \
        .values('date') \
        .annotate(revenue=Sum(F('price') * F('quantity'))) \
        .order_by('date')

    # Convert to arrays for Chart.js
    dates_map = { (thirty_days_ago + datetime.timedelta(days=i)).date(): 0 for i in range(31) }
    for daily in daily_sales:
        dates_map[daily['date']] = float(daily['revenue'])
    
    labels = [d.strftime('%b %d') for d in dates_map.keys()]
    data = list(dates_map.values())

    # 3. Top Products
    top_products = paid_items.values('product__name') \
        .annotate(qty_sold=Sum('quantity'), rev=Sum(F('price') * F('quantity'))) \
        .order_by('-qty_sold')[:5]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'aov': aov,
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(data),
        'top_products': top_products,
    }
    return render(request, 'seller_dashboard_analytics.html', context)

@login_required
def seller_settings(request):
    return render(request, 'seller_dashboard_settings.html')
