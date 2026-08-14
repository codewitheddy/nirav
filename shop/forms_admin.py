from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.forms import inlineformset_factory
from .models import Product, Category, Order, ProductVariant, Promotion, HeroBanner
from PIL import Image


class ProductForm(forms.ModelForm):
    """Form for creating and updating products"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'short_description', 'description',
            'price', 'image_url', 'image_base64', 'image',
            'is_available', 'is_featured', 'stock'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter product name'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.TextInput(attrs={
                'class': 'form-input',
                'maxlength': '150',
                'placeholder': 'Brief description (max 150 characters)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 5,
                'placeholder': 'Detailed product description'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://example.com/image.jpg'
            }),
            'image_base64': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Base64 encoded image data'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-file',
                'accept': 'image/jpeg,image/png,image/webp'
            }),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_featured':  forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'stock': forms.NumberInput(attrs={
                'class': 'form-input', 'min': '0', 'placeholder': 'Leave blank for unlimited'
            }),
        }
        labels = {
            'name': 'Product Name',
            'category': 'Category',
            'short_description': 'Short Description',
            'description': 'Full Description',
            'price': 'Price (KES)',
            'image_url': 'Image URL (Optional)',
            'image_base64': 'Base64 Image (Optional)',
            'image': 'Upload Image (Optional)',
            'is_available': 'Available for Purchase',
            'is_featured':  'Featured Product',
        }
        help_texts = {
            'short_description': 'This appears in product cards (max 150 characters)',
            'price': 'Enter price in Kenyan Shillings',
            'image_url': 'Provide a URL to an external image',
            'image_base64': 'Or paste base64 encoded image data',
            'image': 'Or upload an image file (JPEG, PNG, WebP, max 5MB)',
        }
    
    def clean_name(self):
        """Validate and clean product name - check for duplicates"""
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 3:
            raise ValidationError('Product name must be at least 3 characters long.')
        
        # Check for duplicate names (case-insensitive)
        existing = Product.objects.filter(name__iexact=name)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError(f'A product with the name "{name}" already exists. Please use a different name.')
        
        return name
    
    def clean_price(self):
        """Validate price is non-negative with max 2 decimal places"""
        price = self.cleaned_data.get('price')
        
        if price is None:
            raise ValidationError('Price is required.')
        
        if price < 0:
            raise ValidationError('Price must be non-negative.')
        
        if price > 999999.99:
            raise ValidationError('Price exceeds maximum allowed value (999,999.99).')
        
        # Check decimal places
        if price.as_tuple().exponent < -2:
            raise ValidationError('Price can have at most 2 decimal places.')
        
        return price
    
    def clean_image(self):
        """Validate uploaded image file"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Check if this is a new uploaded file (has content_type) or existing image
            if hasattr(image, 'content_type'):
                # This is a newly uploaded file - validate it
                # Check file size (max 5MB)
                if image.size > 5 * 1024 * 1024:
                    raise ValidationError('Image file size cannot exceed 5MB.')
                
                # Check file type
                valid_types = ['image/jpeg', 'image/png', 'image/webp']
                if image.content_type not in valid_types:
                    raise ValidationError(
                        'Invalid image format. Supported formats: JPEG, PNG, WebP.'
                    )
                
                # Validate image integrity - just open the header, no .load() or .verify()
                # which would exhaust the file pointer and interfere with Django's validator
                try:
                    image.seek(0)
                    img = Image.open(image)
                    # Reading just the header is enough to confirm it's a valid image
                    img.format  # forces header parse without consuming the stream
                    image.seek(0)
                except Exception as e:
                    raise ValidationError(f'Invalid or corrupted image file: {str(e)}')
            # If no content_type, it's an existing image file - no validation needed
        
        return image
    
    def clean(self):
        """Additional validation and slug generation"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        
        # Auto-generate slug from name
        if name:
            base_slug = slugify(name)
            slug = base_slug
            counter = 1
            
            # Ensure slug is unique
            while Product.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            cleaned_data['slug'] = slug
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save product with generated slug"""
        instance = super().save(commit=False)
        
        # Set the slug
        if hasattr(self, 'cleaned_data') and 'slug' in self.cleaned_data:
            instance.slug = self.cleaned_data['slug']
        
        if commit:
            instance.save()
        
        return instance


