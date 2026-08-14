from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField, Value
from .models import Category, Product, ProductVariant, Order, OrderItem
from decimal import Decimal
import json
from urllib.parse import quote


SORT_OPTIONS = {
    'newest':       '-created_at',
    'oldest':       'created_at',
    'price_asc':    'price',
    'price_desc':   '-price',
    'on_sale':      None,        # handled specially
    'best_selling': None,        # handled specially
    'featured':     None,        # handled specially
}


def _apply_sort(products_list, sort):
    """Apply sorting to a Product queryset."""
    if sort == 'best_selling':
        from django.db.models import Count
        return (
            products_list
            .annotate(times_sold=Coalesce(
                Sum('orderitem__quantity'), Value(0), output_field=IntegerField()
            ))
            .order_by('-times_sold', '-created_at')
        )
    if sort == 'featured':
        return products_list.filter(is_featured=True).order_by('-created_at')

    if sort == 'on_sale':
        from django.utils import timezone as tz
        from django.db.models import Q as DQ
        now = tz.now()
        # Get IDs of products that have an active promotion
        from .models import Promotion
        active_promos = Promotion.objects.filter(
            is_active=True,
        ).filter(
            DQ(starts_at__isnull=True) | DQ(starts_at__lte=now)
        ).filter(
            DQ(ends_at__isnull=True) | DQ(ends_at__gt=now)
        )
        sale_ids = set()
        for promo in active_promos.prefetch_related('products', 'variants'):
            if promo.scope == 'all':
                return products_list.order_by('-created_at')
            elif promo.scope == 'category' and promo.category_id:
                sale_ids.update(
                    products_list.filter(category_id=promo.category_id).values_list('id', flat=True)
                )
            elif promo.scope == 'products':
                ids = list(promo.products.values_list('id', flat=True))
                sale_ids.update(ids)
            elif promo.scope == 'variants':
                # Collect the parent product IDs of the discounted variants
                sale_ids.update(
                    promo.variants.values_list('product_id', flat=True)
                )
        return products_list.filter(id__in=sale_ids).order_by('-created_at')

    order_field = SORT_OPTIONS.get(sort, '-created_at')
    return products_list.order_by(order_field)


def home(request):
    categories = Category.objects.all()
    category_slug = request.GET.get('category', 'all')
    sort = request.GET.get('sort', 'newest')
    if sort not in SORT_OPTIONS:
        sort = 'newest'

    products_list = Product.objects.filter(is_available=True).select_related('category').prefetch_related('variants')

    if category_slug and category_slug != 'all':
        try:
            selected_category = Category.objects.get(slug=category_slug)
            products_list = products_list.filter(category=selected_category)
        except Category.DoesNotExist:
            pass

    products_list = _apply_sort(products_list, sort)

    paginator = Paginator(products_list, 16)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)
    cart = request.session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values())

    from .models import HeroBanner
    hero_banner = HeroBanner.objects.filter(is_active=True).order_by('order', '-created_at').first()

    context = {
        'categories': categories,
        'products': products,
        'cart_count': cart_count,
        'selected_category': category_slug,
        'current_sort': sort,
        'hero_banner': hero_banner,
    }
    return render(request, 'home.html', context)

