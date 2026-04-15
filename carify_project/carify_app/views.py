from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import stripe
import uuid
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
import json
from .models import (
    Product, ProductMedia, Order, OrderItem, Payment, OTPToken, 
    SellerProfile, Cart, CartItem, ProductVariant, Category,
    Service, Booking
)
from .forms import (
    ProductForm, ProductMediaFormset, SellerRegistrationForm, 
    BuyerRegistrationForm, OTPVerifyForm, ServiceForm,
    UserProfileForm, SellerProfileForm, CategoryForm
)

STRIPE_PLACEHOLDER_SECRET_KEY = 'sk_test_your_stripe_secret_key_here'


def get_stripe_secret_key():
    return (getattr(settings, 'STRIPE_SECRET_KEY', '') or '').strip()


def is_stripe_demo_mode():
    """Allow local checkout flows to run without a live Stripe secret."""
    stripe_secret_key = get_stripe_secret_key()
    return stripe_secret_key == STRIPE_PLACEHOLDER_SECRET_KEY or (
        settings.DEBUG and not stripe_secret_key
    )


def complete_order_payment(order, payment_method='stripe', transaction_id=None, clear_cart=False):
    order.status = 'paid'
    order.save(update_fields=['status'])

    Payment.objects.get_or_create(
        order=order,
        defaults={
            'payment_method': payment_method,
            'transaction_id': transaction_id or f"{payment_method}-{uuid.uuid4().hex}",
            'amount': order.total_amount,
            'status': 'completed',
        }
    )

    if clear_cart:
        try:
            cart = order.buyer.cart
            if cart:
                cart.items.filter(is_saved_for_later=False).delete()
        except Exception:
            pass

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
    """Display list of products with search and category filtering."""
    query = request.GET.get('search', '')
    category_id = request.GET.get('category')
    
    products = Product.objects.all().prefetch_related('media', 'reviews')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
        
    categories = Category.objects.all()
    
    return render(request, 'product_list.html', {
        'products': products,
        'categories': categories,
        'search_query': query,
        'selected_category': int(category_id) if category_id else None
    })

@login_required
def add_category(request):
    """Initialize a new catalog option (category)."""
    if not request.user.is_superuser:
        messages.error(request, "Clearance_Error: SuperAdmin required.")
        return redirect('carify_app:seller_dashboard')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Catalog option '{category.name}' initialized.")
            return redirect('carify_app:manage_categories')
    else:
        form = CategoryForm()

    existing_categories = Category.objects.all().order_by('name')
    return render(request, 'category_form.html', {
        'form': form, 
        'title': 'INITIALIZE CATALOG OPTION',
        'existing_categories': existing_categories
    })

@login_required
def edit_category(request, category_id):
    """Reconfigure an existing catalog option."""
    if not request.user.is_superuser:
        messages.error(request, "Clearance_Error: SuperAdmin required.")
        return redirect('carify_app:seller_dashboard')

    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Catalog option '{category.name}' reconfigured.")
            return redirect('carify_app:manage_categories')
    else:
        form = CategoryForm(instance=category)

    existing_categories = Category.objects.all().order_by('name')
    return render(request, 'category_form.html', {
        'form': form, 
        'title': 'RECONFIGURE OPTION', 
        'is_edit': True,
        'existing_categories': existing_categories
    })

def product_detail(request, product_id):
    """Display product detail with gallery, variants, and reviews."""
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    user_has_reviewed = product.reviews.filter(user=request.user).exists() if request.user.is_authenticated else False
    
    return render(request, 'product_detail.html', {
        'product': product,
        'related_products': related_products,
        'user_has_reviewed': user_has_reviewed
    })

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

    try:
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
                service=item.service,
                quantity=item.quantity,
                price=unit_price
            )

            item_name = ""
            if item.product:
                item_name = f"{item.product.name} ({item.variant.name if item.variant else 'Standard'})"
            else:
                item_name = f"Ritual: {item.service.name}"

            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item_name,
                        'description': (item.product.description if item.product else item.service.description)[:200],
                    },
                    'unit_amount': int(unit_price * 100),
                },
                'quantity': item.quantity,
            })
        stripe_secret_key = get_stripe_secret_key()

        # DEV BYPASS: Show a local payment-options screen without a configured Stripe key.
        if is_stripe_demo_mode():
            request.session['demo_checkout_order_id'] = order.id
            return redirect('carify_app:demo_payment')

        if not stripe_secret_key:
            order.delete()
            messages.error(request, "Stripe is not configured yet. Add STRIPE_SECRET_KEY to continue with live checkout.")
            return redirect('carify_app:cart_view')

        stripe.api_key = stripe_secret_key

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'klarna', 'affirm'],
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
    request.session.pop('demo_checkout_order_id', None)
    return render(request, 'payment_success.html')

