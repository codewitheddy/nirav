# from django.urls import path
# from . import views

# app_name = 'shop'

# urlpatterns = [
#     path('', views.home, name='home'),
#     path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
#     path('update-cart/', views.update_cart, name='update_cart'),
#     path('get-cart/', views.get_cart, name='get_cart'),
#     path('clear-cart/', views.clear_cart, name='clear_cart'),  # For testing/debugging
#     path('checkout/', views.checkout, name='checkout'),
# ]
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('filter-products/', views.filter_products, name='filter_products'),
    path('search/', views.search_products, name='search_products'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('get-cart/', views.get_cart, name='get_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),  # For testing/debugging
    path('checkout/', views.checkout, name='checkout'),
]
