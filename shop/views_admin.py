from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView, View
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from datetime import timedelta
from decimal import Decimal
import json
import csv

from .models import (
    Product, Category, Order, OrderItem, ProductVariant, Promotion, HeroBanner,
    Attribute, AttributeValue, VariantAttributeValue,
)
from .forms_admin import ProductForm, CategoryForm, OrderStatusForm, ProductVariantFormSet, PromotionForm, HeroBannerForm
from .cache_utils import cache_dashboard_kpis, get_top_products_cached, CacheManager

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# Authentication decorator
def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# Decorator for all admin views
staff_required = method_decorator(
    user_passes_test(is_staff_or_superuser, login_url='/myadmin/login/'),
    name='dispatch'
)


# Authentication Views
class AdminLoginView(LoginView):
    """Custom login view for MyAdmin"""
    template_name = 'myadmin/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('myadmin:dashboard')
    
    def form_valid(self, form):
        user = form.get_user()
        if not (user.is_staff or user.is_superuser):
            messages.error(self.request, 'Access denied. Staff privileges required.')
            return self.form_invalid(form)
        
        # Log successful login
        import logging
        logger = logging.getLogger('myadmin')
        logger.info(f"User {user.username} logged in from IP {self.request.META.get('REMOTE_ADDR')}")
        
        messages.success(self.request, f'Welcome back, {user.username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Log failed login attempt
        import logging
        logger = logging.getLogger('myadmin')
        username = form.data.get('username', 'unknown')
        logger.warning(f"Failed login attempt for username: {username} from IP: {self.request.META.get('REMOTE_ADDR')}")
        
        messages.error(self.request, 'Invalid credentials. Please try again.')
        return super().form_invalid(form)


class AdminLogoutView(View):
    """Custom logout view for MyAdmin"""
    
    def get(self, request):
        """Handle GET request for logout"""
        from django.contrib.auth import logout
        
        if request.user.is_authenticated:
            username = request.user.username
            
            # Log logout
            import logging
            logger = logging.getLogger('myadmin')
            logger.info(f"User {username} logged out from IP {request.META.get('REMOTE_ADDR')}")
            
            # Logout user
            logout(request)
            messages.success(request, f'You have been logged out successfully.')
        
        return redirect('/myadmin/login/')
    
    def post(self, request):
        """Handle POST request for logout (for CSRF-protected forms)"""
        return self.get(request)


# Dashboard View
@staff_required
class DashboardView(TemplateView):
    """Main dashboard with KPIs and recent orders"""
    template_name = 'myadmin/dashboard.html'
    
    @cache_dashboard_kpis()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use cached KPIs if available
        if hasattr(self.request, 'cached_kpis'):
            cached_kpis = self.request.cached_kpis
            context.update({
                'total_revenue': cached_kpis['total_revenue'],
                'total_orders': cached_kpis['total_orders'],
                'total_customers': cached_kpis['total_customers'],
                'total_products': cached_kpis['total_products'],
            })
        else:
            # Fallback to direct calculation (shouldn't happen with caching)
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            context.update({
                'total_revenue': Order.objects.filter(
                    created_at__gte=current_month,
                    status__in=['confirmed', 'processing', 'shipped', 'delivered']
                ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                'total_orders': Order.objects.filter(created_at__gte=current_month).count(),
                'total_customers': Order.objects.values('customer_name').distinct().count(),
                'total_products': Product.objects.filter(is_available=True).count(),
            })
        
        # Recent orders (last 10) - Optimized with select_related
        recent_orders = Order.objects.select_related('promotion').order_by('-created_at')[:10]
        
        # Order status distribution - No changes needed, already optimized
        status_distribution = Order.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context.update({
            'recent_orders': recent_orders,
            'status_distribution': status_distribution,
        })
        
        return context


# Product Views
@staff_required
class ProductListView(ListView):
    """List all products with search and filters"""
    model = Product
    template_name = 'myadmin/products/list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category').prefetch_related(
            'variants',
            'promotions'
        ).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Category filter
        category_filter = self.request.GET.get('category', '').strip()
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)
        
        # Availability filter
        availability_filter = self.request.GET.get('availability', '').strip()
        if availability_filter == 'available':
            queryset = queryset.filter(is_available=True)
        elif availability_filter == 'unavailable':
            queryset = queryset.filter(is_available=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['availability_filter'] = self.request.GET.get('availability', '')
        return context


@staff_required
class ProductCreateView(CreateView):
    """Create a new product"""
    model = Product
    form_class = ProductForm
    template_name = 'myadmin/products/add.html'
    success_url = reverse_lazy('myadmin:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Provide an empty formset for the management_form the template renders
        context['variant_formset'] = ProductVariantFormSet()
        return context

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Product "{self.object.name}" created successfully!')
        # Redirect straight to edit so merchant can add variants via the AJAX builder
        return redirect('myadmin:product_edit', pk=self.object.pk)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


@staff_required
class ProductUpdateView(UpdateView):
    """Update an existing product"""
    model = Product
    form_class = ProductForm
    template_name = 'myadmin/products/edit.html'
    success_url = reverse_lazy('myadmin:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the actual product instance from database (not unsaved form data)
        product = self.get_object()
        
        if self.request.POST:
            # Form submitted but invalid - use POST data with the existing product
            context['variant_formset'] = ProductVariantFormSet(
                self.request.POST, self.request.FILES, instance=product
            )
        else:
            # Initial load - use existing product (has PK)
            context['variant_formset'] = ProductVariantFormSet(instance=product)
        return context

    def form_valid(self, form):
        # Save the product first to get a PK
        self.object = form.save()
        
        # Reset all uploaded file pointers — form.save() may have consumed them,
        # and the formset is about to validate the same request.FILES objects.
        for file_obj in self.request.FILES.values():
            try:
                file_obj.seek(0)
            except Exception:
                pass
        
        # Now get the formset with the saved product instance
        # Use POST data directly since we're in form_valid (form is already valid)
        variant_formset = ProductVariantFormSet(
            self.request.POST, self.request.FILES, instance=self.object
        )
        
        if variant_formset.is_valid():
            variant = variant_formset.save(commit=False)
            # Ensure all variants have the product set
            for v in variant:
                if v.product_id is None:
                    v.product = self.object
                v.save()
            # Handle deletions
            for v in variant_formset.deleted_objects:
                v.delete()
            messages.success(self.request, f'Product "{self.object.name}" updated successfully!')
        else:
            # Formset has errors, re-render with errors
            context = self.get_context_data()
            context['variant_formset'] = variant_formset
            return self.render_to_response(context)
        
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


@staff_required
class ProductDeleteView(DeleteView):
    """Delete a product with referential integrity check"""
    model = Product
    template_name = 'myadmin/products/delete_confirm.html'
    success_url = reverse_lazy('myadmin:product_list')
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        
        # Check for associated order items
        order_item_count = OrderItem.objects.filter(product=product).count()
        if order_item_count > 0:
            messages.error(
                request,
                f'Cannot delete "{product.name}" because it appears in {order_item_count} order(s). '
                f'Products with order history cannot be deleted.'
            )
            return redirect('myadmin:product_list')
        
        product_name = product.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return response


@staff_required
class ProductBulkActionView(View):
    """Handle bulk actions on products"""
    
    def post(self, request):
        action = request.POST.get('action')
        product_ids = request.POST.getlist('product_ids')
        
        if not product_ids:
            messages.warning(request, 'No products selected.')
            return redirect('myadmin:product_list')
        
        products = Product.objects.filter(id__in=product_ids)
        
        if action == 'mark_available':
            count = products.update(is_available=True)
            messages.success(request, f'{count} product(s) marked as available.')
        
        elif action == 'mark_unavailable':
            count = products.update(is_available=False)
            messages.success(request, f'{count} product(s) marked as unavailable.')
        
        elif action == 'delete':
            # Check for order items
            if OrderItem.objects.filter(product__in=products).exists():
                messages.error(request, 'Cannot delete products with associated orders.')
            else:
                count = products.count()
                products.delete()
                messages.success(request, f'{count} product(s) deleted successfully.')
        
        return redirect('myadmin:product_list')


# Order Views
@staff_required
class OrderListView(ListView):
    """List all orders with search and filters"""
    model = Order
    template_name = 'myadmin/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.select_related('promotion').prefetch_related(
            'items__product',
            'items__variant'
        ).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) | 
                Q(customer_name__icontains=search_query)
            )
        
        # Status filter
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Date range filter
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        if date_from and date_to:
            queryset = queryset.filter(created_at__date__range=[date_from, date_to])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        return context


