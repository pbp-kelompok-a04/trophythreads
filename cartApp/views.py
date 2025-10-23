# cartApp/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from merchandiseApp.models import Merchandise
from .models import Cart, CartItem

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
def cart_json(request):
    cart = _get_cart_for_request(request)
    items = []
    for item in cart.items.select_related('product'):
        items.append({
            'id': item.id,
            'product_id': str(item.product.id),
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity,
            'selected': item.selected,
            'thumbnail': getattr(item.product, 'thumbnail', None),
            'line_total': item.line_total(),
            'stock': item.product.stock,
        })
    return JsonResponse({
        'items': items,
        'subtotal': cart.subtotal(),
        'shipping': SHIPPING_FEE,
        'service_fee': SERVICE_FEE,
        'total': cart.subtotal() + SHIPPING_FEE + SERVICE_FEE
    })

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
    selected_items = cart.items.filter(selected=True)

    if request.method == 'GET':
        context = {
            'cart': cart,
            'items': selected_items,
            'shipping_fee': SHIPPING_FEE,
            'service_fee': SERVICE_FEE,
            'total_before_fee': sum(i.line_total() for i in selected_items),
            'user': request.user,
        }
        return render(request, 'checkout.html', context)
    
    address = request.POST.get('address')

    payment_method = request.POST.get('payment_method')

    if not address:
        return JsonResponse({'error': 'Address required'}, status=400)
    if not selected_items.exists():
        return JsonResponse({'error': 'No items selected'}, status=400)

    last_time_iso = request.session.get('last_order_time')
    if last_time_iso:
        try:
            from django.utils import timezone
            last_time = timezone.datetime.fromisoformat(last_time_iso)
            if timezone.now() - last_time < timezone.timedelta(seconds=10):
                return JsonResponse({'error': 'Checkout baru saja dilakukan. Mohon tunggu.'}, status=400)
        except Exception:
            pass

    try:
        with transaction.atomic():
            product_items = [it for it in selected_items if it.product]
            product_ids = [it.product.id for it in product_items]

            products = Merchandise.objects.select_for_update().filter(id__in=product_ids)
            prod_map = {p.id: p for p in products}

            for item in product_items:
                p = prod_map.get(item.product.id)
                if p is None:
                    raise ValueError("Product not found during checkout")
                if item.quantity > p.stock:
                    return JsonResponse({'error': f'Not enough stock for {p.name}'}, status=400)
                
            for item in product_items:
                p = prod_map[item.product.id]
                p.stock -= item.quantity
                if hasattr(p, 'sold'):
                    p.sold = (p.sold or 0) + item.quantity
                p.save()

            purchased_ids = []
            purchased_summary_total = 0
            for it in list(selected_items):
                if it.product:
                    purchased_ids.append(str(it.product.id))
                    price = getattr(it.product, 'price', 0)
                else:
                    purchased_ids.append(f"csv:{it.product_name}")
                    price = it.product_price or 0
                purchased_summary_total += (price * it.quantity)
                it.delete()

            import uuid
            from django.utils import timezone
            request.session['just_ordered'] = True
            request.session['last_order_token'] = str(uuid.uuid4())
            request.session['last_order_products'] = purchased_ids
            request.session['last_order_summary'] = {
                'total': int(purchased_summary_total),
                'count': len(purchased_ids)
            }
            request.session['last_order_time'] = timezone.now().isoformat()

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Checkout successful', 'redirect_url': reverse('cartApp:after_checkout')})

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