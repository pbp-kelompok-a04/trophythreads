from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.apps import apps

from .models import Favorite


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'favoritesApp/favorites_list.html', {'favorites': favorites})


@login_required
@require_POST
def add_favorite(request):
    product_id = request.POST.get('product_id')
    if not product_id:
        return HttpResponseBadRequest('product_id required')

    Product = apps.get_model('merchandise', 'Product')
    product = get_object_or_404(Product, pk=product_id)

    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    action = 'added' if created else 'exists'
    return JsonResponse({'status': 'ok', 'action': action, 'favorite_id': favorite.id})


@login_required
@require_POST
def remove_favorite(request):
    favorite_id = request.POST.get('favorite_id')
    product_id = request.POST.get('product_id')

    if favorite_id:
        fav = get_object_or_404(Favorite, pk=favorite_id, user=request.user)
        fav.delete()
        return JsonResponse({'status': 'ok', 'action': 'removed'})

    if product_id:
        Product = apps.get_model('merchandise', 'Product')
        product = get_object_or_404(Product, pk=product_id)
        qs = Favorite.objects.filter(user=request.user, product=product)
        deleted, _ = qs.delete()
        if deleted:
            return JsonResponse({'status': 'ok', 'action': 'removed'})
        else:
            return JsonResponse({'status': 'ok', 'action': 'not_found'})

    return HttpResponseBadRequest('favorite_id or product_id required')


@login_required
def favorites_json(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    data = []
    for fav in favorites:
        prod = fav.product
        data.append({
            'favorite_id': fav.id,
            'product_id': prod.pk,
            'product_name': getattr(prod, 'name', str(prod)),
            'product_slug': getattr(prod, 'slug', None),
            'created_at': fav.created_at.isoformat(),
        })
    return JsonResponse({'status': 'ok', 'favorites': data})
