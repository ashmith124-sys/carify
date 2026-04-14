import json
import datetime
from django.utils.timezone import now
from django.db.models import Sum, Count, F
from django.contrib import admin
from unfold.sites import UnfoldAdminSite
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Category, Product, ProductMedia, Order, OrderItem, Payment, 
    SellerProfile, Service, Wishlist, ProductQuestion, ProductAnswer, 
    Review, Booking, NewsletterSubscription
)

class CarifyAdminSite(UnfoldAdminSite):
    site_header = "Carify Command Center"
    site_title = "Admin | Carify"
    index_title = "Marketplace Overview"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path("search/", self.admin_view(self.index), name="search"),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # 1. Platform Metrics
        paid_orders = Order.objects.filter(status='paid')
        total_gmv = paid_orders.aggregate(gmv=Sum('total_amount'))['gmv'] or 0
        active_orders = Order.objects.exclude(status='delivered').exclude(status='cancelled').count()
        total_sellers = SellerProfile.objects.filter(is_approved=True).count()
        low_stock = Product.objects.filter(quantity__lte=5).count()
        
        extra_context['platform_stats'] = {
            'gmv': total_gmv,
            'orders': active_orders,
            'sellers': total_sellers,
            'low_stock': low_stock,
            'aov': total_gmv / paid_orders.count() if paid_orders.count() > 0 else 0,
            'total_reviews': Review.objects.count(),
            'open_inquiries': ProductQuestion.objects.filter(answers__isnull=True).count()
        }

        # 2. Revenue Chart Data (30 Days)
        thirty_days_ago = now() - datetime.timedelta(days=30)
        daily_revenue = Order.objects.filter(status='paid', created_at__gte=thirty_days_ago) \
            .extra(select={'day': "date(created_at)"}) \
            .values('day') \
            .annotate(rev=Sum('total_amount')) \
            .order_by('day')

        dates_map = { (thirty_days_ago + datetime.timedelta(days=i)).date(): 0 for i in range(31) }
        for daily in daily_revenue:
            d = daily['day']
            if isinstance(d, str):
                d = datetime.datetime.strptime(d, '%Y-%m-%d').date()
            dates_map[d] = float(daily['rev'])
        
        # 3. Top Specimens (Platform Wide)
        top_products = OrderItem.objects.filter(order__status='paid') \
            .values('product__name') \
            .annotate(qty_sold=Sum('quantity'), rev=Sum(F('price') * F('quantity'))) \
            .order_by('-qty_sold')[:5]

        extra_context['top_products'] = top_products
        extra_context['chart_labels'] = json.dumps([d.strftime('%b %d') for d in dates_map.keys()])
        extra_context['chart_data'] = json.dumps(list(dates_map.values()))

        return super().index(request, extra_context)

# Replace default admin site
admin_site = CarifyAdminSite(name='admin')

class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ('media_type', 'image', 'video', 'caption', 'sort_order', 'created_at')
    readonly_fields = ('created_at',)

class ProductAnswerInline(admin.TabularInline):
    model = ProductAnswer
    extra = 1

@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'product_count', 'delete_action')
    search_fields = ('name', 'description')

    def delete_action(self, obj):
        url = reverse('admin:carify_app_category_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" onclick="event.stopPropagation(); window.location.assign(\'{}\'); return false;" style="color: white; background: #ef4444; padding: 4px 10px; border-radius: 4px; font-weight: bold; text-decoration: none; font-size: 11px;">DELETE</a>',
            url, url
        )
    delete_action.short_description = 'Action'

    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'

