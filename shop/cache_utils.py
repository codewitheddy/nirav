"""
Cache utilities for performance optimization
"""
from django.core.cache import cache
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from decimal import Decimal
import hashlib

from .models import Order, Product, OrderItem


def cache_result(key_prefix, timeout=900):
    """
    Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache key (will be combined with arguments)
        timeout: Cache timeout in seconds (default 900 = 15 minutes)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create unique cache key based on function name and arguments
            cache_key = f"{key_prefix}_{hashlib.md5(str(args).encode() + str(sorted(kwargs.items())).encode()).hexdigest()}"
            
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
            
        return wrapper
    return decorator


def cache_dashboard_kpis():
    """
    Decorator to cache dashboard KPIs for better performance.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            cache_key = f"dashboard_kpis_{timezone.now().date()}"
            cached_data = cache.get(cache_key)
            
            if cached_data is None:
                # Calculate fresh KPIs
                current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                kpis = {
                    'total_revenue': Order.objects.filter(
                        created_at__gte=current_month,
                        status__in=['confirmed', 'processing', 'shipped', 'delivered']
                    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
                    
                    'total_orders': Order.objects.filter(
                        created_at__gte=current_month
                    ).count(),
                    
                    'total_customers': Order.objects.values('customer_name').distinct().count(),
                    
                    'total_products': Product.objects.filter(is_available=True).count(),
                }
                
                cache.set(cache_key, kpis, 900)  # Cache for 15 minutes
                cached_data = kpis
            
            # Add cached data to request for use in view
            request.cached_kpis = cached_data
            return view_func(request, *args, **kwargs)
            
        return wrapper
    return decorator


def get_top_products_cached(date_from, date_to, cache_timeout=600):
    """
    Get top products data with caching
    """
    cache_key = f"top_products_{date_from}_{date_to}"
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        # Top products by quantity
        top_products_quantity = OrderItem.objects.select_related('product').filter(
            order__created_at__date__range=[date_from, date_to]
        ).values('product__name').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:10]
        
        # Top products by revenue
        top_products_revenue = OrderItem.objects.select_related('product').filter(
            order__created_at__date__range=[date_from, date_to]
        ).values('product__name').annotate(
            total_revenue=Sum(F('quantity') * F('price'))
        ).order_by('-total_revenue')[:10]
        
        cached_data = {
            'quantity': list(top_products_quantity),
            'revenue': list(top_products_revenue),
        }
        
        cache.set(cache_key, cached_data, cache_timeout)
    
    return cached_data


def clear_dashboard_cache():
    """Clear dashboard related caches"""
    cache.delete_pattern("dashboard_kpis_*")
    cache.delete_pattern("analytics_*")
    cache.delete_pattern("top_products_*")


class CacheManager:
    """Manager for cache operations"""
    
    @staticmethod
    def invalidate_product_cache(product_id=None):
        """Invalidate product-related caches"""
        CacheManager.clear_all_dashboard_caches()
    
    @staticmethod
    def invalidate_order_cache():
        """Invalidate order-related caches"""
        CacheManager.clear_all_dashboard_caches()
    
    @staticmethod
    def clear_all_dashboard_caches():
        """Clear all dashboard caches"""
        try:
            cache.delete_pattern("dashboard_kpis_*")
            cache.delete_pattern("analytics_*")
            cache.delete_pattern("top_products_*")
        except AttributeError:
            # Fallback for cache backends that don't support patterns
            cache.clear()