@staff_required
class OrderBulkActionView(View):
    """
    POST /myadmin/orders/bulk-action/
    Performs a bulk action on a selected set of orders.

    Actions:
      mark_confirmed / mark_processing / mark_shipped /
      mark_delivered / mark_cancelled  — change status
      delete                           — delete orders (with confirmation guard)
    """
    VALID_STATUS_ACTIONS = {
        'mark_confirmed':  'confirmed',
        'mark_processing': 'processing',
        'mark_shipped':    'shipped',
        'mark_delivered':  'delivered',
        'mark_cancelled':  'cancelled',
    }

    def post(self, request):
        action  = request.POST.get('action', '').strip()
        ids_raw = request.POST.getlist('order_ids')

        if not ids_raw:
            messages.warning(request, 'No orders selected.')
            return redirect('myadmin:order_list')

        try:
            order_ids = [int(i) for i in ids_raw]
        except (ValueError, TypeError):
            messages.error(request, 'Invalid order selection.')
            return redirect('myadmin:order_list')

        orders = Order.objects.select_related('promotion').filter(pk__in=order_ids)
        count  = orders.count()

        if count == 0:
            messages.warning(request, 'No matching orders found.')
            return redirect('myadmin:order_list')

        # ── Status change ─────────────────────────────────────────────
        if action in self.VALID_STATUS_ACTIONS:
            new_status = self.VALID_STATUS_ACTIONS[action]
            orders.update(status=new_status)
            label = dict(Order.STATUS_CHOICES).get(new_status, new_status).capitalize()
            messages.success(request, f'{count} order(s) marked as {label}.')

        # ── Delete ────────────────────────────────────────────────────
        elif action == 'delete':
            orders.delete()
            messages.success(request, f'{count} order(s) deleted permanently.')

        else:
            messages.error(request, f'Unknown action: {action}')

        # Preserve current filters when redirecting back
        params = request.POST.get('return_params', '')
        redirect_url = reverse_lazy('myadmin:order_list')
        if params:
            redirect_url = f'{redirect_url}?{params}'
        return redirect(redirect_url)