@admin.register(Product, site=admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'quantity', 'seller', 'category', 'status', 'delete_action')
    list_filter = ('category', 'seller', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductMediaInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'quantity')
        }),
        ('Relationships', {
            'fields': ('seller', 'category')
        }),
        ('Main Image', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        return format_html('<strong>${}</strong>', obj.price)
    price_display.short_description = 'Price'

    def delete_action(self, obj):
        url = reverse('admin:carify_app_product_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" onclick="event.stopPropagation(); window.location.assign(\'{}\'); return false;" style="color: white; background: #ef4444; padding: 4px 10px; border-radius: 4px; font-weight: bold; text-decoration: none; font-size: 11px;">DELETE</a>',
            url, url
        )
    delete_action.short_description = 'Action'

    def status(self, obj):
        if obj.quantity > 10:
            return mark_safe('<span style="color: green;">✓ In Stock</span>')
        elif obj.quantity > 0:
            return mark_safe('<span style="color: orange;">⚠ Low Stock</span>')
        else:
            return mark_safe('<span style="color: red;">✗ Out of Stock</span>')
    status.short_description = 'Stock Status'

@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'total_amount_display', 'status_badge', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buyer__username', 'buyer__email')
    readonly_fields = ('created_at', 'updated_at')

    def total_amount_display(self, obj):
        return format_html('<strong>${}</strong>', obj.total_amount)
    total_amount_display.short_description = 'Total'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'paid': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

@admin.register(Payment, site=admin_site)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'amount_display', 'status_badge', 'payment_date')
    list_filter = ('payment_method', 'status', 'payment_date')
    search_fields = ('order__id', 'transaction_id')
    readonly_fields = ('payment_date',)

    def amount_display(self, obj):
        return format_html('<strong>${}</strong>', obj.amount)
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

@admin.register(OrderItem, site=admin_site)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_display')
    list_filter = ('order__status',)
    search_fields = ('product__name', 'order__id')

    def price_display(self, obj):
        return format_html('<strong>${}</strong>', obj.price)
    price_display.short_description = 'Price'

@admin.register(SellerProfile, site=admin_site)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('shop_name', 'user__username', 'user__email')
    readonly_fields = ('created_at',)

@admin.register(Service, site=admin_site)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'seller', 'category', 'contact_info', 'created_at', 'delete_action')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'seller__username', 'contact_info')

    # Unfold actions for the list view header
    actions_list = ["add_ritual_protocol"]

    def add_ritual_protocol(self, request):
        return format_html(
            '<a href="{}" class="bg-primary-600 font-bold px-4 py-2 rounded text-white text-xs uppercase tracking-widest no-underline hover:bg-primary-700 transition-colors">INDUCT NEW RITUAL</a>',
            reverse('admin:carify_app_service_add')
        )
    add_ritual_protocol.short_description = 'Induct Ritual'
    add_ritual_protocol.allow_from_facets = True # Show in the list view header area

    def delete_action(self, obj):
        url = reverse('admin:carify_app_service_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" onclick="event.stopPropagation(); window.location.assign(\'{}\'); return false;" style="color: white; background: #ef4444; padding: 4px 10px; border-radius: 4px; font-weight: bold; text-decoration: none; font-size: 11px;">DELETE</a>',
            url, url
        )
    delete_action.short_description = 'Action'

    
    def price_display(self, obj):
        return format_html('<strong>${}</strong>', obj.price)
    price_display.short_description = 'Price'

@admin.register(Wishlist, site=admin_site)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'products_count', 'services_count')
    search_fields = ('user__username', 'user__email')

    def products_count(self, obj):
        return obj.products.count()
    
    def services_count(self, obj):
        return obj.services.count()

@admin.register(ProductQuestion, site=admin_site)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'is_answered_badge', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('question', 'product__name', 'user__username')
    inlines = [ProductAnswerInline]

    def is_answered_badge(self, obj):
        answered = obj.answers.exists()
        color = 'green' if answered else 'orange'
        text = 'ANSWERED' if answered else 'PENDING'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;">{}</span>',
            color, text
        )
    is_answered_badge.short_description = 'Status'

@admin.register(Review, site=admin_site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at', 'helpful_count')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment', 'user__username', 'product__name')

    def helpful_count(self, obj):
        return obj.helpful_votes.count()
    helpful_count.short_description = 'Helpful Votes'

@admin.register(ProductAnswer, site=admin_site)
class ProductAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'is_seller_response', 'created_at')
    list_filter = ('is_seller_response', 'created_at')
    search_fields = ('answer', 'user__username')

@admin.register(Booking, site=admin_site)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'preferred_date', 'preferred_time', 'vehicle_details', 'status', 'status_badge', 'created_at')
    list_filter = ('status', 'preferred_date', 'created_at')
    search_fields = ('user__username', 'user__email', 'vehicle_details', 'service__name')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'completed': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Badge'

@admin.register(NewsletterSubscription, site=admin_site)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at',)
