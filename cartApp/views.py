# cartApp/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from merchandiseApp.models import Merchandise
from .models import Cart, CartItem

from django.conf import settings

SHIPPING_FEE = getattr(settings, 'SHIPPING_FEE', 10000)
SERVICE_FEE = getattr(settings, 'SERVICE_FEE', 3000)

# Helper: get or create cart for request (user or session)
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
            'variant': item.variant,
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

@require_POST
def add_to_cart_ajax(request):
    """
    Expects: product_id, quantity (optional), variant (optional)
    """
    product_id = request.POST.get('product_id')
    qty = int(request.POST.get('quantity', 1))
    variant = request.POST.get('variant')

    if not product_id:
        return JsonResponse({'error': 'product_id required'}, status=400)

    try:
        product = Merchandise.objects.get(pk=product_id)
    except Merchandise.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    if product.stock <= 0:
        return JsonResponse({'error': 'Product out of stock'}, status=400)

    cart = _get_cart_for_request(request)

    # If item with same product+variant exists, increment quantity
    item_qs = cart.items.filter(product=product, variant=variant)
    if item_qs.exists():
        item = item_qs.first()
        item.quantity += qty
        item.save()
    else:
        item = CartItem.objects.create(cart=cart, product=product, quantity=qty, variant=variant or '')

    return JsonResponse({'message': 'Added to cart', 'item_id': item.id, 'cart_subtotal': cart.subtotal()})

@require_POST
def update_cart_item_ajax(request, item_id):
    """
    Request data: action = 'inc'|'dec'|'set', quantity (if set)
    """
    action = request.POST.get('action')
    cart = _get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    if action == 'inc':
        if item.quantity + 1 > item.product.stock:
            return JsonResponse({'error': 'Not enough stock'}, status=400)
        item.quantity += 1
        item.save()
    elif action == 'dec':
        if item.quantity <= 1:
            # front-end should call delete with confirm; but return a signal
            return JsonResponse({'confirm_delete': True, 'message': 'Quantity will be 0. Confirm delete?'})
        item.quantity -= 1
        item.save()
    elif action == 'set':
        try:
            q = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid quantity'}, status=400)
        if q <= 0:
            return JsonResponse({'confirm_delete': True})
        if q > item.product.stock:
            return JsonResponse({'error': 'Not enough stock'}, status=400)
        item.quantity = q
        item.save()
    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)

    return JsonResponse({'message': 'Updated', 'quantity': item.quantity, 'line_total': item.line_total(), 'cart_subtotal': cart.subtotal()})

@require_POST
def toggle_select_ajax(request, item_id):
    cart = _get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.selected = not item.selected
    item.save()
    return JsonResponse({'message': 'Toggled', 'selected': item.selected, 'cart_subtotal': cart.subtotal()})

@require_POST
def delete_item_ajax(request, item_id):
    cart = _get_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    return JsonResponse({'message': 'Deleted', 'cart_subtotal': cart.subtotal()})

# cart page (renders template)
def cart_page(request):
    cart = _get_cart_for_request(request)
    context = {
        'cart': cart,
    }
    return render(request, 'cartApp/cart.html', context)

# checkout page (GET show, POST process)
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
        }
        return render(request, 'cartApp/checkout.html', context)

    # POST -> process checkout
    address = request.POST.get('address')
    notes = request.POST.get('notes', '')
    payment_method = request.POST.get('payment_method')

    if not address:
        return JsonResponse({'error': 'Address required'}, status=400)
    if not selected_items.exists():
        return JsonResponse({'error': 'No items selected'}, status=400)

    # Atomic processing: lock product rows and update stock/sold
    try:
        with transaction.atomic():
            # lock all involved merchandise rows
            product_ids = [item.product.id for item in selected_items]
            products = Merchandise.objects.select_for_update().filter(id__in=product_ids)
            prod_map = {p.id: p for p in products}

            # Check stock
            for item in selected_items:
                p = prod_map.get(item.product.id)
                if p is None:
                    raise ValueError("Product not found during checkout")
                if item.quantity > p.stock:
                    return JsonResponse({'error': f'Not enough stock for {p.name}'}, status=400)

            # Deduct stock & increase sold
            for item in selected_items:
                p = prod_map[item.product.id]
                p.stock -= item.quantity
                # add sold field if missing - safe guard (merchandise model should have sold)
                if hasattr(p, 'sold'):
                    p.sold = (p.sold or 0) + item.quantity
                p.save()

            # Here you would create Order and OrderItem records (not implemented)
            # We'll simulate order success and remove selected cart items
            for item in list(selected_items):
                item.delete()

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    # Return redirect to after_checkout page
    return JsonResponse({'message': 'Checkout successful', 'redirect_url': reverse('cartApp:after_checkout')})

def after_checkout(request):
    # Simple confirmation page
    return render(request, 'cartApp/after_checkout.html')
