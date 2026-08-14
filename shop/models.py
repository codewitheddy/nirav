from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    short_description = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Option 1: Store image URL (recommended for external images)
    image_url = models.URLField(max_length=500, blank=True, null=True, 
                                help_text="External image URL (e.g., from Unsplash, Imgur)")
    
    # Option 2: Store base64 image data (for small images stored in DB)
    image_base64 = models.TextField(blank=True, null=True,
                                    help_text="Base64 encoded image data")
    
    # Keep the old ImageField for backward compatibility (optional)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    is_available = models.BooleanField(default=True)
    is_featured  = models.BooleanField(default=False,
                                       help_text='Featured products are highlighted in the storefront')
    stock        = models.PositiveIntegerField(
                       null=True, blank=True,
                       help_text='Leave blank for unlimited stock. Only used when the product has no variants.')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_available']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['is_available', 'created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_image_url(self):
        """Return the appropriate image URL"""
        if self.image_url:
            return self.image_url
        elif self.image_base64:
            return f"data:image/jpeg;base64,{self.image_base64}"
        elif self.image:
            return self.image.url
        return None

    @property
    def min_variant_price(self):
        """Lowest available variant price, or base price if no variants."""
        variants = self.variants.filter(is_available=True)
        if variants.exists():
            return min(v.price for v in variants)
        return self.price

    @property
    def total_stock(self):
        """
        Effective stock for the product.

        Priority:
        1. If the product has variants with their own stock set, sum those.
        2. If variants exist but none have stock set, use product.stock (shared pool).
        3. If no variants, use product.stock directly.
        None means unlimited.
        """
        variants = list(self.variants.all())
        if variants:
            variant_stocks = [v.stock for v in variants]
            # If at least one variant has an explicit stock value, sum them
            if any(s is not None for s in variant_stocks):
                # Variants with None are treated as unlimited (contribute None to sum)
                if any(s is None for s in variant_stocks):
                    return None  # at least one variant is unlimited
                return sum(variant_stocks)
            # No variant has stock set — fall back to product-level stock
            return self.stock
        return self.stock

    @property
    def is_in_stock(self):
        """False only when stock is explicitly 0."""
        t = self.total_stock
        return t is None or t > 0

    @property
    def low_stock(self):
        """True when stock is tracked and ≤ 5."""
        t = self.total_stock
        return t is not None and 0 < t <= 5

    @property
    def has_variant_on_sale(self):
        """True if any variant has an active promotion."""
        for v in self.variants.filter(is_available=True):
            if self._best_promo_for_variant(v):
                return True
        return False

    @property
    def active_promotion(self):
        """Return the best active promotion that applies to this product with min_quantity=1."""
        from django.utils import timezone as tz
        from django.db.models import Q
        now = tz.now()
        promos = Promotion.objects.prefetch_related('products').select_related('category').filter(
            is_active=True,
            min_quantity=1,
        ).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now)
        )
        best = None
        best_discount = None
        for promo in promos:
            if promo.applies_to_product(self.id):
                d = promo.calculate_discount(self.price)
                if best_discount is None or d > best_discount:
                    best_discount = d
                    best = promo
        return best

    @property
    def sale_price(self):
        """Discounted price if an active promotion applies, else None."""
        promo = self.active_promotion
        if promo is None:
            return None
        from decimal import Decimal
        discounted = self.price - promo.calculate_discount(self.price)
        return max(discounted, Decimal('0'))

    @property
    def discount_percent(self):
        """Integer discount percentage for badge display, or None."""
        promo = self.active_promotion
        if promo is None:
            return None
        if promo.discount_type == 'percentage':
            return int(promo.discount_value)
        # For fixed, compute effective percentage
        if self.price > 0:
            return int((promo.calculate_discount(self.price) / self.price * 100).quantize(1))
        return None

    def get_bulk_discounts(self):
        """Return active bulk discount promotions (min_quantity > 1) applicable to this product."""
        from django.utils import timezone as tz
        from django.db.models import Q
        now = tz.now()
        
        promos = Promotion.objects.prefetch_related('products', 'variants').select_related('category').filter(
            is_active=True,
            min_quantity__gt=1,  # Only bulk discounts
        ).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now)
        )
        
        applicable = []
        for promo in promos:
            # Check if promotion applies to this product
            if promo.scope == 'all':
                applicable.append(promo)
            elif promo.scope == 'products' and promo.products.filter(id=self.id).exists():
                applicable.append(promo)
            elif promo.scope == 'category' and promo.category_id == self.category_id:
                applicable.append(promo)
            elif promo.scope == 'variants' and promo.variants.filter(product_id=self.id).exists():
                if promo.also_discount_base:
                    applicable.append(promo)
        
        return applicable

    def _best_promo_for_variant(self, variant):
        """Return the best active promotion that applies to a specific variant."""
        from django.utils import timezone as tz
        from django.db.models import Q
        now = tz.now()
        promos = Promotion.objects.prefetch_related('products', 'variants').select_related('category').filter(
            is_active=True,
            min_quantity=1,
        ).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now)
        )
        best = None
        best_discount = None
        for promo in promos:
            if promo.applies_to_variant(variant.id):
                d = promo.calculate_discount(variant.price)
                if best_discount is None or d > best_discount:
                    best_discount = d
                    best = promo
        return best

    @property
    def variants_json(self):
        """JSON-safe list of available variants for the storefront modal, including sale info."""
        import json
        from decimal import Decimal
        variants = self.variants.filter(is_available=True).prefetch_related(
            'attribute_values__attribute_value__attribute'
        )
        data = []
        for v in variants:
            promo = self._best_promo_for_variant(v)
            sale_price = None
            discount_pct = None
            if promo:
                discount = promo.calculate_discount(v.price)
                sale_price = max(v.price - discount, Decimal('0'))
                if promo.discount_type == 'percentage':
                    discount_pct = int(promo.discount_value)
                elif v.price > 0:
                    discount_pct = int((discount / v.price * 100).quantize(1))
            data.append({
                'id': v.id,
                'sku': v.sku or '',
                # Legacy fields kept for backwards compat
                'size': v.size,
                'color': v.color,
                # Dynamic attributes dict: {"Color": "Black", "Size": "M"}
                'attributes': v.get_attributes_dict(),
                'display_name': v.display_name,
                'price': str(v.price),
                'sale_price': str(sale_price) if sale_price is not None else None,
                'discount_percent': discount_pct,
                'image': v.get_image_url() or '',
                'stock': v.stock,          # None = unlimited
                'in_stock': v.is_in_stock,
                'low_stock': v.low_stock,
                'stock_status': v.stock_status,
            })
        return json.dumps(data)

    @property
    def sale_json(self):
        """JSON-safe sale info for the storefront — null if no active promo."""
        import json
        sp = self.sale_price
        if sp is None:
            return 'null'
        return json.dumps({
            'sale_price': str(sp),
            'original_price': str(self.price),
            'discount_percent': self.discount_percent,
        })
    
    def __str__(self):
        return self.name


