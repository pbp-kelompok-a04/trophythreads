# favoritesApp/views.py
from uuid import UUID
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Favorite
from django.apps import apps


# Ambil model Merchandise secara aman dari app yang benar
MerchandiseModel = lambda: apps.get_model('merchandiseApp', 'Merchandise')


@login_required
def favorites_list(request):
    """
    Render halaman daftar favorites untuk user yang login.
    
    Returns:
        Rendered HTML page dengan favorites data yang di-load via AJAX
    """
    favorites = Favorite.objects.filter(user=request.user).select_related('merchandise')
    return render(request, 'favorites_list.html', {'favorites': favorites})


@require_POST
def add_favorite(request):
    """
    Tambah merchandise ke favorites user.
    AJAX-friendly endpoint yang returns JSON.
    
    POST Parameters:
        - merchandise_id (required): UUID merchandise yang mau difavorite
        
    Returns:
        - 200: {status: 'ok', action: 'added'|'exists', favorite_id: str}
        - 400: {status: 'error', message: str} - Invalid/missing merchandise_id
        - 401: {status: 'error', message: 'auth_required'} - Not authenticated
    """
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error', 
            'message': 'auth_required'
        }, status=401)

    # Get merchandise_id from request
    merch_id = request.POST.get('merchandise_id') or request.POST.get('product_id')
    if not merch_id:
        return JsonResponse({
            'status': 'error', 
            'message': 'merchandise_id required'
        }, status=400)

    # Get merchandise object
    Merchandise = MerchandiseModel()
    try:
        merchandise = get_object_or_404(Merchandise, pk=merch_id)
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'Invalid merchandise id: {merch_id}'
        }, status=400)

    # Create or get existing favorite
    favorite, created = Favorite.objects.get_or_create(
        user=request.user, 
        merchandise=merchandise
    )
    
    action = 'added' if created else 'exists'
    
    return JsonResponse({
        'status': 'ok', 
        'action': action, 
        'favorite_id': str(favorite.id)
    }, status=200)


@login_required
@require_POST
def remove_favorite(request):
    """
    Hapus merchandise dari favorites user.
    Accepts favorite_id OR merchandise_id.
    
    POST Parameters:
        - favorite_id (optional): UUID favorite yang mau dihapus
        - merchandise_id (optional): UUID merchandise yang mau di-unfavorite
        
    Returns:
        - 200: {status: 'ok', action: 'removed'|'not_found'}
        - 400: Missing parameters or invalid UUID format
    """
    favorite_id = request.POST.get('favorite_id')
    merch_id = request.POST.get('merchandise_id') or request.POST.get('product_id')

    # Option 1: Remove by favorite_id (recommended - more efficient)
    if favorite_id:
        try:
            fav = get_object_or_404(Favorite, pk=favorite_id, user=request.user)
            fav.delete()
            return JsonResponse({
                'status': 'ok', 
                'action': 'removed'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Favorite not found'
            }, status=404)

    # Option 2: Remove by merchandise_id
    if merch_id:
        # Validate UUID format
        try:
            UUID(merch_id)
        except (ValueError, TypeError):
            return HttpResponseBadRequest('invalid merchandise_id (expect UUID)')

        Merchandise = MerchandiseModel()
        try:
            merchandise = get_object_or_404(Merchandise, pk=merch_id)
            qs = Favorite.objects.filter(user=request.user, merchandise=merchandise)
            deleted, _ = qs.delete()
            
            if deleted:
                return JsonResponse({
                    'status': 'ok', 
                    'action': 'removed'
                })
            else:
                return JsonResponse({
                    'status': 'ok', 
                    'action': 'not_found'
                })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Merchandise not found'
            }, status=404)

    # Neither favorite_id nor merchandise_id provided
    return HttpResponseBadRequest('favorite_id or merchandise_id required')


@login_required
def favorites_json(request):
    """
    Return favorites sebagai JSON dengan complete merchandise data.
    Digunakan untuk load favorites via AJAX.
    
    Returns:
        200: {
            status: 'ok',
            favorites: [
                {
                    favorite_id: str,
                    merchandise: {
                        merchandise_id: str,
                        name: str,
                        slug: str,
                        image: str,
                        price: str,
                        description: str,
                        rating: float (optional),
                        total_sold: int (optional),
                        stock: int (optional),
                        category: str (optional)
                    },
                    created_at: str (ISO format)
                },
                ...
            ]
        }
    """
    favorites = Favorite.objects.filter(user=request.user).select_related('merchandise')
    data = []
    
    for fav in favorites:
        merch = fav.merchandise
        
        # Get image URL safely
        image_url = None
        if hasattr(merch, 'image') and merch.image:
            try:
                image_url = merch.image.url
            except (ValueError, AttributeError):
                image_url = None
        
        # Build merchandise data with required fields
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
    
    return JsonResponse({
        'status': 'ok', 
        'favorites': data
    })


@login_required
@require_http_methods(["GET"])
def check_favorite(request, merchandise_id):
    """
    Check apakah merchandise tertentu sudah difavorite oleh current user.
    Useful untuk single product pages untuk show correct initial state.
    
    URL Parameters:
        - merchandise_id: UUID merchandise yang mau dicek
        
    Returns:
        200: {
            status: 'ok',
            is_favorited: bool,
            favorite_id: str|null
        }
        
    Note: 
        merchandise_id sudah divalidasi sebagai UUID oleh Django URL pattern,
        jadi tidak perlu validasi manual lagi.
    """
    try:
        favorite = Favorite.objects.get(
            user=request.user, 
            merchandise_id=merchandise_id
        )
        return JsonResponse({
            'status': 'ok',
            'is_favorited': True,
            'favorite_id': str(favorite.id)
        })
    except Favorite.DoesNotExist:
        return JsonResponse({
            'status': 'ok',
            'is_favorited': False,
            'favorite_id': None
        })