from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import (
    Category, Product, ProductVariant, Order, OrderItem, Promotion, HeroBanner,
    Attribute, AttributeValue, VariantAttributeValue,
)

# Customize admin site headers
admin.site.site_header = "POPSHOP ADMIN"
admin.site.site_title = "POPSHOP Admin Portal"
admin.site.index_title = "Welcome to POPSHOP Administration"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['size', 'color', 'price', 'image_url', 'image', 'is_available']
    
    def clean_sku(self, value):
        """Validate SKU is unique if provided."""
        if value:
            existing = ProductVariant.objects.filter(sku=value).exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("SKU must be unique.")
        return value


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'variant_count', 'is_available', 'created_at']
    list_editable = ['is_available', 'price']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'short_description']
    date_hierarchy = 'created_at'
    list_per_page = 20
    inlines = [ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_available'),
            'description': 'Base price is used when no variants are defined. If variants are added, each variant has its own price.'
        }),
        ('Media', {
            'fields': ('image_url', 'image_base64', 'image'),
            'description': 'Default product image. Each variant can also have its own image.'
        }),
    )
    
    actions = ['make_available', 'make_unavailable']
    
    def variant_count(self, obj):
        count = obj.variants.count()
        return count if count else '—'
    variant_count.short_description = 'Variants'
    
    def make_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} product(s) marked as available.')
    make_available.short_description = 'Mark selected products as available'
    
    def make_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} product(s) marked as unavailable.')
    make_unavailable.short_description = 'Mark selected products as unavailable'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'display_name', 'sku', 'price', 'stock', 'is_available']
    list_filter = ['is_available', 'product__category']
    search_fields = ['product__name', 'sku', 'size', 'color']
    list_editable = ['price', 'is_available']
    
    def save_model(self, request, obj, form, change):
        """Call clean() before saving to validate against duplicates."""
        obj.full_clean()  # This will call clean() which checks for duplicates
        super().save_model(request, obj, form, change)


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 2
    fields = ['value', 'position']


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'position']
    list_filter = ['product__category']
    search_fields = ['name', 'product__name']
    inlines = [AttributeValueInline]


@admin.register(VariantAttributeValue)
class VariantAttributeValueAdmin(admin.ModelAdmin):
    list_display = ['variant', 'attribute_value']
    search_fields = ['variant__product__name', 'attribute_value__value']


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ['heading_preview', 'eyebrow', 'color_scheme', 'is_active', 'order', 'created_at']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active', 'color_scheme']

    def heading_preview(self, obj):
        return obj.heading[:60]
    heading_preview.short_description = 'Heading'


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'discount_value', 'scope', 'min_quantity', 'is_active', 'starts_at', 'ends_at']
    list_editable = ['is_active']
    list_filter = ['is_active', 'discount_type', 'scope']
    filter_horizontal = ['products']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'quantity', 'price', 'get_subtotal']
    readonly_fields = ['get_subtotal']
    
    def get_subtotal(self, obj):
        if obj.id:
            return f'Ksh {obj.get_subtotal():,.2f}'
        return '-'
    get_subtotal.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'customer_phone', 'status', 'total_amount', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 20
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'total_amount')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_phone', 'customer_address', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_confirmed', 'mark_processing', 'mark_shipped', 'mark_delivered']
    
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} order(s) marked as confirmed.')
    mark_confirmed.short_description = 'Mark as Confirmed'
    
    def mark_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} order(s) marked as processing.')
    mark_processing.short_description = 'Mark as Processing'
    
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_shipped.short_description = 'Mark as Shipped'
    
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_delivered.short_description = 'Mark as Delivered'
