from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product, ProductMedia, Order, OrderItem, Payment

class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ('media_type', 'image', 'video', 'caption', 'sort_order', 'created_at')
    readonly_fields = ('created_at',)

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'product_count')
    search_fields = ('name', 'description')

    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'quantity', 'seller', 'category', 'status', 'created_at')
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

    def status(self, obj):
        if obj.quantity > 10:
            return mark_safe('<span style="color: green;">✓ In Stock</span>')
        elif obj.quantity > 0:
            return mark_safe('<span style="color: orange;">⚠ Low Stock</span>')
        else:
            return mark_safe('<span style="color: red;">✗ Out of Stock</span>')
    status.short_description = 'Stock Status'

@admin.register(Order)
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

@admin.register(Payment)
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

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_display')
    list_filter = ('order__status',)
    search_fields = ('product__name', 'order__id')

    def price_display(self, obj):
        return format_html('<strong>${}</strong>', obj.price)
    price_display.short_description = 'Price'