class CategoryForm(forms.ModelForm):
    """Form for creating and updating categories"""
    
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter category name'
            }),
        }
        labels = {
            'name': 'Category Name',
        }
    
    def clean_name(self):
        """Validate and clean category name - check for duplicates"""
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise ValidationError('Category name must be at least 2 characters long.')
        
        # Check for duplicate names (case-insensitive)
        existing = Category.objects.filter(name__iexact=name)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError(f'A category with the name "{name}" already exists. Please use a different name.')
        
        return name
    
    def clean(self):
        """Generate unique slug"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        
        if name:
            base_slug = slugify(name)
            slug = base_slug
            counter = 1
            
            # Ensure slug is unique
            while Category.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            cleaned_data['slug'] = slug
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save category with generated slug"""
        instance = super().save(commit=False)
        
        # Set the slug
        if hasattr(self, 'cleaned_data') and 'slug' in self.cleaned_data:
            instance.slug = self.cleaned_data['slug']
        
        if commit:
            instance.save()
        
        return instance


class OrderStatusForm(forms.ModelForm):
    """Form for updating order status"""
    
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'status': 'Order Status',
        }
    
    def clean_status(self):
        """Validate status transitions"""
        new_status = self.cleaned_data.get('status')
        current_status = self.instance.status
        
        # Define valid status transitions
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered', 'cancelled'],
            'delivered': [],  # Cannot change from delivered
            'cancelled': [],  # Cannot change from cancelled
        }
        
        # Check if transition is valid
        if new_status not in valid_transitions.get(current_status, []):
            valid_options = valid_transitions.get(current_status, [])
            if valid_options:
                raise ValidationError(
                    f'Cannot change order status from "{current_status}" to "{new_status}". '
                    f'Valid transitions: {", ".join(valid_options)}'
                )
            else:
                raise ValidationError(
                    f'Cannot change order status from "{current_status}". '
                    f'This status is final.'
                )
        
        return new_status