class Attribute(models.Model):
    """
    A reusable product attribute type, e.g. "Color", "Size", "Material".
    Attributes are scoped to a product so each product can define its own set.
    """
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, related_name='attributes'
    )
    name = models.CharField(max_length=100, help_text="e.g. Color, Size, Material")
    position = models.PositiveSmallIntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ['position', 'id']
        unique_together = [('product', 'name')]

    def __str__(self):
        return f"{self.product.name} › {self.name}"


class AttributeValue(models.Model):
    """A concrete value for an attribute, e.g. "Red", "XL", "Cotton"."""
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, related_name='values'
    )
    value = models.CharField(max_length=100)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']
        unique_together = [('attribute', 'value')]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    """
    A specific combination of attribute values for a product.
    The legacy 'size' and 'color' CharField fields are kept for backward
    compatibility with existing data and are still used as a fallback
    display_name when no VariantAttributeValue rows exist.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(
        max_length=100, blank=True, unique=True, null=True,
        help_text="Stock-keeping unit — must be unique across all variants"
    )
    # Legacy fields — kept for backward compat, used as fallback display
    size = models.CharField(max_length=50, blank=True, help_text="e.g. S, M, L, XL, 6, 7, 8 ...")
    color = models.CharField(max_length=50, blank=True, help_text="e.g. Gold, Silver, Rose Gold ...")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Internal cost price (not shown to customers)"
    )
    stock = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Leave blank for unlimited stock.')
    weight = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True,
        help_text="Weight in kg (optional)"
    )
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    @property
    def is_in_stock(self):
        return self.stock is None or self.stock > 0

    @property
    def low_stock(self):
        return self.stock is not None and 0 < self.stock <= 5

    @property
    def stock_status(self):
        if self.stock is None:
            return 'in_stock'
        if self.stock == 0:
            return 'out_of_stock'
        if self.stock <= 5:
            return 'low_stock'
        return 'in_stock'

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_available']),
            models.Index(fields=['product', 'is_available']),
            models.Index(fields=['size']),
            models.Index(fields=['color']),
            models.Index(fields=['price']),
            models.Index(fields=['stock']),
        ]

    def __str__(self):
        parts = [self.product.name]
        label = self.display_name
        if label and label != 'Default':
            parts.append(label)
        return ' - '.join(parts)

    def get_image_url(self):
        """Return variant image, falling back to parent product image."""
        if self.image_url:
            return self.image_url
        elif self.image:
            return self.image.url
        return self.product.get_image_url()

    def clean(self):
        """Validate that this variant doesn't duplicate another for the same product."""
        from django.core.exceptions import ValidationError
        
        # Skip validation if variant hasn't been saved yet (no PK)
        if self.pk is None:
            return
        
        # Get current attribute values
        current_attrs = set()
        for av in self.attribute_values.all():
            current_attrs.add((av.attribute_value.attribute.id, av.attribute_value.id))
        
        # If no dynamic attributes, check legacy fields
        if not current_attrs:
            # Check for duplicate legacy variants (same size/color combo)
            existing = ProductVariant.objects.filter(
                product=self.product,
                size=self.size,
                color=self.color
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError(
                    f"A variant with {self.size or 'no size'} / {self.color or 'no color'} "
                    f"already exists for this product."
                )
        else:
            # Check for duplicate dynamic attribute combinations
            other_variants = self.product.variants.exclude(pk=self.pk)
            for variant in other_variants:
                other_attrs = set()
                for av in variant.attribute_values.all():
                    other_attrs.add((av.attribute_value.attribute.id, av.attribute_value.id))
                
                if current_attrs == other_attrs:
                    raise ValidationError(
                        f"A variant with the same attributes ({self.display_name}) "
                        f"already exists for this product."
                    )

    @property
    def display_name(self):
        """
        Build display name from dynamic attribute values first,
        then fall back to legacy size/color fields.
        """
        # Try dynamic attributes
        av_rows = self.attribute_values.select_related('attribute_value__attribute').order_by(
            'attribute_value__attribute__position',
            'attribute_value__attribute__id',
        )
        parts = [row.attribute_value.value for row in av_rows]
        if parts:
            return ' / '.join(parts)
        # Legacy fallback
        legacy = []
        if self.size:
            legacy.append(self.size)
        if self.color:
            legacy.append(self.color)
        return ' / '.join(legacy) if legacy else 'Default'

    def get_attributes_dict(self):
        """Return {attribute_name: value} ordered by attribute position."""
        av_rows = self.attribute_values.select_related('attribute_value__attribute').order_by(
            'attribute_value__attribute__position',
            'attribute_value__attribute__id',
        )
        return {row.attribute_value.attribute.name: row.attribute_value.value for row in av_rows}


class VariantAttributeValue(models.Model):
    """
    Links a ProductVariant to a specific AttributeValue.
    E.g. variant #42 → Color: Red AND Size: M means two rows here.
    """
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='attribute_values'
    )
    attribute_value = models.ForeignKey(
        AttributeValue, on_delete=models.CASCADE, related_name='variant_links'
    )

    class Meta:
        unique_together = [('variant', 'attribute_value')]

    def __str__(self):
        return f"{self.variant} → {self.attribute_value}"


