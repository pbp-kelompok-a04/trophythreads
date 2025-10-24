# cartApp/admin.py
from django.contrib import admin
from .models import Cart, CartItem, Purchase


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'total_items', 'subtotal')
    list_filter = ('user',)
    search_fields = ('user__username', 'session_key')
    readonly_fields = ('id',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'get_product_name', 'quantity', 'get_price', 'line_total', 'selected')
    list_filter = ('selected', 'cart__user')
    search_fields = ('product__name', 'product_name', 'cart__user__username')
    readonly_fields = ('id', 'line_total')
    raw_id_fields = ('cart', 'product')
    
    fieldsets = (
        ('Cart Information', {
            'fields': ('id', 'cart', 'selected')
        }),
        ('Product Information (Database)', {
            'fields': ('product',),
            'description': 'For products stored in the database'
        }),
        ('Product Information (CSV/Manual)', {
            'fields': ('product_name', 'product_price', 'product_thumbnail', 'product_stock'),
            'description': 'For products from CSV or manual entry'
        }),
        ('Quantity', {
            'fields': ('quantity', 'line_total')
        }),
    )
    
    def get_product_name(self, obj):
        return obj.product.name if obj.product else (obj.product_name or 'Unknown')
    get_product_name.short_description = 'Product Name'
    
    def get_price(self, obj):
        return obj.product.price if obj.product else (obj.product_price or 0)
    get_price.short_description = 'Price'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart', 'product', 'cart__user')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_token', 'user', 'get_product_name', 'quantity', 'product_price', 'line_total')
    list_filter = ('user', 'order_token')
    search_fields = ('order_token', 'user__username', 'product__name', 'product_name')
    readonly_fields = ('id', 'order_token', 'line_total')
    raw_id_fields = ('user', 'product')
    date_hierarchy = None  # Add if you have created_at field
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'order_token', 'user')
        }),
        ('Product Information (Database)', {
            'fields': ('product',),
            'description': 'For products stored in the database'
        }),
        ('Product Information (Stored)', {
            'fields': ('product_name', 'product_price'),
            'description': 'Product details at time of purchase'
        }),
        ('Purchase Details', {
            'fields': ('quantity', 'line_total')
        }),
    )
    
    def get_product_name(self, obj):
        return obj.product.name if obj.product else (obj.product_name or 'Unknown')
    get_product_name.short_description = 'Product Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')
    
    # Group by order token in changelist
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Purchase History'
        return super().changelist_view(request, extra_context)