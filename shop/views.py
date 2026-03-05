from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Category, Product, Order, OrderItem
from decimal import Decimal
import json
from urllib.parse import quote

def home(request):
    categories = Category.objects.all()
    # Optimize query with select_related to avoid N+1 queries
    products_list = Product.objects.filter(is_available=True).select_related('category')
    
    # Pagination - 16 products per page
    paginator = Paginator(products_list, 16)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)
    
    # Get cart from session
    cart = request.session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values())
    
    context = {
        'categories': categories,
        'products': products,
        'cart_count': cart_count,
    }
    return render(request, 'home.html', context)

@require_POST
def add_to_cart(request):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            product_id = data.get('product_id')
        else:
            product_id = request.POST.get('product_id')
        
        logger.info(f"Adding product {product_id} to cart")
        product = get_object_or_404(Product, id=product_id)
        
        cart = request.session.get('cart', {})
        logger.info(f"Current cart before add: {cart}")
        
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += 1
        else:
            cart[str(product_id)] = {
                'name': product.name,
                'price': str(product.price),
                'quantity': 1,
                'image': product.get_image_url() or ''
            }
        
        request.session['cart'] = cart
        request.session.modified = True  # Explicitly mark session as modified
        
        cart_count = sum(item['quantity'] for item in cart.values())
        logger.info(f"Cart after add: {cart}, Count: {cart_count}")
        
        return JsonResponse({'success': True, 'cart_count': cart_count})
    except Exception as e:
        logger.error(f"Error adding to cart: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def update_cart(request):
    data = json.loads(request.body)
    product_id = data.get('product_id')
    action = data.get('action')
    
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        if action == 'increase':
            cart[str(product_id)]['quantity'] += 1
        elif action == 'decrease':
            if cart[str(product_id)]['quantity'] > 1:
                cart[str(product_id)]['quantity'] -= 1
            else:
                del cart[str(product_id)]
        elif action == 'remove':
            del cart[str(product_id)]
    
    request.session['cart'] = cart
    request.session.modified = True  # Explicitly mark session as modified
    cart_count = sum(item['quantity'] for item in cart.values())
    cart_total = sum(float(item['price']) * item['quantity'] for item in cart.values())
    
    # Build cart_items array for frontend sync
    cart_items = []
    for pid, item in cart.items():
        subtotal = float(item['price']) * item['quantity']
        cart_items.append({
            'id': pid,
            'name': item['name'],
            'price': float(item['price']),
            'quantity': item['quantity'],
            'subtotal': subtotal,
            'image': item.get('image', '')
        })
    
    return JsonResponse({
        'success': True,
        'cart_count': cart_count,
        'cart_total': cart_total,
        'cart_items': cart_items
    })

def get_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    
    for product_id, item in cart.items():
        subtotal = float(item['price']) * item['quantity']
        cart_total += subtotal
        cart_items.append({
            'id': product_id,
            'name': item['name'],
            'price': float(item['price']),
            'quantity': item['quantity'],
            'subtotal': subtotal,
            'image': item.get('image', '')
        })
    
    return JsonResponse({
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': sum(item['quantity'] for item in cart.values())
    })

def checkout(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        notes = request.POST.get('notes', '')
        
        cart = request.session.get('cart', {})
        
        if not cart:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})
        
        # Calculate total
        total = sum(float(item['price']) * item['quantity'] for item in cart.values())
        
        # Create Order in database
        order = Order.objects.create(
            customer_name=name,
            customer_phone=phone,
            customer_address=address,
            notes=notes,
            total_amount=Decimal(str(total)),
            status='pending'
        )
        
        # Create OrderItems
        for product_id, item in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=Decimal(item['price'])
            )
        
        # Build WhatsApp message with basic ASCII characters only
        message = "*NEW ORDER - ThePopShopKe*\n"
        # message += "========================\n"
        # message += "*NEW ORDER RECEIVED*\n"
        message += f"Order #: {order.order_number}\n"
        message += "\n"
       
         
        # Order Items
        message += "*ORDER ITEMS*\n"
        # message += "------------------------\n"
        
        item_count = 0
        item_number = 1
        for item in cart.values():
            subtotal = float(item['price']) * item['quantity']
            item_count += item['quantity']
            message += f"{item_number}. {item['name']}\n"
            message += f"   Qty: {item['quantity']} x Ksh {float(item['price']):,.2f}\n"
            message += f"   Subtotal: Ksh {subtotal:,.2f}\n\n"
            item_number += 1
        
        # Order Summary
        # message += "========================\n"
        message += "*ORDER SUMMARY*\n"
        message += f"Total Items: {item_count}\n"
        message += f"Total Amount: Ksh {total:,.2f}\n\n"
        # message += "========================\n"

            # Customer Information
        message += "*CUSTOMER DETAILS*\n"
        message += f"Name: {name}\n"
        message += f"Phone: {phone}\n"
        message += f"Address: {address}\n"
        
        
        # Additional Notes
        if notes:
            message += f"\n*SPECIAL NOTES*\n{notes}\n"
            message += "--------------------------------\n"
        
        # Footer
        message += "\nUpon Order Placed, We'll send you Payment Details and Delivery Fees.\n"
        # message += "Delivery: 1-2 days (Nairobi)\n"
        # message += "Payment: M-Pesa/Bank/COD\n\n"
        message += "\n"
        message += "Thank you for shopping with ThePopShopKe!\n"
        
        # URL encode and create WhatsApp link
        encoded_message = quote(message)
        whatsapp_url = f"https://wa.me/254700840182?text={encoded_message}"
        
        # Clear cart
        request.session['cart'] = {}
        
        return JsonResponse({
            'success': True, 
            'whatsapp_url': whatsapp_url,
            'order_number': order.order_number
        })
    
    return JsonResponse({'success': False})



def clear_cart(request):
    """Clear cart - for testing/debugging only"""
    request.session['cart'] = {}
    request.session.modified = True
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Cart cleared for session: {request.session.session_key}")
    
    return JsonResponse({
        'success': True,
        'message': 'Cart cleared',
        'cart_count': 0
    })
