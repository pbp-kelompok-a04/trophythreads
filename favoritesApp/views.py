# favoritesApp/views.py
from uuid import UUID
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Favorite
from django.apps import apps


# ambil model Merchandise secara aman dari app yang benar
MerchandiseModel = lambda: apps.get_model('merchandiseApp', 'Merchandise')


@login_required
def favorites_list(request):
    """
    Render halaman daftar favorites untuk user yang login.
    Template: 'favoritesApp/favorites_list.html' (atau 'favorites_list.html' tergantung path)
    """
    # gunakan select_related ke field yg benar: 'merchandise'
    favorites = Favorite.objects.filter(user=request.user).select_related('merchandise')
    return render(request, 'favorites_list.html', {'favorites': favorites})


@require_POST
def add_favorite(request):
    """
    AJAX-friendly: returns JSON in all cases.
    - 200 OK: added/exists
    - 400 Bad Request: missing/invalid id
    - 401 Unauthorized: not authenticated
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'auth_required'}, status=401)

    merch_id = request.POST.get('merchandise_id') or request.POST.get('product_id')
    if not merch_id:
        return JsonResponse({'status': 'error', 'message': 'merchandise_id required'}, status=400)

    Merchandise = MerchandiseModel()
    try:
        merchandise = get_object_or_404(Merchandise, pk=merch_id)
    except Exception:
        return JsonResponse({'status': 'error', 'message': f'Invalid merchandise id: {merch_id}'}, status=400)

    favorite, created = Favorite.objects.get_or_create(user=request.user, merchandise=merchandise)
    action = 'added' if created else 'exists'
    return JsonResponse({'status': 'ok', 'action': action, 'favorite_id': str(favorite.id)}, status=200)


@login_required
@require_POST
def remove_favorite(request):
    """
    Hapus favorite. Accepts POST 'favorite_id' OR 'merchandise_id' (atau 'product_id').
    Returns JSON e.g. {status:ok, action:removed}
    """
    favorite_id = request.POST.get('favorite_id')
    merch_id = request.POST.get('merchandise_id') or request.POST.get('product_id')

    if favorite_id:
        fav = get_object_or_404(Favorite, pk=favorite_id, user=request.user)
        fav.delete()
        return JsonResponse({'status': 'ok', 'action': 'removed'})

    if merch_id:
        # validasi UUID
        try:
            UUID(merch_id)
        except (ValueError, TypeError):
            return HttpResponseBadRequest('invalid merchandise_id (expect UUID)')

        Merchandise = MerchandiseModel()
        merchandise = get_object_or_404(Merchandise, pk=merch_id)
        qs = Favorite.objects.filter(user=request.user, merchandise=merchandise)
        deleted, _ = qs.delete()
        if deleted:
            return JsonResponse({'status': 'ok', 'action': 'removed'})
        else:
            return JsonResponse({'status': 'ok', 'action': 'not_found'})

    return HttpResponseBadRequest('favorite_id or merchandise_id required')


@login_required
def favorites_json(request):
    """
    Return favorites as JSON with complete merchandise data (requires login).
    """
    favorites = Favorite.objects.filter(user=request.user).select_related('merchandise')
    data = []
    
    for fav in favorites:
        merch = fav.merchandise
        
        # Get image URL
        image_url = None
        if hasattr(merch, 'image') and merch.image:
            try:
                image_url = merch.image.url
            except (ValueError, AttributeError):
                image_url = None
        
        # Build merchandise data
        merchandise_data = {
            'merchandise_id': str(merch.pk),
            'name': getattr(merch, 'name', 'Unknown Product'),
            'slug': getattr(merch, 'slug', None),
            'image': image_url,
            'price': str(getattr(merch, 'price', 0)),
            'description': getattr(merch, 'description', ''),
        }
        
        # Add optional fields if they exist
        if hasattr(merch, 'rating'):
            merchandise_data['rating'] = float(getattr(merch, 'rating', 0))
        
        if hasattr(merch, 'total_sold'):
            merchandise_data['total_sold'] = int(getattr(merch, 'total_sold', 0))
        
        if hasattr(merch, 'stock'):
            merchandise_data['stock'] = int(getattr(merch, 'stock', 0))
        
        if hasattr(merch, 'category'):
            merchandise_data['category'] = str(getattr(merch, 'category', ''))
        
        # Build favorite data
        favorite_data = {
            'favorite_id': str(fav.id),
            'merchandise': merchandise_data,
            'created_at': fav.created_at.isoformat() if fav.created_at else None,
        }
        
        data.append(favorite_data)
    
    return JsonResponse({'status': 'ok', 'favorites': data})