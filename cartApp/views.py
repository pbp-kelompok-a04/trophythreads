# cartApp/views.py
from datetime import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from merchandiseApp.models import Merchandise
from .models import Cart, CartItem, Purchase

from django.conf import settings
import csv, os, uuid
from django.db.models import F

SHIPPING_FEE = getattr(settings, 'SHIPPING_FEE', 10000)
SERVICE_FEE = getattr(settings, 'SERVICE_FEE', 3000)

# helper get or create cart for request (user or sesi)
def _get_cart_for_request(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    # guest -> session based
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

@login_required
@require_POST
def add_to_cart_ajax(request):

    product_id_raw = request.POST.get('product_id')
    qty = int(request.POST.get('quantity', 1))

    if not product_id_raw:
        return JsonResponse({'error': 'product_id required'}, status=400)

    cart = _get_cart_for_request(request)

    try:
        uuid.UUID(product_id_raw)
        product = Merchandise.objects.get(pk=product_id_raw)
        item_qs = cart.items.filter(product=product)
        if item_qs.exists():
            item = item_qs.first()
            item.quantity = F('quantity') + qty
            item.save()
        else:
            item = CartItem.objects.create(
                cart=cart, product=product, quantity=qty,
                selected=False,  # <--- agar tidak auto-selected
            )
        return JsonResponse({
            'message': 'Added to cart (DB product)',
            'item_id': item.id,
            'cart_subtotal': cart.subtotal(),
            'total_items': cart.total_items()
        })

    except (ValueError, Merchandise.DoesNotExist):
        pass

    try:
        idx = str(product_id_raw)
        if idx.startswith("csv_"):
            idx = idx.split("csv_")[1]
        idx = int(idx)
    except Exception:
        return JsonResponse({'error'}, status=400)

    csv_path = os.path.join(settings.BASE_DIR, 'merchandise.csv')
    if not os.path.exists(csv_path):
        return JsonResponse({'error'}, status=500)

    with open(csv_path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    if idx < 0 or idx >= len(rows):
        return JsonResponse({'error'}, status=404)

    row = rows[idx]
    name = row.get('name') or 'Unknown'
    try:
        price = int(float(row.get('price') or 0))
    except:
        price = 0
    thumbnail = row.get('thumbnail') or ''
    stock = row.get('stock') or row.get('Stock') or row.get('stok') or 0
    try:
        stock = int(stock)
    except:
        stock = 0

    # Simpan ke CartItem 
    item_qs = cart.items.filter(product_name=name)
    if item_qs.exists():
        item = item_qs.first()
        item.quantity = F('quantity') + qty
        item.save()
    else:
        item = CartItem.objects.create(
            cart=cart,
            product=None,
            product_name=name,
            product_price=price,
            product_thumbnail=thumbnail,
            product_stock=stock,
            quantity=qty,
            selected=False,  # <--- agar tidak auto-selected
        )

    return JsonResponse({
        'message': 'Added to cart',
        'item_id': item.id,
        'cart_subtotal': cart.subtotal(),
        'total_items': cart.total_items()
    })

@login_required
@require_POST
def update_cart_item_ajax(request, item_id):
    action = request.POST.get('action')
    cart = _get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    def get_item_stock(it):
        if it.product:
            return getattr(it.product, 'stock', 0)
        return (it.product_stock or 0)

    try:
        with transaction.atomic():
            if action == 'inc':
                stock = get_item_stock(item)
                if stock < item.quantity + 1:
                    return JsonResponse({'error': 'Not enough stock'}, status=400)
                CartItem.objects.filter(pk=item.pk).update(quantity=F('quantity') + 1)
                item.refresh_from_db()

            elif action == 'dec':
                if item.quantity <= 1:
                    item.delete()
                    return JsonResponse({'message': 'Deleted', 'quantity': 0, 'cart_subtotal': cart.subtotal(), 'total_items': cart.total_items()})
                CartItem.objects.filter(pk=item.pk).update(quantity=F('quantity') - 1)
                item.refresh_from_db()

            elif action == 'set':
                try:
                    q = int(request.POST.get('quantity', 1))
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Invalid quantity'}, status=400)
                if q <= 0:
                    item.delete()
                    return JsonResponse({'message': 'Deleted', 'quantity': 0, 'cart_subtotal': cart.subtotal(), 'total_items': cart.total_items()})
                stock = get_item_stock(item)
                if q > stock:
                    return JsonResponse({'error': 'Not enough stock'}, status=400)
                item.quantity = q
                item.save()
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Updated', 'quantity': item.quantity, 'line_total': item.line_total(), 'cart_subtotal': cart.subtotal(), 'total_items': cart.total_items()})

@login_required
@require_POST
def toggle_select_ajax(request, item_id):
    cart = _get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.selected = not item.selected
    item.save()
    return JsonResponse({'message': 'Toggled', 'selected': item.selected, 'cart_subtotal': cart.subtotal()})

@login_required
@require_POST
def toggle_select_all(request):
    selected = request.POST.get('selected') == 'true'
    cart = _get_cart_for_request(request)
    CartItem.objects.filter(cart=cart).update(selected=selected)
    return JsonResponse({'success': True})

@login_required
@require_POST
def delete_item_ajax(request, item_id):
    cart = _get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    return JsonResponse({'message': 'Deleted', 'cart_subtotal': cart.subtotal()})

@login_required
def cart_page(request):
    cart = _get_cart_for_request(request)
    cart_items = cart.items.select_related('product').all()

    # Clear any leftover buy_now session data when user visits cart
    request.session.pop('buy_now', None)
    request.session.pop('last_order_token', None)
    request.session.pop('last_order_summary', None)

    total_price = 0
    for item in cart_items:
        if item.selected:
            total_price += item.line_total()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_count': cart_items.count(),
        'total_price': total_price,
        'selected_count': cart_items.filter(selected=True).count(),
    }
    return render(request, 'cart.html', context)

@login_required
def checkout_view(request):
    cart = _get_cart_for_request(request)
    # session flags potentially set by buy_now_ajax earlier
    buy_now = request.session.get('buy_now', False)
    last_token = request.session.get('last_order_token')
    last_summary = request.session.get('last_order_summary', {})

    # Handle GET request for buy_now flow
    if buy_now and last_token and request.method == 'GET':
        purchases = Purchase.objects.filter(order_token=last_token, user=request.user)
        if purchases.exists():
            # small wrapper object so template can use same attributes/methods as CartItem
            class _TempItem:
                def __init__(self, purchase):
                    self._purchase = purchase
                    self.product = purchase.product  # may be None
                    thumb = ''
                    if self.product and hasattr(self.product, 'thumbnail'):
                        thumb = getattr(self.product, 'thumbnail') or ''
                    else:
                        # if Purchase had stored thumbnail earlier (unlikely), use it; else empty
                        thumb = getattr(purchase, 'product_thumbnail', '') or ''
                    self.product_thumbnail = thumb

                    # name/price/qty
                    self.product_name = purchase.product_name or (getattr(self.product, 'name', '') or '')
                    self.product_price = purchase.product_price or (getattr(self.product, 'price', 0) or 0)
                    self.quantity = purchase.quantity or 1

                def line_total(self):
                    return (self.product_price or 0) * (self.quantity or 0)

            items = [_TempItem(p) for p in purchases]
            total_before_fee = sum(i.line_total() for i in items)

            context = {
                'cart': cart,
                'items': items,  # now template can use item.product.thumbnail|default:item.product_thumbnail
                'shipping_fee': SHIPPING_FEE,
                'service_fee': SERVICE_FEE,
                'total_before_fee': total_before_fee,
                'user': request.user,
                'is_buy_now': True,
            }
            return render(request, 'checkout.html', context)

    # Handle GET request for cart-based checkout (clear buy_now session if exists)
    if request.method == 'GET':
        # Clear any leftover buy_now session data
        request.session.pop('buy_now', None)
        request.session.pop('last_order_token', None)
        request.session.pop('last_order_summary', None)
        
        selected_items = cart.items.filter(selected=True)
        context = {
            'cart': cart,
            'items': selected_items,
            'shipping_fee': SHIPPING_FEE,
            'service_fee': SERVICE_FEE,
            'total_before_fee': sum((i.line_total()) for i in selected_items),
            'user': request.user,
        }
        return render(request, 'checkout.html', context)

    # Handle POST: buy_now completion
    if buy_now and last_token:
        purchases = Purchase.objects.filter(order_token=last_token, user=request.user)
        if not purchases.exists():
            return JsonResponse({'error': 'No purchase found for Buy Now. Please try again.'}, status=400)
        request.session['just_ordered'] = True
        request.session['last_order_token'] = str(last_token)
        request.session.pop('buy_now', None)

        return JsonResponse({'message': 'Checkout successful', 'redirect_url': reverse('cartApp:loading')})

    # ----- POST: CART-BASED checkout processing -----
    # Clear buy_now session if user is doing cart-based checkout
    request.session.pop('buy_now', None)
    request.session.pop('last_order_token', None)
    request.session.pop('last_order_summary', None)
    
    selected_items = cart.items.filter(selected=True)
    address = request.POST.get('address')
    payment_method = request.POST.get('payment_method')

    if not address:
        return JsonResponse({'error': 'Address required'}, status=400)
    if not selected_items.exists():
        return JsonResponse({'error': 'No items selected'}, status=400)

    try:
        with transaction.atomic():
            # prepare product-backed items for stock locking
            product_items = [it for it in selected_items if it.product]
            product_ids = [it.product.id for it in product_items]

            # lock product rows
            products = Merchandise.objects.select_for_update().filter(id__in=product_ids)
            prod_map = {p.id: p for p in products}

            # Validate stock first
            for item in product_items:
                p = prod_map.get(item.product.id)
                if p is None:
                    raise ValueError("Product not found during checkout")
                if item.quantity > getattr(p, 'stock', 0):
                    return JsonResponse({'error': f'Not enough stock for {p.name}'}, status=400)

            # Deduct stock and update sold
            for item in product_items:
                p = prod_map[item.product.id]
                p.stock = (p.stock or 0) - item.quantity
                if hasattr(p, 'sold'):
                    p.sold = (p.sold or 0) + item.quantity
                p.save()

            # create purchases and remove cart items
            order_token = uuid.uuid4()
            purchased_ids = []
            purchased_summary_total = 0

            # copy list because we will delete items while iterating
            for it in list(selected_items):
                if it.product:
                    purchased_ids.append(str(it.product.id))
                    price = getattr(it.product, 'price', 0) or 0
                    product_obj = it.product
                    name = getattr(product_obj, 'name', '') or ''
                else:
                    purchased_ids.append(f"csv:{it.product_name}")
                    price = it.product_price or 0
                    product_obj = None
                    name = it.product_name or ""

                Purchase.objects.create(
                    order_token=order_token,
                    user=request.user if request.user.is_authenticated else None,
                    product=product_obj,
                    product_name=name,
                    product_price=price,
                    quantity=it.quantity,
                )

                purchased_summary_total += (price * it.quantity)
                # remove item from cart (we assume that's desired behavior)
                it.delete()

            # mark session so after_checkout/loader pages can read it
            request.session['just_ordered'] = True
            request.session['last_order_token'] = str(order_token)
            request.session['last_order_products'] = purchased_ids
            request.session['last_order_summary'] = {
                'total': int(purchased_summary_total),
                'count': len(purchased_ids)
            }

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Checkout successful', 'redirect_url': reverse('cartApp:loading')})

@login_required
def after_checkout(request):
    just_ordered = request.session.pop('just_ordered', False)
    last_order_token = request.session.pop('last_order_token', None)
    last_order_summary = request.session.pop('last_order_summary', None)
    last_order_products = request.session.pop('last_order_products', None)

    context = {
        'just_ordered': just_ordered,
        'last_order_token': last_order_token,
        'last_order_summary': last_order_summary,
        'last_order_products': last_order_products,
    }
    return render(request, 'after_checkout.html', context)

@login_required
def loading_view(request):
    redirect_url = reverse('cartApp:after_checkout')
    # waktu tampil loading (ms) 
    wait_ms = 1400
    last_order_summary = request.session.get('last_order_summary')

    context = {
        'redirect_url': redirect_url,
        'wait_ms': wait_ms,
        'last_order_summary': last_order_summary,
    }
    return render(request, 'loading.html', context)

@login_required
@require_POST
def buy_now_ajax(request):
    request.session.pop('buy_now', None)
    request.session.pop('last_order_token', None)
    request.session.pop('last_order_summary', None)
    request.session.pop('last_order_products', None)
    
    product_id_raw = request.POST.get('product_id')
    qty_raw = request.POST.get('quantity', '1')

    try:
        qty = int(qty_raw)
        if qty <= 0:
            raise ValueError("quantity must be positive")
    except Exception:
        return JsonResponse({'error': 'Invalid quantity'}, status=400)

    if not product_id_raw:
        return JsonResponse({'error': 'product_id required'}, status=400)

    try:
        uuid.UUID(product_id_raw)
        # lock product row for stock safety
        with transaction.atomic():
            product = Merchandise.objects.select_for_update().get(pk=product_id_raw)
            if qty > getattr(product, 'stock', 0):
                return JsonResponse({'error': 'Not enough stock'}, status=400)

            # reduce stock
            product.stock -= qty
            if hasattr(product, 'sold'):
                product.sold = (product.sold or 0) + qty
            product.save()

            # create purchase(s)
            order_token = uuid.uuid4()
            Purchase.objects.create(
                order_token=order_token,
                user=request.user,
                product=product,
                product_name=product.name,
                product_price=product.price,
                quantity=qty,
            )

            # session markers (reuse same pattern as checkout_view)
            request.session['just_ordered'] = True
            request.session['last_order_token'] = str(order_token)
            request.session['last_order_products'] = [str(product.id)]
            request.session['last_order_summary'] = {
                'total': int(product.price * qty),
                'count': 1
            }

        # set flag supaya checkout tahu ini Buy Now (single-product checkout)
        request.session['buy_now'] = True
        # last_order_* sudah kita set sebelumnya (last_order_token, last_order_products, last_order_summary)
        return JsonResponse({'message': 'Buy now successful', 'redirect_url': reverse('cartApp:checkout')})

    except (ValueError, Merchandise.DoesNotExist):
        # not a DB product – maybe csv index
        pass

    # Handle CSV products
    import os
    csv_path = os.path.join(settings.BASE_DIR, 'merchandise.csv')
    try:
        idx = str(product_id_raw)
        if idx.startswith("csv_"):
            idx = idx.split("csv_")[1]
        idx = int(idx)
    except Exception:
        return JsonResponse({'error': 'product not found'}, status=404)

    if not os.path.exists(csv_path):
        return JsonResponse({'error': 'csv not found'}, status=500)

    with open(csv_path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    if idx < 0 or idx >= len(rows):
        return JsonResponse({'error': 'product not found'}, status=404)

    row = rows[idx]
    try:
        price = int(float(row.get('price') or 0))
    except:
        price = 0
    stock = row.get('stock') or row.get('Stock') or row.get('stok') or 0
    try:
        stock = int(stock)
    except:
        stock = 0

    if qty > stock:
        return JsonResponse({'error': 'Not enough stock'}, status=400)
    order_token = uuid.uuid4()
    Purchase.objects.create(
        order_token=order_token,
        user=request.user,
        product=None,
        product_name=row.get('name') or '',
        product_price=price,
        quantity=qty,
    )
    request.session['just_ordered'] = True
    request.session['last_order_token'] = str(order_token)
    request.session['last_order_products'] = [f"csv:{row.get('name')}"]
    request.session['last_order_summary'] = {
        'total': int(price * qty),
        'count': 1
    }

    # set flag supaya checkout tahu ini Buy Now (single-product checkout)
    request.session['buy_now'] = True
    # last_order_* sudah kita set sebelumnya (last_order_token, last_order_products, last_order_summary)
    return JsonResponse({'message': 'Buy now successful', 'redirect_url': reverse('cartApp:checkout')})