@login_required
def payment_cancel(request):
    return render(request, 'payment_cancel.html')


@login_required
def demo_payment(request):
    order_id = request.session.get('demo_checkout_order_id')
    if not order_id:
        messages.error(request, "No demo checkout session was found.")
        return redirect('carify_app:cart_view')

    order = get_object_or_404(Order, id=order_id, buyer=request.user, status='pending')
    return render(request, 'payment_demo.html', {'order': order})


@login_required
@require_POST
def complete_demo_payment(request):
    order_id = request.session.get('demo_checkout_order_id')
    if not order_id:
        messages.error(request, "The demo payment session has expired.")
        return redirect('carify_app:cart_view')

    order = get_object_or_404(Order, id=order_id, buyer=request.user, status='pending')
    selected_method = request.POST.get('payment_method', 'card').lower()
    allowed_methods = {'card', 'klarna', 'affirm'}
    if selected_method not in allowed_methods:
        selected_method = 'card'

    complete_order_payment(
        order,
        payment_method='stripe',
        transaction_id=f"demo-{selected_method}-{uuid.uuid4().hex}",
        clear_cart=True,
    )
    request.session.pop('demo_checkout_order_id', None)
    messages.success(request, f"Demo payment confirmed with {selected_method.upper()}.")
    return redirect('carify_app:payment_success')

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
                complete_order_payment(
                    order,
                    payment_method='stripe',
                    transaction_id=session.payment_intent,
                    clear_cart=False,
                )

                # Deduct inventory quantities for products
                for item in order.items.all():
                    if item.product and item.product.quantity >= item.quantity:
                        item.product.quantity -= item.quantity
                        item.product.save()

                # Clear the buyer's ACTIVE cart items now that order is securely paid
                try:
                    cart = order.buyer.cart
                    if cart:
                        cart.items.filter(is_saved_for_later=False).delete()
                except Exception:
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
        # Use inlineformset_factory for better handling
        from django.forms import inlineformset_factory
        EditMediaFormset = inlineformset_factory(Product, ProductMedia, fields=('media_type', 'image', 'video', 'caption', 'sort_order'), extra=3, can_delete=True)
        formset = EditMediaFormset(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            
            # Save formset items
            formset.instance = product
            formset.save()
            
            # Handle Bulk Image Uploads (NEW)
            multi_images = request.FILES.getlist('multi_images')
            for f in multi_images:
                ProductMedia.objects.create(
                    product=product,
                    media_type='image',
                    image=f,
                    caption=f"Specimen View"
                )
            
            messages.success(request, f"New specimen '{product.name}' has been indexed.")
            return redirect('carify_app:product_detail', product_id=product.id)
    else:
        form = ProductForm()
        from django.forms import inlineformset_factory
        InitialMediaFormset = inlineformset_factory(Product, ProductMedia, fields=('media_type', 'image', 'video', 'caption', 'sort_order'), extra=3, can_delete=True)
        formset = InitialMediaFormset()
    return render(request, 'product_create.html', {'form': form, 'formset': formset})

@login_required
def seller_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    from django.forms import inlineformset_factory
    EditMediaFormset = inlineformset_factory(Product, ProductMedia, fields=('media_type', 'image', 'video', 'caption', 'sort_order'), extra=3, can_delete=True)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = EditMediaFormset(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            # Handle Bulk Image Uploads (NEW)
            multi_images = request.FILES.getlist('multi_images')
            for f in multi_images:
                ProductMedia.objects.create(
                    product=product,
                    media_type='image',
                    image=f,
                    caption=f"Specimen View"
                )
            
            messages.success(request, f"Specimen '{product.name}' details updated.")
            return redirect('carify_app:product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)
        formset = EditMediaFormset(instance=product)
        
    return render(request, 'product_create.html', {
        'form': form, 
        'formset': formset, 
        'is_edit': True, 
        'product': product
    })

@login_required
def seller_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    name = product.name
    product.delete()
    messages.warning(request, f"Specimen '{name}' has been purged from inventory.")
    return redirect('carify_app:seller_products')

def services_catalog(request):
    """Render the dynamic Elite Solutions catalog."""
    services = Service.objects.all().select_related('seller', 'category')
    return render(request, 'services.html', {'services': services})

@login_required
def add_service(request):
    """Handle administrative creation of new car care ceremonies."""
    if not request.user.is_superuser:
        messages.error(request, "Clearance_Error: SuperAdmin protocol required.")
        return redirect('carify_app:services')

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.seller = request.user
            service.save()
            messages.success(request, f"Ceremony '{service.name}' initialized in the catalog.")
            return redirect('carify_app:services')
    else:
        form = ServiceForm()

    return render(request, 'service_create.html', {'form': form})

@login_required
def delete_service(request, service_id):
    """Terminate an existing ritual from the catalog."""
    if not request.user.is_superuser:
        messages.error(request, "Clearance_Error: SuperAdmin required for termination.")
        return redirect('carify_app:services')
    
    service = get_object_or_404(Service, id=service_id)
    name = service.name
    service.delete()
    messages.success(request, f"Ritual Protocol '{name}' has been terminated.")
    return redirect('carify_app:services')

@login_required
@require_POST
def book_service(request):
    """Handle service ceremony booking requests with optional Cart clearing."""
    service_id = request.POST.get('service_id')
    # Align with form field names in cart.html and services.html
    preferred_date = request.POST.get('preferred_date') or request.POST.get('date')
    preferred_time = request.POST.get('preferred_time') or request.POST.get('time')
    vehicle_details = request.POST.get('vehicle_details') or request.POST.get('vehicle')
    notes = request.POST.get('additional_notes') or request.POST.get('notes', '')
    
    redirect_to_cart = request.POST.get('redirect_to_cart') == 'true'

    service = get_object_or_404(Service, id=service_id)

    try:
        Booking.objects.create(
            user=request.user,
            service=service,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            vehicle_details=vehicle_details,
            additional_notes=notes
        )
        
        # Clear from cart if present
        if request.user.is_authenticated:
            CartItem.objects.filter(cart__user=request.user, service=service).delete()
        
        messages.success(request, f"Ritual Protocol '{service.name}' initiated. Our curators will finalize the scheduling shortly.")
    except Exception as e:
        messages.error(request, f"Protocol_Error: {str(e)}")

    if redirect_to_cart:
        return redirect('carify_app:cart_view')
    return redirect('carify_app:services')


@login_required
def manage_categories(request):
    """List all catalog options for administrative management."""
    if not request.user.is_superuser:
        messages.error(request, "Clearance_Error: SuperAdmin protocol required.")
        return redirect('carify_app:seller_dashboard')
    
    # Annotate with product count for the registry view
    categories = Category.objects.annotate(product_count=Count('product')).order_by('name')
    return render(request, 'category_list.html', {'categories': categories})


@login_required
def delete_category(request, category_id):
    """Purge a catalog option from the registry."""
    if not request.user.is_superuser:
        messages.error(request, "Clearance_Error: SuperAdmin required.")
        return redirect('carify_app:seller_dashboard')

    category = get_object_or_404(Category, id=category_id)
    name = category.name
    category.delete()
    messages.warning(request, f"Catalog option '{name}' purged.")
    return redirect('carify_app:manage_categories')


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
    seller_profile = getattr(request.user, 'seller_profile', None)
    if not seller_profile:
        return redirect('carify_app:home')
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, request.FILES, instance=seller_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Global Partner Protocol updated successfully.")
            return redirect('carify_app:seller_settings')
    else:
        form = SellerProfileForm(instance=seller_profile)
        
    return render(request, 'seller_dashboard_settings.html', {'form': form, 'profile': seller_profile})

@login_required
def user_profile(request):
    """Render the elite member profile with orders and rituals."""
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    bookings = Booking.objects.filter(user=request.user).order_by('-preferred_date')
    
    return render(request, 'account/profile.html', {
        'orders': orders,
        'bookings': bookings
    })

@login_required
def update_user_profile(request):
    """Modify member identity and communication protocols."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Member Identity updated successfully.")
            return redirect('carify_app:user_profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'account/profile_edit.html', {'form': form})

def public_seller_profile(request, seller_id):
    """Display a seller's showcase to the public."""
    seller_user = get_object_or_404(User, id=seller_id)
    profile = get_object_or_404(SellerProfile, user=seller_user)
    products = Product.objects.filter(seller=seller_user).prefetch_related('media', 'reviews')
    services = Service.objects.filter(seller=seller_user)
    
    return render(request, 'seller_public_profile.html', {
        'seller_profile': profile,
        'products': products,
        'services': services
    })

@login_required
def cart_view(request):
    """Render the dedicated full-page acquisition portfolio."""
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})


@require_POST
def subscribe_newsletter(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
        
        from .models import NewsletterSubscription
        if NewsletterSubscription.objects.filter(email=email).exists():
            return JsonResponse({'status': 'success', 'message': 'You are already in the loop.'})
        
        NewsletterSubscription.objects.create(email=email)
        return JsonResponse({'status': 'success', 'message': 'Welcome to the loop! We will keep you updated.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
