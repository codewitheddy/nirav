from django.urls import path
from . import views_admin

app_name = 'myadmin'

urlpatterns = [
    # Authentication
    path('login/', views_admin.AdminLoginView.as_view(), name='login'),
    path('logout/', views_admin.AdminLogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', views_admin.DashboardView.as_view(), name='dashboard'),
    
    # Products
    path('products/', views_admin.ProductListView.as_view(), name='product_list'),
    path('products/add/', views_admin.ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', views_admin.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views_admin.ProductDeleteView.as_view(), name='product_delete'),
    path('products/bulk-action/', views_admin.ProductBulkActionView.as_view(), name='product_bulk_action'),

    # Product Attribute + Variant AJAX endpoints
    path('products/<int:pk>/stock/', views_admin.UpdateProductStockView.as_view(), name='product_stock_update'),
    path('products/<int:pk>/attributes/', views_admin.GetProductAttributesView.as_view(), name='product_attributes'),
    path('products/<int:pk>/attributes/save/', views_admin.SaveProductAttributesView.as_view(), name='product_attributes_save'),
    path('products/<int:pk>/generate-variants/', views_admin.GenerateVariantsView.as_view(), name='product_generate_variants'),
    path('products/<int:pk>/variants/', views_admin.GetProductVariantsView.as_view(), name='product_variants'),
    path('variants/<int:pk>/update/', views_admin.UpdateVariantView.as_view(), name='variant_update'),
    path('variants/<int:pk>/delete/', views_admin.DeleteVariantView.as_view(), name='variant_delete'),
    
    # Orders
    path('orders/', views_admin.OrderListView.as_view(), name='order_list'),
    path('orders/bulk-action/', views_admin.OrderBulkActionView.as_view(), name='order_bulk_action'),
    path('orders/<int:pk>/', views_admin.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/update-status/', views_admin.OrderStatusUpdateView.as_view(), name='order_update_status'),
    
    # Categories
    path('categories/', views_admin.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views_admin.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views_admin.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views_admin.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Analytics
    path('analytics/', views_admin.AnalyticsView.as_view(), name='analytics'),
    path('analytics/export/', views_admin.AnalyticsExportView.as_view(), name='analytics_export'),
    
    # User Management
    path('users/', views_admin.UserListView.as_view(), name='user_list'),
    path('users/add/', views_admin.UserCreateView.as_view(), name='user_add'),
    path('users/<int:pk>/edit/', views_admin.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/password/', views_admin.UserPasswordChangeView.as_view(), name='user_password_change'),
    path('users/<int:pk>/delete/', views_admin.UserDeleteView.as_view(), name='user_delete'),

    # Promotions
    path('promotions/', views_admin.PromotionListView.as_view(), name='promotion_list'),
    path('promotions/add/', views_admin.PromotionCreateView.as_view(), name='promotion_add'),
    path('promotions/<int:pk>/edit/', views_admin.PromotionUpdateView.as_view(), name='promotion_edit'),
    path('promotions/<int:pk>/delete/', views_admin.PromotionDeleteView.as_view(), name='promotion_delete'),
    path('promotions/<int:pk>/toggle/', views_admin.PromotionToggleView.as_view(), name='promotion_toggle'),

    # Hero Banners
    path('hero/', views_admin.HeroBannerListView.as_view(), name='hero_list'),
    path('hero/add/', views_admin.HeroBannerCreateView.as_view(), name='hero_add'),
    path('hero/<int:pk>/edit/', views_admin.HeroBannerUpdateView.as_view(), name='hero_edit'),
    path('hero/<int:pk>/delete/', views_admin.HeroBannerDeleteView.as_view(), name='hero_delete'),
    path('hero/<int:pk>/toggle/', views_admin.HeroBannerToggleView.as_view(), name='hero_toggle'),
    path('hero/<int:pk>/clear-image/', views_admin.HeroBannerClearImageView.as_view(), name='hero_clear_image'),
]