@staff_required
class OrderDetailView(DetailView):
    """View order details"""
    model = Order
    template_name = 'myadmin/orders/detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        
        # Get order items with products
        order_items = order.items.select_related('product').all()
        
        # Calculate subtotal sum
        subtotal_sum = sum(item.get_subtotal() for item in order_items)
        
        # Status form for updating
        context['status_form'] = OrderStatusForm(instance=order)
        context['order_items'] = order_items
        context['subtotal_sum'] = subtotal_sum
        
        return context


@staff_required
class OrderStatusUpdateView(UpdateView):
    """Update order status"""
    model = Order
    form_class = OrderStatusForm
    template_name = 'myadmin/orders/detail.html'
    
    def get_success_url(self):
        return reverse_lazy('myadmin:order_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Log status change
        import logging
        logger = logging.getLogger('myadmin')
        logger.info(
            f"Order {self.object.order_number} status changed from "
            f"{self.object.status} to {form.cleaned_data['status']} "
            f"by {self.request.user.username}"
        )
        
        messages.success(self.request, f'Order status updated to {form.cleaned_data["status"]}.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid status transition. Please check the allowed transitions.')
        return redirect('myadmin:order_detail', pk=self.object.pk)


# Category Views
@staff_required
class CategoryListView(ListView):
    """List all categories"""
    model = Category
    template_name = 'myadmin/categories/list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        return Category.objects.annotate(
            product_count=Count('products')
        ).order_by('name')


@staff_required
class CategoryCreateView(CreateView):
    """Create a new category"""
    model = Category
    form_class = CategoryForm
    template_name = 'myadmin/categories/form.html'
    success_url = reverse_lazy('myadmin:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created successfully!')
        return super().form_valid(form)


