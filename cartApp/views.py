from datetime import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core import serializers
from functools import wraps

from merchandiseApp.models import Merchandise
from .models import Cart, CartItem, Purchase

from django.conf import settings
import csv, os, uuid, json
from django.db.models import F
import requests

SHIPPING_FEE = getattr(settings, 'SHIPPING_FEE', 10000)
SERVICE_FEE = getattr(settings, 'SERVICE_FEE', 3000)

@login_required
def _get_cart_for_request(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

def _is_json_request(request):
    return (request.headers.get('Accept') == 'application/json' or
            request.headers.get('Content-Type') == 'application/json' or
            request.GET.get('format') == 'json')

def _get_request_data(request):
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body)
        except:
            return {}
    return request.POST

@csrf_exempt
@login_required
def cart_page(request):
    cart = _get_cart_for_request(request)
    cart_items = cart.items.select_related('product').all()
    request.session.pop('buy_now', None)
    request.session.pop('last_order_token', None)
    request.session.pop('last_order_summary', None)
    total_price = sum(item.line_total() for item in cart_items if item.selected)

    if _is_json_request(request):
        items_data = []
        for item in cart_items:
            # PERBAIKAN: Format response agar sesuai dengan CartItem model Flutter
            items_data.append({
                'model': 'cartApp.cartitem',
                'pk': item.id,
                'fields': {
                    'cart': item.cart.id,
                    'product': str(item.product.id) if item.product else None,
                    'product_name': item.product_name or (item.product.name if item.product else 'Unknown Product'),
                    'product_price': item.product_price or (item.product.price if item.product else 0),
                    'product_thumbnail': item.product_thumbnail or (getattr(item.product, 'thumbnail', '') if item.product else ''),
                    'product_stock': item.product_stock or (getattr(item.product, 'stock', 0) if item.product else 0),
                    'quantity': item.quantity,
                    'selected': item.selected,
                }
            })
        return JsonResponse({
            'items': items_data,
            'cart_subtotal': cart.subtotal(),
            'total_items': cart.total_items(),
            'selected_count': cart_items.filter(selected=True).count(),
            'total_price': total_price
        })

    context = {'cart': cart, 'cart_items': cart_items, 'cart_count': cart_items.count(),
               'total_price': total_price, 'selected_count': cart_items.filter(selected=True).count()}
    return render(request, 'cart.html', context)

@csrf_exempt
@login_required
def cart_item_detail(request, item_id):
    try:
        cart = _get_cart_for_request(request)
        item = cart.items.get(pk=item_id)
        if item.product:
            product_data = {'id': str(item.product.id), 'name': item.product.name, 'price': item.product.price,
                            'thumbnail': getattr(item.product, 'thumbnail', ''), 'stock': getattr(item.product, 'stock', 0)}
        else:
            product_data = {'id': None, 'name': item.product_name, 'price': item.product_price,
                            'thumbnail': item.product_thumbnail or '', 'stock': item.product_stock or 0}
        return JsonResponse({'id': item.id, 'product': product_data, 'quantity': item.quantity, 
                             'selected': item.selected, 'line_total': item.line_total()})
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)