class HeroBanner(models.Model):
    """Dynamically editable hero/banner section for the storefront."""

    SCHEME_LIGHT = 'light'   # dark text on light bg
    SCHEME_DARK  = 'dark'    # light text on dark bg
    SCHEME_CHOICES = [
        (SCHEME_LIGHT, 'Light (dark text)'),
        (SCHEME_DARK,  'Dark (light text)'),
    ]

    # ── Content ──────────────────────────────────────────────────────
    eyebrow    = models.CharField(max_length=80,  blank=True, default='Timeless Beauty',
                                  help_text='Small label above the heading (e.g. "NEW COLLECTION")')
    heading    = models.CharField(max_length=200, default='Timeless Elegance,\nCrafted to Shine',
                                  help_text='Main heading. Use \\n for a line break.')
    subtitle   = models.CharField(max_length=200, blank=True,
                                  default='Minimal jewelry for everyday confidence.',
                                  help_text='Short line below the heading.')

    # Three optional feature pills
    pill_1 = models.CharField(max_length=60, blank=True, default='Hypoallergenic')
    pill_2 = models.CharField(max_length=60, blank=True, default='Water Resistant')
    pill_3 = models.CharField(max_length=60, blank=True, default='Tarnish Free')

    ICON_CHECK    = 'check'
    ICON_SHIELD   = 'shield'
    ICON_STAR     = 'star'
    ICON_HEART    = 'heart'
    ICON_LEAF     = 'leaf'
    ICON_DIAMOND  = 'diamond'
    ICON_DROPLET  = 'droplet'
    ICON_CIRCLE   = 'circle'
    ICON_CUSTOM   = 'custom'
    ICON_CHOICES  = [
        (ICON_CHECK,   '✓ Checkmark'),
        (ICON_SHIELD,  '🛡 Shield'),
        (ICON_STAR,    '★ Star'),
        (ICON_HEART,   '♥ Heart'),
        (ICON_LEAF,    '🌿 Leaf'),
        (ICON_DIAMOND, '◆ Diamond'),
        (ICON_DROPLET, '💧 Droplet'),
        (ICON_CIRCLE,  '○ Circle'),
        (ICON_CUSTOM,  '✏ Custom SVG path'),
    ]
    pill_1_icon        = models.CharField(max_length=20,   choices=ICON_CHOICES, default=ICON_SHIELD,  blank=True)
    pill_1_icon_custom = models.CharField(max_length=1000, blank=True, default='',
                                          help_text='SVG <path> / <polyline> etc. content when icon is set to Custom')
    pill_2_icon        = models.CharField(max_length=20,   choices=ICON_CHOICES, default=ICON_DROPLET, blank=True)
    pill_2_icon_custom = models.CharField(max_length=1000, blank=True, default='',
                                          help_text='SVG <path> / <polyline> etc. content when icon is set to Custom')
    pill_3_icon        = models.CharField(max_length=20,   choices=ICON_CHOICES, default=ICON_CHECK,   blank=True)
    pill_3_icon_custom = models.CharField(max_length=1000, blank=True, default='',
                                          help_text='SVG <path> / <polyline> etc. content when icon is set to Custom')

    # CTA buttons
    cta_primary_text = models.CharField(max_length=60, blank=True, default='Explore Collection')
    cta_primary_url  = models.CharField(max_length=200, blank=True, default='#products')
    cta_secondary_text = models.CharField(max_length=60, blank=True, default='Contact Us')
    cta_secondary_url  = models.CharField(max_length=200, blank=True,
                                          default='https://wa.me/254700840182')

    # ── Visual ───────────────────────────────────────────────────────
    bg_color      = models.CharField(max_length=20, blank=True, default='#faf7f4',
                                     help_text='CSS colour for the left panel background (e.g. #faf7f4)')
    bg_image_url  = models.URLField(max_length=500, blank=True,
                                    help_text='Full-hero background image URL (covers both columns). Overrides bg_color.')
    bg_image      = models.ImageField(upload_to='banners/bg/', blank=True, null=True,
                                      help_text='Or upload a background image')
    image_url     = models.URLField(max_length=500, blank=True,
                                    help_text='Right-hand side image URL')
    image         = models.ImageField(upload_to='banners/', blank=True, null=True,
                                      help_text='Or upload a side image')
    hide_side_image = models.BooleanField(default=False,
                                          help_text='Hide the right-hand image panel (full-width content)')
    color_scheme  = models.CharField(max_length=10, choices=SCHEME_CHOICES, default=SCHEME_LIGHT)

    # ── Typography & Button colours ──────────────────────────────────
    eyebrow_color          = models.CharField(max_length=20, blank=True, default='#c0567a',
                                              help_text='Eyebrow label text colour')
    heading_color          = models.CharField(max_length=20, blank=True, default='#1a1a1a',
                                              help_text='Heading (h1) text colour')
    subtitle_color         = models.CharField(max_length=20, blank=True, default='#777777',
                                              help_text='Subtitle paragraph colour')
    pill_text_color        = models.CharField(max_length=20, blank=True, default='#555555',
                                              help_text='Feature pill label colour')
    pill_icon_color        = models.CharField(max_length=20, blank=True, default='#c9a96e',
                                              help_text='Feature pill icon colour')
    btn_primary_bg         = models.CharField(max_length=20, blank=True, default='#1a1a1a',
                                              help_text='Primary button background colour')
    btn_primary_text_color = models.CharField(max_length=20, blank=True, default='#ffffff',
                                              help_text='Primary button text colour')
    btn_secondary_bg       = models.CharField(max_length=20, blank=True, default='transparent',
                                              help_text='Secondary button background colour')
    btn_secondary_text_color = models.CharField(max_length=20, blank=True, default='#1a1a1a',
                                                help_text='Secondary button text & border colour')

    # ── Meta ─────────────────────────────────────────────────────────
    is_active  = models.BooleanField(default=True)
    order      = models.PositiveIntegerField(default=0,
                                             help_text='Lower number = higher priority when multiple banners are active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Hero Banner'
        verbose_name_plural = 'Hero Banners'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['order']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active', 'order']),
        ]

    def __str__(self):
        return self.heading[:60]

    def get_image_url(self):
        if self.image_url:
            return self.image_url
        if self.image:
            return self.image.url
        return None

    def get_bg_image_url(self):
        if self.bg_image_url:
            return self.bg_image_url
        if self.bg_image:
            return self.bg_image.url
        return None

    @property
    def heading_html(self):
        """Convert literal \\n or real newlines in heading to <br> for the template."""
        import html as h
        escaped = h.escape(self.heading)
        # Handle both literal \n (typed in admin) and real newlines
        return escaped.replace('\\n', '<br>').replace('\n', '<br>')

    @property
    def pills(self):
        return [p for p in [self.pill_1, self.pill_2, self.pill_3] if p.strip()]

    @property
    def pills_with_icons(self):
        """Returns list of (text, icon_key, custom_path) for non-empty pills."""
        pairs = [
            (self.pill_1, self.pill_1_icon or self.ICON_SHIELD, self.pill_1_icon_custom),
            (self.pill_2, self.pill_2_icon or self.ICON_DROPLET, self.pill_2_icon_custom),
            (self.pill_3, self.pill_3_icon or self.ICON_CHECK,  self.pill_3_icon_custom),
        ]
        return [(text, icon, custom) for text, icon, custom in pairs if text.strip()]