class ProductVariantForm(forms.ModelForm):
    """Form for a single product variant (size / color / price / image)."""

    class Meta:
        model = ProductVariant
        fields = ['size', 'color', 'price', 'stock', 'image_url', 'image', 'is_available']
        widgets = {
            'size': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. S, M, L or 6, 7, 8'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Gold, Silver, Rose Gold'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'placeholder': 'Leave blank for unlimited'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://example.com/image.jpg (optional)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-file',
                'accept': 'image/jpeg,image/png,image/webp'
            }),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('Price must be non-negative.')
        return price

    def clean_image(self):
        """Validate uploaded image file - allow empty/None for optional image"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Check if this is a new uploaded file (has content_type) or existing image
            if hasattr(image, 'content_type'):
                # This is a newly uploaded file - validate it
                # Check file size (max 5MB)
                if image.size > 5 * 1024 * 1024:
                    raise ValidationError('Image file size cannot exceed 5MB.')
                
                # Check file type
                valid_types = ['image/jpeg', 'image/png', 'image/webp']
                if image.content_type not in valid_types:
                    raise ValidationError(
                        'Invalid image format. Supported formats: JPEG, PNG, WebP.'
                    )
                
                # Validate image integrity - just open the header, no .load() or .verify()
                # which would exhaust the file pointer and interfere with Django's validator
                try:
                    image.seek(0)
                    img = Image.open(image)
                    img.format  # forces header parse without consuming the stream
                    image.seek(0)
                except Exception as e:
                    raise ValidationError(f'Invalid or corrupted image file: {str(e)}')
            # If no content_type, it's an existing image file - no validation needed
        
        return image


# Inline formset: manage variants directly on the product add/edit page
ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=0,        # No blank rows — variants are managed via AJAX on the edit page
    can_delete=True,
)


class HeroBannerForm(forms.ModelForm):
    class Meta:
        model = HeroBanner
        fields = [
            'eyebrow', 'heading', 'subtitle',
            'pill_1', 'pill_1_icon', 'pill_1_icon_custom',
            'pill_2', 'pill_2_icon', 'pill_2_icon_custom',
            'pill_3', 'pill_3_icon', 'pill_3_icon_custom',
            'cta_primary_text', 'cta_primary_url',
            'cta_secondary_text', 'cta_secondary_url',
            'bg_color', 'bg_image_url', 'bg_image',
            'image_url', 'image', 'hide_side_image',
            'color_scheme',
            'eyebrow_color', 'heading_color', 'subtitle_color',
            'pill_text_color', 'pill_icon_color',
            'btn_primary_bg', 'btn_primary_text_color',
            'btn_secondary_bg', 'btn_secondary_text_color',
            'is_active', 'order',
        ]

        _color_widget = lambda placeholder='#000000': forms.TextInput(attrs={
            'class': 'form-input', 'type': 'color',
            'style': 'height:44px;padding:4px 8px;cursor:pointer;width:100%;',
        })

        widgets = {
            'eyebrow': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. NEW COLLECTION'}),
            'heading': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3,
                                             'placeholder': 'Main heading. Use \\n for a line break.'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Short tagline'}),
            'pill_1': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Hypoallergenic'}),
            'pill_1_icon': forms.Select(attrs={'class': 'form-select pill-icon-select', 'data-pill': '1'}),
            'pill_1_icon_custom': forms.TextInput(attrs={
                'class': 'form-input pill-icon-custom', 'data-pill': '1',
                'placeholder': 'e.g. <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
            }),
            'pill_2': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Water Resistant'}),
            'pill_2_icon': forms.Select(attrs={'class': 'form-select pill-icon-select', 'data-pill': '2'}),
            'pill_2_icon_custom': forms.TextInput(attrs={
                'class': 'form-input pill-icon-custom', 'data-pill': '2',
                'placeholder': 'e.g. <circle cx="12" cy="12" r="10"/>',
            }),
            'pill_3': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Tarnish Free'}),
            'pill_3_icon': forms.Select(attrs={'class': 'form-select pill-icon-select', 'data-pill': '3'}),
            'pill_3_icon_custom': forms.TextInput(attrs={
                'class': 'form-input pill-icon-custom', 'data-pill': '3',
                'placeholder': 'e.g. <polyline points="20 6 9 17 4 12"/>',
            }),
            'cta_primary_text':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Explore Collection'}),
            'cta_primary_url':    forms.TextInput(attrs={'class': 'form-input', 'placeholder': '#products'}),
            'cta_secondary_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Contact Us'}),
            'cta_secondary_url':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'https://wa.me/...'}),
            'bg_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color',
                                               'style': 'height:44px;padding:4px 8px;cursor:pointer;'}),
            'bg_image_url': forms.URLInput(attrs={'class': 'form-input',
                                                  'placeholder': 'https://... full-hero background image (overrides colour)'}),
            'bg_image': forms.FileInput(attrs={'class': 'form-file', 'accept': 'image/*'}),
            'image_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://... right-side image'}),
            'image': forms.FileInput(attrs={'class': 'form-file', 'accept': 'image/*'}),
            'hide_side_image': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'color_scheme': forms.Select(attrs={'class': 'form-select'}),
            'eyebrow_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color',
                                                    'style': 'height:44px;padding:4px 8px;cursor:pointer;width:100%;'}),
            'heading_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color',
                                                    'style': 'height:44px;padding:4px 8px;cursor:pointer;width:100%;'}),
            'subtitle_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color',
                                                     'style': 'height:44px;padding:4px 8px;cursor:pointer;width:100%;'}),
            'pill_text_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color',
                                                      'style': 'height:44px;padding:4px 8px;cursor:pointer;width:100%;'}),
            'pill_icon_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color',
                                                      'style': 'height:44px;padding:4px 8px;cursor:pointer;width:100%;'}),
            'btn_primary_bg': forms.TextInput(attrs={
                'class': 'form-input color-or-transparent',
                'placeholder': '#1a1a1a or transparent',
                'style': 'width:100%;',
                'data-color-companion': 'picker_btn_primary_bg',
            }),
            'btn_primary_text_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color',
                                                             'style': 'height:44px;padding:4px 8px;cursor:pointer;width:100%;'}),
            'btn_secondary_bg': forms.TextInput(attrs={
                'class': 'form-input color-or-transparent',
                'placeholder': 'transparent or #hex',
                'style': 'width:100%;',
                'data-color-companion': 'picker_btn_secondary_bg',
            }),
            'btn_secondary_text_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color',
                                                               'style': 'height:44px;padding:4px 8px;cursor:pointer;width:100%;'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
        }


class PromotionForm(forms.ModelForm):
    """Form for creating and editing promotions."""

    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_available=True).order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'product-checkbox-list'}),
        label='Apply to Products',
        help_text='Only used when scope is "Specific Products"'
    )

    variants = forms.ModelMultipleChoiceField(
        queryset=ProductVariant.objects.filter(is_available=True).select_related('product').order_by('product__name', 'size', 'color'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'product-checkbox-list'}),
        label='Apply to Variants',
        help_text='Only used when scope is "Specific Variants"'
    )

    class Meta:
        model = Promotion
        fields = [
            'name', 'discount_type', 'discount_value', 'scope',
            'products', 'variants', 'category', 'min_quantity',
            'starts_at', 'ends_at', 'is_active', 'also_discount_base',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Summer Sale 20%'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'scope': forms.Select(attrs={'class': 'form-select', 'id': 'id_scope'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'placeholder': '1'}),
            'starts_at': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'ends_at': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'also_discount_base': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['category'].empty_label = '— Select Category —'
        self.fields['category'].required = False
        # Pre-format datetime fields for the datetime-local input
        if self.instance and self.instance.pk:
            if self.instance.starts_at:
                self.initial['starts_at'] = self.instance.starts_at.strftime('%Y-%m-%dT%H:%M')
            if self.instance.ends_at:
                self.initial['ends_at'] = self.instance.ends_at.strftime('%Y-%m-%dT%H:%M')

    def clean_discount_value(self):
        val = self.cleaned_data.get('discount_value')
        if val is None or val <= 0:
            raise ValidationError('Discount value must be greater than 0.')
        dtype = self.cleaned_data.get('discount_type')
        if dtype == Promotion.TYPE_PERCENTAGE and val > 100:
            raise ValidationError('Percentage discount cannot exceed 100%.')
        return val

    def clean(self):
        cleaned = super().clean()
        scope = cleaned.get('scope')
        if scope == Promotion.SCOPE_PRODUCTS and not cleaned.get('products'):
            self.add_error('products', 'Select at least one product for "Specific Products" scope.')
        if scope == Promotion.SCOPE_CATEGORY and not cleaned.get('category'):
            self.add_error('category', 'Select a category for "Specific Category" scope.')
        starts = cleaned.get('starts_at')
        ends = cleaned.get('ends_at')
        if starts and ends and ends <= starts:
            self.add_error('ends_at', 'End date must be after start date.')
        return cleaned


class UserCreateForm(forms.Form):
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter username'
        }),
        label='Username',
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'user@example.com'
        }),
        label='Email Address',
        required=False
    )
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name'
        }),
        label='First Name',
        required=False
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name'
        }),
        label='Last Name',
        required=False
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter password'
        }),
        label='Password',
        help_text='Password must be at least 8 characters long.'
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm password'
        }),
        label='Confirm Password'
    )
    
    is_staff = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        label='Staff Status',
        help_text='Designates whether the user can log into MyAdmin.',
        initial=True,
        required=False
    )
    
    is_superuser = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        label='Superuser Status',
        help_text='Designates that this user has all permissions without explicitly assigning them.',
        initial=False,
        required=False
    )
    
    def clean_username(self):
        """Validate username is unique"""
        from django.contrib.auth.models import User
        username = self.cleaned_data.get('username')
        
        if User.objects.filter(username=username).exists():
            raise ValidationError('A user with that username already exists.')
        
        return username
    
    def clean_password1(self):
        """Validate password strength"""
        password = self.cleaned_data.get('password1')
        
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        return password
    
    def clean(self):
        """Validate passwords match"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('The two password fields must match.')
        
        return cleaned_data


class UserEditForm(forms.Form):
    """Form for editing existing staff users"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'user@example.com'
        }),
        label='Email Address',
        required=False
    )
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name'
        }),
        label='First Name',
        required=False
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name'
        }),
        label='Last Name',
        required=False
    )
    
    is_active = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        label='Active',
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
        required=False
    )
    
    is_staff = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        label='Staff Status',
        help_text='Designates whether the user can log into MyAdmin.',
        required=False
    )
    
    is_superuser = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        label='Superuser Status',
        help_text='Designates that this user has all permissions without explicitly assigning them.',
        required=False
    )


class UserPasswordChangeForm(forms.Form):
    """Form for changing user password"""
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter new password'
        }),
        label='New Password',
        help_text='Password must be at least 8 characters long.'
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm new password'
        }),
        label='Confirm New Password'
    )
    
    def clean_new_password1(self):
        """Validate password strength"""
        password = self.cleaned_data.get('new_password1')
        
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        return password
    
    def clean(self):
        """Validate passwords match"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('The two password fields must match.')
        
        return cleaned_data