@csrf_exempt
@login_required
def add_to_cart_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = _get_request_data(request)
    product_id_raw = data.get('product_id')
    qty = int(data.get('quantity', 1))
    if not product_id_raw:
        return JsonResponse({'error': 'product_id required'}, status=400)
    cart = _get_cart_for_request(request)

    try:
        uuid.UUID(product_id_raw)
        product = Merchandise.objects.get(pk=product_id_raw)
        item_qs = cart.items.filter(product=product)
        
        if item_qs.exists():
            item = item_qs.first()
            # Update existing item
            item.quantity = F('quantity') + qty
            # TAMBAHAN: Update denormalized fields juga
            item.product_name = product.name
            item.product_price = product.price
            item.product_thumbnail = getattr(product, 'thumbnail', '')
            item.product_stock = getattr(product, 'stock', 0)
            item.save()
            item.refresh_from_db()
        else:
            # Create new item dengan semua field
            item = CartItem.objects.create(
                cart=cart, 
                product=product,
                product_name=product.name,
                product_price=product.price,
                product_thumbnail=getattr(product, 'thumbnail', ''),
                product_stock=getattr(product, 'stock', 0),
                quantity=qty, 
                selected=False
            )
        
        return JsonResponse({
            'success': True, 
            'message': 'Added to cart', 
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
        return JsonResponse({'error': 'Invalid product_id'}, status=400)

    csv_path = os.path.join(settings.BASE_DIR, 'merchandise.csv')
    if not os.path.exists(csv_path):
        return JsonResponse({'error': 'CSV not found'}, status=500)
    with open(csv_path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if idx < 0 or idx >= len(rows):
        return JsonResponse({'error': 'Product not found'}, status=404)

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

    item_qs = cart.items.filter(product_name=name)
    if item_qs.exists():
        item = item_qs.first()
        item.quantity = F('quantity') + qty
        item.save()
        item.refresh_from_db()
    else:
        item = CartItem.objects.create(
            cart=cart, 
            product=None, 
            product_name=name, 
            product_price=price,
            product_thumbnail=thumbnail, 
            product_stock=stock, 
            quantity=qty, 
            selected=False
        )
    
    return JsonResponse({
        'success': True, 
        'message': 'Added to cart', 
        'item_id': item.id,
        'cart_subtotal': cart.subtotal(), 
        'total_items': cart.total_items()
    })

@csrf_exempt
@login_required
def update_cart_item_ajax(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = _get_request_data(request)
    action = data.get('action')
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
                    return JsonResponse({'success': True, 'message': 'Deleted', 'quantity': 0,
                                         'cart_subtotal': cart.subtotal(), 'total_items': cart.total_items()})
                CartItem.objects.filter(pk=item.pk).update(quantity=F('quantity') - 1)
                item.refresh_from_db()
            elif action == 'set':
                try:
                    q = int(data.get('quantity', 1))
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Invalid quantity'}, status=400)
                if q <= 0:
                    item.delete()
                    return JsonResponse({'success': True, 'message': 'Deleted', 'quantity': 0,
                                         'cart_subtotal': cart.subtotal(), 'total_items': cart.total_items()})
                stock = get_item_stock(item)
                if q > stock:
                    return JsonResponse({'error': 'Not enough stock'}, status=400)
                item.quantity = q
                item.save()
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'success': True, 'message': 'Updated', 'quantity': item.quantity, 
                         'line_total': item.line_total(), 'cart_subtotal': cart.subtotal(), 'total_items': cart.total_items()})

@csrf_exempt
@login_required
def toggle_select_ajax(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    cart = _get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.selected = not item.selected
    item.save()
    return JsonResponse({'success': True, 'message': 'Toggled', 'selected': item.selected, 'cart_subtotal': cart.subtotal()})

@csrf_exempt
@login_required
def toggle_select_all(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = _get_request_data(request)
    selected = data.get('selected') == 'true' or data.get('selected') == True
    cart = _get_cart_for_request(request)
    CartItem.objects.filter(cart=cart).update(selected=selected)
    return JsonResponse({'success': True, 'message': 'All items toggled', 'selected': selected})

@csrf_exempt
@login_required
def delete_item_ajax(request, item_id):
    if request.method not in ('POST', 'DELETE'):
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    cart = _get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    return JsonResponse({'success': True, 'message': 'Deleted', 'cart_subtotal': cart.subtotal(), 'total_items': cart.total_items()})

@csrf_exempt
@login_required
def checkout_view(request):
    cart = _get_cart_for_request(request)
    buy_now = request.session.get('buy_now', False)
    last_token = request.session.get('last_order_token')
    last_summary = request.session.get('last_order_summary', {})

    if buy_now and last_token and request.method == 'GET':
        purchases = Purchase.objects.filter(order_token=last_token, user=request.user)
        if purchases.exists():
            class _TempItem:
                def __init__(self, purchase):
                    self._purchase = purchase
                    self.product = purchase.product
                    thumb = ''
                    if self.product and hasattr(self.product, 'thumbnail'):
                        thumb = getattr(self.product, 'thumbnail') or ''
                    else:
                        thumb = getattr(purchase, 'product_thumbnail', '') or ''
                    self.product_thumbnail = thumb
                    self.product_name = purchase.product_name or (getattr(self.product, 'name', '') or '')
                    self.product_price = purchase.product_price or (getattr(self.product, 'price', 0) or 0)
                    self.quantity = purchase.quantity or 1
                def line_total(self):
                    return (self.product_price or 0) * (self.quantity or 0)
            items = [_TempItem(p) for p in purchases]
            total_before_fee = sum(i.line_total() for i in items)
            context = {'cart': cart, 'items': items, 'shipping_fee': SHIPPING_FEE, 'service_fee': SERVICE_FEE,
                       'total_before_fee': total_before_fee, 'user': request.user, 'is_buy_now': True}
            return render(request, 'checkout.html', context)

    if request.method == 'GET':
        request.session.pop('buy_now', None)
        request.session.pop('last_order_token', None)
        request.session.pop('last_order_summary', None)
        selected_items = cart.items.filter(selected=True)
        context = {'cart': cart, 'items': selected_items, 'shipping_fee': SHIPPING_FEE, 'service_fee': SERVICE_FEE,
                   'total_before_fee': sum((i.line_total()) for i in selected_items), 'user': request.user}
        return render(request, 'checkout.html', context)

    # POST request - Process checkout
    if buy_now and last_token:
        purchases = Purchase.objects.filter(order_token=last_token, user=request.user)
        if not purchases.exists():
            return JsonResponse({'success': False, 'error': 'No purchase found'}, status=400)
        
        request.session['just_ordered'] = True
        request.session['last_order_token'] = str(last_token)
        request.session.pop('buy_now', None)
        
        # Calculate totals for buy now
        total_before_fee = sum(p.product_price * p.quantity for p in purchases)
        grand_total = total_before_fee + SHIPPING_FEE + SERVICE_FEE
        
        if _is_json_request(request):
            return JsonResponse({
                'success': True, 
                'message': 'Checkout successful', 
                'order_token': str(last_token),
                'total': total_before_fee,
                'shipping_fee': SHIPPING_FEE,
                'service_fee': SERVICE_FEE,
                'grand_total': grand_total
            })
        return JsonResponse({'message': 'Checkout successful', 'redirect_url': reverse('cartApp:loading')})

    data = _get_request_data(request)
    request.session.pop('buy_now', None)
    request.session.pop('last_order_token', None)
    request.session.pop('last_order_summary', None)
    
    selected_items = cart.items.filter(selected=True)
    address = data.get('address', '').strip()
    payment_method = data.get('payment_method', '').strip()
    
    # PENTING: Validasi SEBELUM transaction
    if not address:
        return JsonResponse({'success': False, 'error': 'Address is required'}, status=400)
    
    if not payment_method:
        return JsonResponse({'success': False, 'error': 'Payment method is required'}, status=400)
    
    if not selected_items.exists():
        return JsonResponse({'success': False, 'error': 'No items selected for checkout'}, status=400)

    try:
        with transaction.atomic():
            product_items = [it for it in selected_items if it.product]
            product_ids = [it.product.id for it in product_items]
            products = Merchandise.objects.select_for_update().filter(id__in=product_ids)
            prod_map = {p.id: p for p in products}
            
            # Validate stock for all items
            for item in product_items:
                p = prod_map.get(item.product.id)
                if p is None:
                    raise ValueError(f"Product {item.product_name} not found")
                current_stock = getattr(p, 'stock', 0)
                if item.quantity > current_stock:
                    raise ValueError(f'Not enough stock for {p.name}. Available: {current_stock}, Requested: {item.quantity}')
            
            # Update stock
            for item in product_items:
                p = prod_map[item.product.id]
                p.stock = (p.stock or 0) - item.quantity
                if hasattr(p, 'sold'):
                    p.sold = (p.sold or 0) + item.quantity
                p.save()
            
            order_token = uuid.uuid4()
            purchased_ids = []
            purchased_summary_total = 0
            purchased_items = []
            
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
                    quantity=it.quantity
                )
                
                purchased_summary_total += (price * it.quantity)
                purchased_items.append({
                    'product_name': name, 
                    'quantity': it.quantity, 
                    'price': price, 
                    'line_total': price * it.quantity
                })
                it.delete()
            
            request.session['just_ordered'] = True
            request.session['last_order_token'] = str(order_token)
            request.session['last_order_products'] = purchased_ids
            request.session['last_order_summary'] = {'total': int(purchased_summary_total), 'count': len(purchased_ids)}
    
    except ValueError as e:
        # Validation error - transaction will rollback
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        # Other errors - transaction will rollback
        return JsonResponse({'success': False, 'error': f'Checkout failed: {str(e)}'}, status=500)

    # Calculate grand total
    grand_total = purchased_summary_total + SHIPPING_FEE + SERVICE_FEE

    if _is_json_request(request):
        return JsonResponse({
            'success': True, 
            'message': 'Checkout successful', 
            'order_token': str(order_token),
            'items': purchased_items,
            'total': int(purchased_summary_total),
            'shipping_fee': SHIPPING_FEE, 
            'service_fee': SERVICE_FEE,
            'grand_total': int(grand_total)
        }, status=201)
    
    return JsonResponse({'message': 'Checkout successful', 'redirect_url': reverse('cartApp:loading')})

@csrf_exempt
@login_required
def buy_now_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = _get_request_data(request)
    request.session.pop('buy_now', None)
    request.session.pop('last_order_token', None)
    request.session.pop('last_order_summary', None)
    request.session.pop('last_order_products', None)
    product_id_raw = data.get('product_id')
    qty_raw = data.get('quantity', '1')
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
        with transaction.atomic():
            product = Merchandise.objects.select_for_update().get(pk=product_id_raw)
            if qty > getattr(product, 'stock', 0):
                return JsonResponse({'error': 'Not enough stock'}, status=400)
            product.stock -= qty
            if hasattr(product, 'sold'):
                product.sold = (product.sold or 0) + qty
            product.save()
            order_token = uuid.uuid4()
            Purchase.objects.create(order_token=order_token, user=request.user, product=product,
                                    product_name=product.name, product_price=product.price, quantity=qty)
            request.session['just_ordered'] = True
            request.session['last_order_token'] = str(order_token)
            request.session['last_order_products'] = [str(product.id)]
            request.session['last_order_summary'] = {'total': int(product.price * qty), 'count': 1}
            request.session['buy_now'] = True
        if _is_json_request(request):
            return JsonResponse({'success': True, 'message': 'Buy now successful', 'order_token': str(order_token),
                                 'product_name': product.name, 'quantity': qty, 'total': int(product.price * qty)}, status=201)
        return JsonResponse({'message': 'Buy now successful', 'redirect_url': reverse('cartApp:checkout')})
    except (ValueError, Merchandise.DoesNotExist):
        pass

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
    Purchase.objects.create(order_token=order_token, user=request.user, product=None,
                            product_name=row.get('name') or '', product_price=price, quantity=qty)
    request.session['just_ordered'] = True
    request.session['last_order_token'] = str(order_token)
    request.session['last_order_products'] = [f"csv:{row.get('name')}"]
    request.session['last_order_summary'] = {'total': int(price * qty), 'count': 1}
    request.session['buy_now'] = True
    if _is_json_request(request):
        return JsonResponse({'success': True, 'message': 'Buy now successful', 'order_token': str(order_token),
                             'product_name': row.get('name') or '', 'quantity': qty, 'total': int(price * qty)}, status=201)
    return JsonResponse({'message': 'Buy now successful', 'redirect_url': reverse('cartApp:checkout')})

@login_required
def after_checkout(request):
    just_ordered = request.session.pop('just_ordered', False)
    last_order_token = request.session.pop('last_order_token', None)
    last_order_summary = request.session.pop('last_order_summary', None)
    last_order_products = request.session.pop('last_order_products', None)
    if _is_json_request(request):
        return JsonResponse({'just_ordered': just_ordered, 'last_order_token': last_order_token,
                             'last_order_summary': last_order_summary, 'last_order_products': last_order_products})
    context = {'just_ordered': just_ordered, 'last_order_token': last_order_token,
               'last_order_summary': last_order_summary, 'last_order_products': last_order_products}
    return render(request, 'after_checkout.html', context)

@login_required
def loading_view(request):
    redirect_url = reverse('cartApp:after_checkout')
    wait_ms = 1400
    last_order_summary = request.session.get('last_order_summary')
    context = {'redirect_url': redirect_url, 'wait_ms': wait_ms, 'last_order_summary': last_order_summary}
    return render(request, 'loading.html', context)

@login_required
def show_json(request):
    cart = _get_cart_for_request(request)
    cart_items = cart.items.select_related('product').all()
    return HttpResponse(serializers.serialize("json", cart_items), content_type="application/json")

@login_required
def show_json_by_id(request, item_id):
    try:
        cart = _get_cart_for_request(request)
        item = cart.items.get(pk=item_id)
        return HttpResponse(serializers.serialize("json", [item]), content_type="application/json")
    except CartItem.DoesNotExist:
        return HttpResponse(status=404)

@login_required
def show_checkout_json(request):
    cart = _get_cart_for_request(request)
    buy_now = request.session.get('buy_now', False)
    last_token = request.session.get('last_order_token')
    
    # Handle buy now case
    if buy_now and last_token:
        purchases = Purchase.objects.filter(order_token=last_token, user=request.user)
        
        if not purchases.exists():
            return JsonResponse({
                'success': False,
                'error': 'No purchase found',
                'items': [],
                'total_before_fee': 0,
                'shipping_fee': SHIPPING_FEE,
                'service_fee': SERVICE_FEE,
                'grand_total': SHIPPING_FEE + SERVICE_FEE,
                'is_buy_now': True
            })
        
        items_data = []
        total_before_fee = 0
        
        for purchase in purchases:
            product_name = purchase.product_name or (purchase.product.name if purchase.product else 'Unknown')
            product_price = purchase.product_price or (purchase.product.price if purchase.product else 0)
            product_thumbnail = ''
            product_stock = 0
            
            if purchase.product:
                product_thumbnail = getattr(purchase.product, 'thumbnail', '')
                product_stock = getattr(purchase.product, 'stock', 0)
            
            line_total = product_price * purchase.quantity
            total_before_fee += line_total
            
            items_data.append({
                'id': purchase.id,
                'product_id': str(purchase.product.id) if purchase.product else None,
                'product_name': product_name,
                'product_price': product_price,
                'product_thumbnail': product_thumbnail,
                'product_stock': product_stock,
                'quantity': purchase.quantity,
                'line_total': line_total
            })
        
        grand_total = total_before_fee + SHIPPING_FEE + SERVICE_FEE
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'total_before_fee': total_before_fee,
            'shipping_fee': SHIPPING_FEE,
            'service_fee': SERVICE_FEE,
            'grand_total': grand_total,
            'is_buy_now': True
        })
    
    # Normal checkout from cart
    selected_items = cart.items.filter(selected=True).select_related('product')
    
    if not selected_items.exists():
        return JsonResponse({
            'success': False,
            'error': 'No items selected for checkout',
            'items': [],
            'total_before_fee': 0,
            'shipping_fee': SHIPPING_FEE,
            'service_fee': SERVICE_FEE,
            'grand_total': SHIPPING_FEE + SERVICE_FEE,
            'is_buy_now': False
        })
    
    items_data = []
    total_before_fee = 0
    
    for item in selected_items:
        product_name = item.product_name or (item.product.name if item.product else 'Unknown')
        product_price = item.product_price or (item.product.price if item.product else 0)
        product_thumbnail = item.product_thumbnail or (getattr(item.product, 'thumbnail', '') if item.product else '')
        product_stock = item.product_stock or (getattr(item.product, 'stock', 0) if item.product else 0)
        
        line_total = product_price * item.quantity
        total_before_fee += line_total
        
        items_data.append({
            'id': item.id,
            'product_id': str(item.product.id) if item.product else None,
            'product_name': product_name,
            'product_price': product_price,
            'product_thumbnail': product_thumbnail,
            'product_stock': product_stock,
            'quantity': item.quantity,
            'line_total': line_total
        })
    
    grand_total = total_before_fee + SHIPPING_FEE + SERVICE_FEE
    
    return JsonResponse({
        'success': True,
        'items': items_data,
        'total_before_fee': total_before_fee,
        'shipping_fee': SHIPPING_FEE,
        'service_fee': SERVICE_FEE,
        'grand_total': grand_total,
        'is_buy_now': False
    })

@csrf_exempt
@login_required
def toggle_select_item_ajax(request, item_id):
    return toggle_select_ajax(request, item_id)

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)