class Promotion(models.Model):
    TYPE_PERCENTAGE = 'percentage'
    TYPE_FIXED = 'fixed'
    TYPE_CHOICES = [
        (TYPE_PERCENTAGE, 'Percentage Off (%)'),
        (TYPE_FIXED, 'Fixed Amount Off (Ksh)'),
    ]

    SCOPE_ALL = 'all'
    SCOPE_PRODUCTS = 'products'
    SCOPE_CATEGORY = 'category'
    SCOPE_VARIANTS = 'variants'
    SCOPE_CHOICES = [
        (SCOPE_ALL,      'All Products (Site-wide)'),
        (SCOPE_PRODUCTS, 'Specific Products'),
        (SCOPE_CATEGORY, 'Specific Category'),
        (SCOPE_VARIANTS, 'Specific Variants'),
    ]

    name = models.CharField(max_length=200, help_text="Internal label, e.g. 'Summer Sale 20%'")
    discount_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_PERCENTAGE)
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Enter 20 for 20% off, or 500 for Ksh 500 off"
    )

    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_ALL)
    products = models.ManyToManyField(
        'Product', blank=True, related_name='promotions',
        help_text="Only used when scope is 'Specific Products'"
    )
    variants = models.ManyToManyField(
        'ProductVariant', blank=True, related_name='promotions',
        help_text="Only used when scope is 'Specific Variants'"
    )
    category = models.ForeignKey(
        'Category', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='promotions',
        help_text="Only used when scope is 'Specific Category'"
    )

    # Bulk discount: only applies when cart contains this many qualifying items
    min_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Minimum total quantity in cart for promotion to apply (use >1 for bulk discounts)"
    )

    starts_at = models.DateTimeField(null=True, blank=True, help_text="Leave blank to start immediately")
    ends_at   = models.DateTimeField(null=True, blank=True, help_text="Leave blank for no expiry")
    is_active = models.BooleanField(default=True)
    also_discount_base = models.BooleanField(
        default=False,
        help_text="When scope is 'Specific Variants', also apply the discount to the base product price"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['starts_at']),
            models.Index(fields=['ends_at']),
            models.Index(fields=['scope']),
            models.Index(fields=['category']),
            models.Index(fields=['min_quantity']),
            models.Index(fields=['is_active', 'starts_at', 'ends_at']),
            models.Index(fields=['is_active', 'min_quantity']),
        ]

    def __str__(self):
        return self.name

    def is_valid(self):
        """Check the promotion is currently active and within its date window."""
        from django.utils import timezone as tz
        if not self.is_active:
            return False
        now = tz.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now >= self.ends_at:
            return False
        return True

    def applies_to_product(self, product_id):
        """Return True if this promotion covers the given product (ignores variant scope)."""
        if self.scope == self.SCOPE_ALL:
            return True
        if self.scope == self.SCOPE_PRODUCTS:
            return self.products.filter(id=product_id).exists()
        if self.scope == self.SCOPE_CATEGORY:
            if self.category_id is None:
                return False
            return Product.objects.filter(id=product_id, category_id=self.category_id).exists()
        if self.scope == self.SCOPE_VARIANTS:
            # Only discount base price if admin explicitly opted in
            if self.also_discount_base:
                return self.variants.filter(product_id=product_id).exists()
            return False
        return False

    def applies_to_variant(self, variant_id):
        """Return True if this promotion covers the given variant."""
        if self.scope == self.SCOPE_ALL:
            return True
        if self.scope == self.SCOPE_VARIANTS:
            return self.variants.filter(id=variant_id).exists()
        if self.scope == self.SCOPE_PRODUCTS:
            # Applies to all variants of the selected products
            return self.products.filter(variants__id=variant_id).exists()
        if self.scope == self.SCOPE_CATEGORY:
            if self.category_id is None:
                return False
            return ProductVariant.objects.filter(
                id=variant_id, product__category_id=self.category_id
            ).exists()
        return False

    def calculate_discount(self, original_price):
        """Return the discount amount (Decimal) for a single unit."""
        from decimal import Decimal
        if self.discount_type == self.TYPE_PERCENTAGE:
            return (Decimal(str(original_price)) * self.discount_value / Decimal('100')).quantize(Decimal('0.01'))
        return min(Decimal(str(original_price)), self.discount_value)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    customer_address = models.TextField()
    notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promotion = models.ForeignKey(
        'Promotion', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['customer_name']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['total_amount']),
            models.Index(fields=['promotion']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: ORD-YYYYMMDD-XXXX
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(order_number__startswith=f'ORD-{date_str}').order_by('-order_number').first()
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.order_number = f'ORD-{date_str}-{new_num:04d}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order_number} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True
    )
    # Snapshot of product name at order time — preserved even if product is deleted
    product_name = models.CharField(max_length=200, blank=True, default='')
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    # Snapshot of variant details at order time
    variant_name = models.CharField(max_length=200, blank=True, default='',
                                    help_text="Variant display name at time of order")
    sku_snapshot = models.CharField(max_length=100, blank=True, default='',
                                    help_text="SKU at time of order")
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Snapshot the product name when the item is first created
        if not self.product_name and self.product:
            self.product_name = self.product.name
        # Snapshot variant info
        if not self.variant_name and self.variant:
            self.variant_name = self.variant.display_name
        if not self.sku_snapshot and self.variant and self.variant.sku:
            self.sku_snapshot = self.variant.sku
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.product.name if self.product else self.product_name or '(deleted product)'
        variant_info = f' ({self.variant_name or self.variant.display_name})' if self.variant else ''
        return f"{self.quantity}x {name}{variant_info}"

    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
            models.Index(fields=['variant']),
            models.Index(fields=['order', 'product']),
            models.Index(fields=['product_name']),
            models.Index(fields=['price']),
            models.Index(fields=['quantity']),
        ]

    def get_subtotal(self):
        return self.quantity * self.price

    def get_display_name(self):
        """Returns product name even if the product has been deleted."""
        if self.product:
            return self.product.name
        return self.product_name or '(deleted product)'