@staff_required
class CategoryUpdateView(UpdateView):
    """Update an existing category"""
    model = Category
    form_class = CategoryForm
    template_name = 'myadmin/categories/form.html'
    success_url = reverse_lazy('myadmin:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


@staff_required
class CategoryDeleteView(DeleteView):
    """Delete a category with referential integrity check"""
    model = Category
    template_name = 'myadmin/categories/delete_confirm.html'
    success_url = reverse_lazy('myadmin:category_list')
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        
        # Check for associated products
        if category.products.exists():
            product_count = category.products.count()
            messages.error(
                request,
                f'Cannot delete "{category.name}" because it has {product_count} associated product(s).'
            )
            return redirect('myadmin:category_list')
        
        category_name = category.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return response


# Analytics Views
@staff_required
class AnalyticsView(TemplateView):
    """Analytics dashboard with reports"""
    template_name = 'myadmin/analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request or default to last 30 days
        date_to = timezone.now().date()
        date_from = date_to - timedelta(days=30)
        
        if self.request.GET.get('date_from'):
            date_from = timezone.datetime.strptime(self.request.GET.get('date_from'), '%Y-%m-%d').date()
        if self.request.GET.get('date_to'):
            date_to = timezone.datetime.strptime(self.request.GET.get('date_to'), '%Y-%m-%d').date()
        
        # Filter orders by date range - Optimized with select_related
        orders = Order.objects.select_related('promotion').filter(
            created_at__date__range=[date_from, date_to]
        )
        
        # Calculate metrics
        total_revenue = orders.filter(
            status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        
        total_orders = orders.count()
        
        average_order_value = orders.aggregate(
            Avg('total_amount')
        )['total_amount__avg'] or Decimal('0.00')
        
        # Top products - Use cached version for better performance
        top_products_data = get_top_products_cached(date_from, date_to)
        top_products_quantity = top_products_data['quantity']
        top_products_revenue = top_products_data['revenue']
        
        # Order status distribution
        order_status_distribution = orders.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context.update({
            'date_from': date_from,
            'date_to': date_to,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'average_order_value': average_order_value,
            'top_products_quantity': top_products_quantity,
            'top_products_revenue': top_products_revenue,
            'order_status_distribution': order_status_distribution,
        })
        
        return context


@staff_required
class AnalyticsExportView(View):
    """Export analytics data as CSV"""
    
    def get(self, request):
        # Get date range
        date_to = timezone.now().date()
        date_from = date_to - timedelta(days=30)
        
        if request.GET.get('date_from'):
            date_from = timezone.datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d').date()
        if request.GET.get('date_to'):
            date_to = timezone.datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d').date()
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{date_from}_{date_to}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order Number', 'Customer', 'Total', 'Status', 'Date'])
        
        orders = Order.objects.select_related('promotion').filter(
            created_at__date__range=[date_from, date_to]
        ).order_by('-created_at')
        
        for order in orders:
            writer.writerow([
                order.order_number,
                order.customer_name,
                order.total_amount,
                order.get_status_display(),
                order.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response



# User Management Views
@staff_required
class UserListView(ListView):
    """List all staff users"""
    model = None  # Will use User model
    template_name = 'myadmin/users/list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        from django.contrib.auth.models import User
        queryset = User.objects.filter(is_staff=True).select_related().order_by('-date_joined')
        
        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Filter by status
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Filter by role
        role_filter = self.request.GET.get('role', '')
        if role_filter == 'superuser':
            queryset = queryset.filter(is_superuser=True)
        elif role_filter == 'staff':
            queryset = queryset.filter(is_superuser=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['role_filter'] = self.request.GET.get('role', '')
        return context


@staff_required
class UserCreateView(View):
    """Create a new staff user"""
    template_name = 'myadmin/users/form.html'
    
    def get(self, request):
        from .forms_admin import UserCreateForm
        form = UserCreateForm()
        return render(request, self.template_name, {
            'form': form,
            'title': 'Create New User',
            'action': 'Create'
        })
    
    def post(self, request):
        from django.contrib.auth.models import User
        from .forms_admin import UserCreateForm
        
        form = UserCreateForm(request.POST)
        
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data.get('email', ''),
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', '')
            )
            
            user.is_staff = form.cleaned_data.get('is_staff', True)
            user.is_superuser = form.cleaned_data.get('is_superuser', False)
            user.save()
            
            # Log action
            import logging
            logger = logging.getLogger('myadmin')
            logger.info(f"User {request.user.username} created new user: {user.username}")
            
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('myadmin:user_list')
        
        return render(request, self.template_name, {
            'form': form,
            'title': 'Create New User',
            'action': 'Create'
        })


@staff_required
class UserUpdateView(View):
    """Update an existing staff user"""
    template_name = 'myadmin/users/form.html'
    
    def get(self, request, pk):
        from django.contrib.auth.models import User
        from .forms_admin import UserEditForm
        
        user = get_object_or_404(User, pk=pk, is_staff=True)
        
        form = UserEditForm(initial={
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        })
        
        return render(request, self.template_name, {
            'form': form,
            'user_obj': user,
            'title': f'Edit User: {user.username}',
            'action': 'Update'
        })
    
    def post(self, request, pk):
        from django.contrib.auth.models import User
        from .forms_admin import UserEditForm
        
        user = get_object_or_404(User, pk=pk, is_staff=True)
        form = UserEditForm(request.POST)
        
        if form.is_valid():
            user.email = form.cleaned_data.get('email', '')
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
            user.is_active = form.cleaned_data.get('is_active', True)
            user.is_staff = form.cleaned_data.get('is_staff', True)
            user.is_superuser = form.cleaned_data.get('is_superuser', False)
            user.save()
            
            # Log action
            import logging
            logger = logging.getLogger('myadmin')
            logger.info(f"User {request.user.username} updated user: {user.username}")
            
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('myadmin:user_list')
        
        return render(request, self.template_name, {
            'form': form,
            'user_obj': user,
            'title': f'Edit User: {user.username}',
            'action': 'Update'
        })


@staff_required
class UserPasswordChangeView(View):
    """Change user password"""
    template_name = 'myadmin/users/password_change.html'
    
    def get(self, request, pk):
        from django.contrib.auth.models import User
        from .forms_admin import UserPasswordChangeForm
        
        user = get_object_or_404(User, pk=pk, is_staff=True)
        form = UserPasswordChangeForm()
        
        return render(request, self.template_name, {
            'form': form,
            'user_obj': user
        })
    
    def post(self, request, pk):
        from django.contrib.auth.models import User
        from .forms_admin import UserPasswordChangeForm
        
        user = get_object_or_404(User, pk=pk, is_staff=True)
        form = UserPasswordChangeForm(request.POST)
        
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # Log action
            import logging
            logger = logging.getLogger('myadmin')
            logger.info(f"User {request.user.username} changed password for user: {user.username}")
            
            messages.success(request, f'Password for "{user.username}" changed successfully.')
            return redirect('myadmin:user_list')
        
        return render(request, self.template_name, {
            'form': form,
            'user_obj': user
        })


@staff_required
class UserDeleteView(View):
    """Delete a staff user"""
    template_name = 'myadmin/users/delete_confirm.html'
    
    def get(self, request, pk):
        from django.contrib.auth.models import User
        user = get_object_or_404(User, pk=pk, is_staff=True)
        
        # Prevent deleting yourself
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('myadmin:user_list')
        
        return render(request, self.template_name, {'user_obj': user})
    
    def post(self, request, pk):
        from django.contrib.auth.models import User
        user = get_object_or_404(User, pk=pk, is_staff=True)
        
        # Prevent deleting yourself
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('myadmin:user_list')
        
        username = user.username
        user.delete()
        
        # Log action
        import logging
        logger = logging.getLogger('myadmin')
        logger.info(f"User {request.user.username} deleted user: {username}")
        
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('myadmin:user_list')


# ── Promotion Views ───────────────────────────────────────────────────────────

@staff_required
class PromotionListView(ListView):
    model = Promotion
    template_name = 'myadmin/promotions/list.html'
    context_object_name = 'promotions'
    paginate_by = 20

    def get_queryset(self):
        from django.utils import timezone as tz
        qs = Promotion.objects.select_related('category').prefetch_related(
            'products',
            'variants'
        ).order_by('-created_at')
        now = tz.now()
        # Annotate status for display
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.utils import timezone as tz
        ctx['now'] = tz.now()
        return ctx


@staff_required
class PromotionCreateView(View):
    template_name = 'myadmin/promotions/form.html'

    def _variant_qs(self):
        from .models import ProductVariant
        return ProductVariant.objects.filter(is_available=True).select_related('product').prefetch_related(
            'attribute_values__attribute_value__attribute'
        ).order_by('product__name', 'size', 'color')

    def get(self, request):
        form = PromotionForm()
        return render(request, self.template_name, {
            'form': form,
            'title': 'Create Promotion',
            'action': 'Create',
            'all_products': Product.objects.select_related('category').filter(is_available=True).order_by('category__name', 'name'),
            'selected_product_ids': [],
            'all_variants': self._variant_qs(),
            'selected_variant_ids': [],
        })

    def post(self, request):
        form = PromotionForm(request.POST)
        if form.is_valid():
            promo = form.save()
            messages.success(request, f'Promotion "{promo.name}" created successfully.')
            return redirect('myadmin:promotion_list')
        selected_ids = [int(x) for x in request.POST.getlist('products') if x.isdigit()]
        selected_variant_ids = [int(x) for x in request.POST.getlist('variants') if x.isdigit()]
        return render(request, self.template_name, {
            'form': form,
            'title': 'Create Promotion',
            'action': 'Create',
            'all_products': Product.objects.select_related('category').filter(is_available=True).order_by('category__name', 'name'),
            'selected_product_ids': selected_ids,
            'all_variants': self._variant_qs(),
            'selected_variant_ids': selected_variant_ids,
        })


@staff_required
class PromotionUpdateView(View):
    template_name = 'myadmin/promotions/form.html'

    def _variant_qs(self):
        from .models import ProductVariant
        return ProductVariant.objects.filter(is_available=True).select_related('product').prefetch_related(
            'attribute_values__attribute_value__attribute'
        ).order_by('product__name', 'size', 'color')

    def get(self, request, pk):
        promo = get_object_or_404(Promotion, pk=pk)
        form = PromotionForm(instance=promo)
        selected_ids = list(promo.products.values_list('id', flat=True))
        selected_variant_ids = list(promo.variants.values_list('id', flat=True))
        return render(request, self.template_name, {
            'form': form,
            'promo': promo,
            'title': f'Edit: {promo.name}',
            'action': 'Update',
            'all_products': Product.objects.select_related('category').filter(is_available=True).order_by('category__name', 'name'),
            'selected_product_ids': selected_ids,
            'all_variants': self._variant_qs(),
            'selected_variant_ids': selected_variant_ids,
        })

    def post(self, request, pk):
        promo = get_object_or_404(Promotion, pk=pk)
        form = PromotionForm(request.POST, instance=promo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Promotion "{promo.name}" updated.')
            return redirect('myadmin:promotion_list')
        selected_ids = [int(x) for x in request.POST.getlist('products') if x.isdigit()]
        selected_variant_ids = [int(x) for x in request.POST.getlist('variants') if x.isdigit()]
        return render(request, self.template_name, {
            'form': form,
            'promo': promo,
            'title': f'Edit: {promo.name}',
            'action': 'Update',
            'all_products': Product.objects.select_related('category').filter(is_available=True).order_by('category__name', 'name'),
            'selected_product_ids': selected_ids,
            'all_variants': self._variant_qs(),
            'selected_variant_ids': selected_variant_ids,
        })


@staff_required
class PromotionDeleteView(View):
    template_name = 'myadmin/promotions/delete_confirm.html'

    def get(self, request, pk):
        promo = get_object_or_404(Promotion, pk=pk)
        return render(request, self.template_name, {'promo': promo})

    def post(self, request, pk):
        promo = get_object_or_404(Promotion, pk=pk)
        name = promo.name
        promo.delete()
        messages.success(request, f'Promotion "{name}" deleted.')
        return redirect('myadmin:promotion_list')


@staff_required
class PromotionToggleView(View):
    """Quick-toggle active/inactive via POST."""

    def post(self, request, pk):
        promo = get_object_or_404(Promotion, pk=pk)
        promo.is_active = not promo.is_active
        promo.save(update_fields=['is_active'])
        state = 'activated' if promo.is_active else 'deactivated'
        messages.success(request, f'Promotion "{promo.name}" {state}.')
        return redirect('myadmin:promotion_list')


# ── Hero Banner Views ─────────────────────────────────────────────────────────

@staff_required
class HeroBannerListView(ListView):
    model = HeroBanner
    template_name = 'myadmin/hero/list.html'
    context_object_name = 'banners'
    paginate_by = 20
    ordering = ['order', '-created_at']


@staff_required
class HeroBannerCreateView(View):
    template_name = 'myadmin/hero/form.html'

    def get(self, request):
        form = HeroBannerForm()
        return render(request, self.template_name, {'form': form, 'title': 'Create Banner', 'action': 'Create'})

    def post(self, request):
        form = HeroBannerForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save()
            messages.success(request, f'Banner "{banner}" created.')
            return redirect('myadmin:hero_list')
        return render(request, self.template_name, {'form': form, 'title': 'Create Banner', 'action': 'Create'})


@staff_required
class HeroBannerUpdateView(View):
    template_name = 'myadmin/hero/form.html'

    def get(self, request, pk):
        banner = get_object_or_404(HeroBanner, pk=pk)
        form = HeroBannerForm(instance=banner)
        return render(request, self.template_name, {'form': form, 'banner': banner, 'title': 'Edit Banner', 'action': 'Update'})

    def post(self, request, pk):
        banner = get_object_or_404(HeroBanner, pk=pk)
        form = HeroBannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, f'Banner updated.')
            return redirect('myadmin:hero_list')
        return render(request, self.template_name, {'form': form, 'banner': banner, 'title': 'Edit Banner', 'action': 'Update'})


@staff_required
class HeroBannerDeleteView(View):
    template_name = 'myadmin/hero/delete_confirm.html'

    def get(self, request, pk):
        banner = get_object_or_404(HeroBanner, pk=pk)
        return render(request, self.template_name, {'banner': banner})

    def post(self, request, pk):
        banner = get_object_or_404(HeroBanner, pk=pk)
        banner.delete()
        messages.success(request, 'Banner deleted.')
        return redirect('myadmin:hero_list')


@staff_required
class HeroBannerToggleView(View):
    def post(self, request, pk):
        banner = get_object_or_404(HeroBanner, pk=pk)
        banner.is_active = not banner.is_active
        banner.save(update_fields=['is_active'])
        state = 'activated' if banner.is_active else 'deactivated'
        messages.success(request, f'Banner {state}.')
        return redirect('myadmin:hero_list')


@staff_required
class HeroBannerClearImageView(View):
    """Clears either the bg_image/bg_image_url or image/image_url from a banner."""

    def post(self, request, pk):
        import os
        banner = get_object_or_404(HeroBanner, pk=pk)
        field = request.POST.get('field')  # 'bg' or 'side'

        if field == 'bg':
            # Delete the uploaded file from disk if it exists
            if banner.bg_image:
                try:
                    if os.path.isfile(banner.bg_image.path):
                        os.remove(banner.bg_image.path)
                except Exception:
                    pass
                banner.bg_image = None
            banner.bg_image_url = ''
            banner.save(update_fields=['bg_image', 'bg_image_url'])
            messages.success(request, 'Background image removed.')

        elif field == 'side':
            if banner.image:
                try:
                    if os.path.isfile(banner.image.path):
                        os.remove(banner.image.path)
                except Exception:
                    pass
                banner.image = None
            banner.image_url = ''
            banner.save(update_fields=['image', 'image_url'])
            messages.success(request, 'Side image removed.')

        else:
            messages.error(request, 'Unknown image field.')

        return redirect('myadmin:hero_edit', pk=pk)


# ══════════════════════════════════════════════════════════════════════════════
# ── AJAX API Views for Attribute/Variant Management ──────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

@staff_required
class UpdateProductStockView(View):
    """
    POST /myadmin/products/<pk>/stock/
    Updates the stock field on a simple (non-variant) product.
    Body: {"stock": 10}  or  {"stock": null} for unlimited
    """
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            data = json.loads(request.body)
            stock_val = data.get('stock')
            product.stock = int(stock_val) if stock_val is not None else None
            product.save(update_fields=['stock'])
            return JsonResponse({'success': True, 'stock': product.stock})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_required
class GetProductAttributesView(View):
    """
    GET /myadmin/products/<pk>/attributes/
    Returns JSON list of attributes + values for a product.
    """
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        attrs = product.attributes.prefetch_related('values').order_by('position', 'id')
        data = []
        for attr in attrs:
            data.append({
                'id': attr.id,
                'name': attr.name,
                'position': attr.position,
                'values': [
                    {'id': v.id, 'value': v.value, 'position': v.position}
                    for v in attr.values.all()
                ],
            })
        return JsonResponse({'attributes': data})


@staff_required
class SaveProductAttributesView(View):
    """
    POST /myadmin/products/<pk>/attributes/save/
    Saves the full attribute + value structure for a product.
    Body: {"attributes": [{"name": "Color", "values": ["Red", "Blue"]}, ...]}
    """
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            data = json.loads(request.body)
            attributes_data = data.get('attributes', [])
            
            # Clear existing attributes (cascades to values)
            product.attributes.all().delete()
            
            # Recreate
            for pos, attr_dict in enumerate(attributes_data):
                attr = Attribute.objects.create(
                    product=product,
                    name=attr_dict['name'].strip(),
                    position=pos,
                )
                for vpos, val_str in enumerate(attr_dict.get('values', [])):
                    if val_str.strip():
                        AttributeValue.objects.create(
                            attribute=attr,
                            value=val_str.strip(),
                            position=vpos,
                        )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_required
class GenerateVariantsView(View):
    """
    POST /myadmin/products/<pk>/generate-variants/
    Body: {"combinations": [[valueId1, valueId2], ...], "base_price": "1500"}
    Generates ProductVariant rows and links them via VariantAttributeValue.
    """
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            data = json.loads(request.body)
            combinations = data.get('combinations', [])
            base_price = Decimal(data.get('base_price', product.price))
            
            created_count = 0
            for combo in combinations:
                # combo is a list of AttributeValue IDs
                if not combo:
                    continue
                
                # Check if this exact combination already exists
                # We'll do a simple approach: create the variant, then link it
                variant = ProductVariant.objects.create(
                    product=product,
                    price=base_price,
                    is_available=True,
                )
                
                # Link attribute values
                for av_id in combo:
                    av = AttributeValue.objects.get(id=av_id)
                    VariantAttributeValue.objects.create(
                        variant=variant,
                        attribute_value=av,
                    )
                
                created_count += 1
            
            return JsonResponse({
                'success': True,
                'created_count': created_count,
                'message': f'{created_count} variant(s) created',
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_required
class GetProductVariantsView(View):
    """
    GET /myadmin/products/<pk>/variants/
    Returns JSON list of all variants with their attributes.
    """
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        variants = product.variants.prefetch_related(
            'attribute_values__attribute_value__attribute'
        ).order_by('id')
        
        data = []
        for v in variants:
            # Build attribute dict
            attrs = {}
            for vav in v.attribute_values.select_related('attribute_value__attribute'):
                attr_name = vav.attribute_value.attribute.name
                attrs[attr_name] = vav.attribute_value.value
            
            data.append({
                'id': v.id,
                'sku': v.sku or '',
                'display_name': v.display_name,
                'attributes': attrs,
                'price': str(v.price),
                'cost_price': str(v.cost_price) if v.cost_price else '',
                'stock': v.stock,
                'weight': str(v.weight) if v.weight else '',
                'image_url': v.image_url or '',
                'image': v.image.url if v.image else '',
                'is_available': v.is_available,
                'stock_status': v.stock_status,
            })
        
        return JsonResponse({'variants': data})


@staff_required
class UpdateVariantView(View):
    """
    POST /myadmin/variants/<pk>/update/
    Updates a single variant's fields.
    Body: {"sku": "...", "price": "...", "stock": ..., ...}
    """
    def post(self, request, pk):
        variant = get_object_or_404(ProductVariant, pk=pk)
        try:
            data = json.loads(request.body)
            
            if 'sku' in data:
                variant.sku = data['sku'].strip() or None
            if 'price' in data:
                variant.price = Decimal(data['price'])
            if 'cost_price' in data:
                val = data['cost_price'].strip()
                variant.cost_price = Decimal(val) if val else None
            if 'stock' in data:
                val = data['stock']
                variant.stock = int(val) if val not in (None, '') else None
            if 'weight' in data:
                val = data['weight'].strip()
                variant.weight = Decimal(val) if val else None
            if 'is_available' in data:
                variant.is_available = bool(data['is_available'])
            
            variant.save()
            return JsonResponse({'success': True, 'variant_id': variant.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_required
class DeleteVariantView(View):
    """
    POST /myadmin/variants/<pk>/delete/
    Deletes a variant.
    """
    def post(self, request, pk):
        variant = get_object_or_404(ProductVariant, pk=pk)
        try:
            variant.delete()
            return JsonResponse({'success': True, 'message': 'Variant deleted'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ══════════════════════════════════════════════════════════════════════════════
# ── Cache Invalidation Signals ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Clear dashboard cache when product is saved or deleted"""
    CacheManager.clear_all_dashboard_caches()


@receiver([post_save, post_delete], sender=Order)
def invalidate_order_cache(sender, instance, **kwargs):
    """Clear dashboard cache when order is saved or deleted"""
    CacheManager.clear_all_dashboard_caches()


@receiver([post_save, post_delete], sender=OrderItem)
def invalidate_order_item_cache(sender, instance, **kwargs):
    """Clear dashboard cache when order item is saved or deleted"""
    CacheManager.clear_all_dashboard_caches()


@receiver([post_save, post_delete], sender=Promotion)
def invalidate_promotion_cache(sender, instance, **kwargs):
    """Clear dashboard cache when promotion is saved or deleted"""
    CacheManager.clear_all_dashboard_caches()