def filter_products(request):
    """AJAX endpoint for filtering products by category"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        category_slug = request.GET.get('category', 'all')
        page_number   = request.GET.get('page', 1)
        sort          = request.GET.get('sort', 'newest')
        if sort not in SORT_OPTIONS:
            sort = 'newest'

        logger.info(f"Filter request - Category: {category_slug}, Page: {page_number}, Sort: {sort}")

        products_list = Product.objects.filter(is_available=True).select_related('category').prefetch_related('variants')

        if category_slug and category_slug != 'all':
            try:
                selected_category = Category.objects.get(slug=category_slug)
                products_list = products_list.filter(category=selected_category)
                logger.info(f"Filtered by category: {selected_category.name}")
            except Category.DoesNotExist:
                logger.warning(f"Category not found: {category_slug}")

        products_list = _apply_sort(products_list, sort)

        paginator = Paginator(products_list, 16)
        products  = paginator.get_page(page_number)

        logger.info(f"Found {paginator.count} products, showing page {products.number} of {paginator.num_pages}")

        cart = request.session.get('cart', {})

        products_html = render_to_string('partials/products_grid.html', {
            'products': products,
            'cart': cart,
        }, request=request)

        pagination_html = render_to_string('partials/pagination.html', {
            'products': products,
            'category': category_slug,
        }, request=request)

        response_data = {
            'success': True,
            'products_html': products_html,
            'pagination_html': pagination_html,
            'total_count': paginator.count,
            'page_count': paginator.num_pages,
            'current_page': products.number,
            'category': category_slug,
            'sort': sort,
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error in filter_products: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


@require_POST
def add_to_cart(request):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            product_id = data.get('product_id')
            variant_id = data.get('variant_id')
        else:
            product_id = request.POST.get('product_id')
            variant_id = request.POST.get('variant_id')
        
        logger.info(f"Adding product {product_id} (variant {variant_id}) to cart")
        product = get_object_or_404(Product, id=product_id)
        
        # Resolve price and image from variant if provided
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product, is_available=True)
            except ProductVariant.DoesNotExist:
                pass
        
        if variant:
            promo = product._best_promo_for_variant(variant)
            if promo:
                from decimal import Decimal
                discount = promo.calculate_discount(variant.price)
                effective_price = max(variant.price - discount, Decimal('0'))
                original_price = str(variant.price)
            else:
                effective_price = variant.price
                original_price = None
            price = str(effective_price)
            image = variant.get_image_url() or ''
            display_name = f"{product.name} ({variant.display_name})"
        else:
            # Use sale_price if an active promotion applies, otherwise use base price
            effective_price = product.sale_price
            if effective_price is not None:
                original_price = str(product.price)
                price = str(effective_price)
            else:
                original_price = None
                price = str(product.price)
            image = product.get_image_url() or ''
            display_name = product.name

        # Cart key is "productId" or "productId_variantId" for variant items
        cart_key = f"{product_id}_{variant_id}" if variant_id else str(product_id)

        cart = request.session.get('cart', {})

        # ── Stock check ───────────────────────────────────────────────────
        # Variant stock takes priority; if unset fall back to parent product stock
        if variant:
            available_stock = variant.stock if variant.stock is not None else product.stock
        else:
            available_stock = product.stock
        current_qty = cart[cart_key]['quantity'] if cart_key in cart else 0

        if available_stock is not None and current_qty >= available_stock:
            return JsonResponse({
                'success': False,
                'error': f'Only {available_stock} item(s) available in stock.',
                'stock_limit': available_stock,
            }, status=400)

        if cart_key in cart:
            cart[cart_key]['quantity'] += 1
        else:
            cart[cart_key] = {
                'product_id': str(product_id),
                'variant_id': str(variant_id) if variant_id else None,
                'name': display_name,
                'price': price,
                'original_price': original_price,
                'quantity': 1,
                'image': image,
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        cart_count = sum(item['quantity'] for item in cart.values())
        logger.info(f"Cart after add: count={cart_count}")
        
        return JsonResponse({'success': True, 'cart_count': cart_count, 'cart_key': cart_key})
    except Exception as e:
        logger.error(f"Error adding to cart: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def update_cart(request):
    data = json.loads(request.body)
    cart_key = data.get('cart_key') or str(data.get('product_id'))
    action = data.get('action')

    cart = request.session.get('cart', {})

    if cart_key in cart:
        if action == 'increase':
            item = cart[cart_key]
            # Re-fetch live stock so the cart can never exceed available quantity
            pid = item.get('product_id', cart_key.split('_')[0])
            vid = item.get('variant_id')
            try:
                if vid:
                    from .models import ProductVariant
                    v = ProductVariant.objects.select_related('product').get(id=vid)
                    # Use variant stock if set; fall back to parent product stock
                    available = v.stock if v.stock is not None else v.product.stock
                else:
                    from .models import Product as _P
                    p = _P.objects.get(id=pid)
                    available = p.stock
            except Exception:
                available = None

            if available is not None and item['quantity'] >= available:
                # Return current state unchanged with an error flag
                cart_count = sum(i['quantity'] for i in cart.values())
                cart_total = sum(float(i['price']) * i['quantity'] for i in cart.values())
                cart_items = []
                for key, i in cart.items():
                    subtotal = float(i['price']) * i['quantity']
                    orig = i.get('original_price')
                    cart_items.append({
                        'id': key,
                        'product_id': i.get('product_id', key),
                        'variant_id': i.get('variant_id'),
                        'name': i['name'],
                        'price': float(i['price']),
                        'original_price': float(orig) if orig else None,
                        'quantity': i['quantity'],
                        'subtotal': subtotal,
                        'image': i.get('image', ''),
                        'stock': available,
                    })
                return JsonResponse({
                    'success': False,
                    'error': f'Only {available} item(s) in stock.',
                    'stock_limit': available,
                    'cart_count': cart_count,
                    'cart_total': cart_total,
                    'cart_items': cart_items,
                })
            cart[cart_key]['quantity'] += 1
        elif action == 'decrease':
            if cart[cart_key]['quantity'] > 1:
                cart[cart_key]['quantity'] -= 1
            else:
                del cart[cart_key]
        elif action == 'remove':
            del cart[cart_key]
    
    request.session['cart'] = cart
    request.session.modified = True
    cart_count = sum(item['quantity'] for item in cart.values())
    cart_total = sum(float(item['price']) * item['quantity'] for item in cart.values())
    
    # Build cart_items array for frontend sync
    cart_items = []
    for key, item in cart.items():
        subtotal = float(item['price']) * item['quantity']
        orig = item.get('original_price')
        cart_items.append({
            'id': key,
            'product_id': item.get('product_id', key),
            'variant_id': item.get('variant_id'),
            'name': item['name'],
            'price': float(item['price']),
            'original_price': float(orig) if orig else None,
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

    # Batch-fetch live stock for all items in one pass
    product_ids = set()
    variant_ids = set()
    for item in cart.values():
        pid = item.get('product_id')
        vid = item.get('variant_id')
        if vid:
            variant_ids.add(int(vid))
        elif pid:
            product_ids.add(int(pid))

    from .models import Product as _P, ProductVariant as _PV
    product_stock = {p.id: p.stock for p in _P.objects.filter(id__in=product_ids).only('id', 'stock')}
    _variants = _PV.objects.filter(id__in=variant_ids).select_related('product').only('id', 'stock', 'product_id')
    variant_stock = {v.id: (v.stock, v.product_id, v.product.stock) for v in _variants}

    for key, item in cart.items():
        subtotal = float(item['price']) * item['quantity']
        cart_total += subtotal
        orig = item.get('original_price')
        vid = item.get('variant_id')
        pid = item.get('product_id', key.split('_')[0])
        if vid and int(vid) in variant_stock:
            v_stock, v_pid, parent_stock = variant_stock[int(vid)]
            # Use variant stock if set, otherwise fall back to parent product stock
            stock = v_stock if v_stock is not None else parent_stock
        else:
            stock = product_stock.get(int(pid)) if pid else None
        cart_items.append({
            'id': key,
            'product_id': pid,
            'variant_id': vid,
            'name': item['name'],
            'price': float(item['price']),
            'original_price': float(orig) if orig else None,
            'quantity': item['quantity'],
            'subtotal': subtotal,
            'image': item.get('image', ''),
            'stock': stock,       # None = unlimited; int = hard limit
        })

    return JsonResponse({
        'success': True,
        'cart': cart,
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

        # ── Server-side stock validation ───────────────────────────────
        # Re-fetch live stock for every cart item and reject the order if
        # any item exceeds available stock. This is the final gate — it
        # catches race conditions where two customers checked out at the
        # same time or the stock was reduced by the admin after the
        # customer added the item.
        stock_errors = []
        for cart_key, item in cart.items():
            pid = item.get('product_id', cart_key.split('_')[0])
            vid = item.get('variant_id')
            qty = item['quantity']
            try:
                if vid:
                    v = ProductVariant.objects.select_related('product').get(id=vid)
                    available = v.stock if v.stock is not None else v.product.stock
                    name = item['name']
                else:
                    p = Product.objects.get(id=pid)
                    available = p.stock
                    name = item['name']
                if available is not None and qty > available:
                    if available == 0:
                        stock_errors.append(f'"{name}" is out of stock.')
                    else:
                        stock_errors.append(
                            f'"{name}" — only {available} available, you have {qty} in cart.'
                        )
            except (Product.DoesNotExist, ProductVariant.DoesNotExist):
                stock_errors.append(f'"{item["name"]}" is no longer available.')

        if stock_errors:
            return JsonResponse({
                'success': False,
                'error': 'Some items in your cart exceed available stock:\n' + '\n'.join(stock_errors),
                'stock_errors': stock_errors,
            }, status=400)

        # ── Calculate subtotal ──────────────────────────────────────────
        subtotal = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())
        total_qty = sum(item['quantity'] for item in cart.values())

        # ── Find best applicable active promotion ──────────────────────
        from .models import Promotion
        from django.utils import timezone as tz
        now = tz.now()

        active_promos = Promotion.objects.prefetch_related('products').select_related('category').filter(
            is_active=True
        ).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now)
        )

        best_promo = None
        best_discount = Decimal('0')

        import logging
        logger = logging.getLogger('myadmin')
        
        logger.info(f"🔍 CHECKOUT DEBUG: total_qty={total_qty}, subtotal={subtotal}")
        logger.info(f"🔍 Cart items: {list(cart.keys())}")
        for promo in active_promos:
            logger.info(f"🔍 Checking promo: {promo.name}, min_qty={promo.min_quantity}, scope={promo.scope}")
            if total_qty < promo.min_quantity:
                logger.info(f"   ❌ total_qty ({total_qty}) < min_quantity ({promo.min_quantity})")
                continue

            # Calculate discount against qualifying items only
            # For bulk promotions (min_quantity > 1), we evaluate ALL items including
            # those already discounted, to find if bulk discount is better overall.
            # For individual promotions (min_quantity = 1), skip already-discounted items.
            promo_discount = Decimal('0')
            for cart_key, item in cart.items():
                pid = item.get('product_id', cart_key.split('_')[0])
                vid = item.get('variant_id')
                # If the item was already discounted at add-to-cart, its
                # original_price holds the pre-discount price. Use that as the
                # base; if no original_price exists the item had no prior promo.
                base_unit = Decimal(item.get('original_price') or item['price'])
                already_discounted = item.get('original_price') is not None
                
                logger.info(f"   📦 Item: cart_key={cart_key}, pid={pid}, vid={vid}, qty={item['quantity']}")
                
                if vid and promo.applies_to_variant(int(vid)):
                    logger.info(f"      ✓ Variant {vid} matches promotion")
                    # For bulk promos, evaluate all items; for individual promos, skip already-discounted
                    if already_discounted and promo.min_quantity == 1:
                        logger.info(f"      ⏭️ Skipping already-discounted for min_qty=1 promo")
                        continue
                    item_price = base_unit * item['quantity']
                    discount = promo.calculate_discount(item_price)
                    promo_discount += discount
                    logger.info(f"      💰 Added discount: {discount}")
                elif not vid and promo.applies_to_product(int(pid)):
                    logger.info(f"      ✓ Product {pid} matches promotion")
                    # For bulk promos, evaluate all items; for individual promos, skip already-discounted
                    if already_discounted and promo.min_quantity == 1:
                        logger.info(f"      ⏭️ Skipping already-discounted for min_qty=1 promo")
                        continue
                    item_price = base_unit * item['quantity']
                    discount = promo.calculate_discount(item_price)
                    promo_discount += discount
                    logger.info(f"      💰 Added discount: {discount}")
                else:
                    logger.info(f"      ❌ No match - applies_to_variant={promo.applies_to_variant(int(vid)) if vid else 'N/A'}, applies_to_product={promo.applies_to_product(int(pid)) if not vid else 'N/A'}")

            logger.info(f"   💵 Total promo discount: {promo_discount}")
            if promo_discount > best_discount:
                best_discount = promo_discount
                best_promo = promo
                logger.info(f"   🏆 New best promotion!")
        
        logger.info(f"🔍 Final: best_promo={best_promo}, best_discount={best_discount}")

        discount_amount = min(best_discount, subtotal)
        total = subtotal - discount_amount

        # ── Create Order ───────────────────────────────────────────────
        order = Order.objects.create(
            customer_name=name,
            customer_phone=phone,
            customer_address=address,
            notes=notes,
            total_amount=total,
            discount_amount=discount_amount,
            promotion=best_promo,
            status='pending'
        )

        # ── Create OrderItems ──────────────────────────────────────────
        for cart_key, item in cart.items():
            pid = item.get('product_id', cart_key.split('_')[0])
            vid = item.get('variant_id')
            try:
                product = Product.objects.get(id=pid)
            except Product.DoesNotExist:
                continue
            variant = None
            if vid:
                try:
                    variant = ProductVariant.objects.get(id=vid)
                except ProductVariant.DoesNotExist:
                    pass
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=item['quantity'],
                price=Decimal(item['price'])
            )

            # ── Deduct stock ───────────────────────────────────────────
            qty = item['quantity']
            if variant:
                if variant.stock is not None:
                    # Variant has its own stock — deduct from variant
                    variant.stock = max(0, variant.stock - qty)
                    variant.save(update_fields=['stock'])
                elif product.stock is not None:
                    # Variant stock not set — deduct from parent product (shared pool)
                    product.stock = max(0, product.stock - qty)
                    product.save(update_fields=['stock'])
            else:
                if product.stock is not None:
                    product.stock = max(0, product.stock - qty)
                    product.save(update_fields=['stock'])

        # ── Build WhatsApp message ──────────────────────────────────────
        message = "*NEW ORDER - ThePopShopKe*\n"
        message += f"Order #: {order.order_number}\n\n"
        message += "*ORDER ITEMS*\n"

        item_count = 0
        item_number = 1
        for item in cart.values():
            item_price = float(item['price'])
            item_subtotal = item_price * item['quantity']
            item_count += item['quantity']
            orig = item.get('original_price')
            
            # Item name
            message += f"{item_number}. {item['name']}\n"
            
            # Show original price if on sale
            if orig and float(orig) > item_price:
                message += f"   Original Price: Ksh {float(orig):,.2f}\n"
                message += f"   Discounted Price: Ksh {item_price:,.2f}\n"
            else:
                message += f"   Price: Ksh {item_price:,.2f}\n"
            
            # Quantity and subtotal
            message += f"   Qty: {item['quantity']} x Ksh {item_price:,.2f}\n"
            message += f"   Subtotal: Ksh {item_subtotal:,.2f}\n\n"
            item_number += 1

        message += "*ORDER SUMMARY*\n"
        message += f"Total Items: {item_count}\n"
        if discount_amount > 0:
            message += f"Subtotal: Ksh {float(subtotal):,.2f}\n"
            message += f"Discount: -Ksh {float(discount_amount):,.2f}\n"
        message += f"Total Amount: Ksh {float(total):,.2f}\n\n"
        message += "*CUSTOMER DETAILS*\n"
        message += f"Name: {name}\n"
        message += f"Phone: {phone}\n"
        message += f"Address: {address}\n"
        if notes:
            message += f"\n*SPECIAL NOTES*\n{notes}"
            message += f"\n--------------------------------------\n"
        message += "\nUpon Order Placed, We'll send you Payment Details and Delivery Fees.\n\n"
        message += "Thank you for shopping with ThePopShopKe!"

        encoded_message = quote(message)
        whatsapp_url = f"https://wa.me/254700840182?text={encoded_message}"

        request.session['cart'] = {}

        return JsonResponse({
            'success': True,
            'whatsapp_url': whatsapp_url,
            'order_number': order.order_number,
            'discount_amount': str(discount_amount),
            'total': str(total),
        })

    return JsonResponse({'success': False})


def search_products(request):
    """AJAX search endpoint — returns matching products as JSON."""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': [], 'query': query})

    products = (
        Product.objects
        .filter(is_available=True)
        .filter(
            Q(name__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
        .select_related('category')
        .prefetch_related('variants')
        .distinct()[:12]
    )

    results = []
    for p in products:
        sale_price = p.sale_price
        results.append({
            'id': p.id,
            'name': p.name,
            'short_description': p.short_description,
            'price': str(p.price),
            'category': p.category.name,
            'image': p.get_image_url() or '',
            'variants': json.loads(p.variants_json),
            'sale_info': {
                'sale_price': str(sale_price),
                'original_price': str(p.price),
                'discount_percent': p.discount_percent,
            } if sale_price is not None else None,
        })

    return JsonResponse({'results': results, 'query': query})


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
