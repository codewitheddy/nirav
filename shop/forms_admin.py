from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import Product, Category, Order
from PIL import Image
from io import BytesIO


class ProductForm(forms.ModelForm):
    """Form for creating and updating products"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'short_description', 'description',
            'price', 'image_url', 'image_base64', 'image', 'is_available'
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
                
                # Validate image integrity
                try:
                    img = Image.open(image)
                    img.verify()
                    # Reset file pointer after verify
                    image.seek(0)
                except Exception:
                    raise ValidationError('Invalid or corrupted image file.')
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



class UserCreateForm(forms.Form):
    """Form for creating new staff users"""
    
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
