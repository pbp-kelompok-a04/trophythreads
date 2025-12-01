# favoritesApp/views.py
from uuid import UUID
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from .models import Favorite
from django.apps import apps


# Ambil model Merchandise secara aman dari app yang benar
MerchandiseModel = lambda: apps.get_model('merchandiseApp', 'Merchandise')


@login_required
def favorites_list(request):
    """
    Render halaman daftar favorites untuk user yang login.
    """
    favorites = Favorite.objects.filter(user=request.user).select_related('merchandise')
    return render(request, 'favorites_list.html', {'favorites': favorites})


@csrf_exempt  # Tambahkan ini jika masih ada masalah CSRF
@require_POST
def add_favorite(request):
    """
    Tambah merchandise ke favorites user.
    AJAX-friendly endpoint yang returns JSON.
    """
    # Check authentication - PENTING!
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error', 
            'message': 'auth_required'
        }, status=401)

    # Get merchandise_id from request
    merch_id = request.POST.get('merchandise_id') or request.POST.get('product_id')
    
    # Debug log
    print(f"[ADD_FAVORITE] User: {request.user}, Merch ID: {merch_id}")
    
    if not merch_id:
        return JsonResponse({
            'status': 'error', 
            'message': 'merchandise_id required'
        }, status=400)

    # Validate UUID format
    try:
        UUID(merch_id)
    except (ValueError, TypeError):
        return JsonResponse({
            'status': 'error',
            'message': f'Invalid merchandise_id format: {merch_id}'
        }, status=400)

    # Get merchandise object
    Merchandise = MerchandiseModel()
    try:
        merchandise = get_object_or_404(Merchandise, pk=merch_id)
    except Exception as e:
        print(f"[ADD_FAVORITE] Error: {str(e)}")
        return JsonResponse({
            'status': 'error', 
            'message': f'Merchandise not found: {merch_id}'
        }, status=404)

    # Create or get existing favorite
    favorite, created = Favorite.objects.get_or_create(
        user=request.user, 
        merchandise=merchandise
    )
    
    action = 'added' if created else 'exists'
    
    print(f"[ADD_FAVORITE] Success: {action}, Favorite ID: {favorite.id}")
    
    return JsonResponse({
        'status': 'ok', 
        'action': action, 
        'favorite_id': str(favorite.id)
    }, status=200)


@login_required
@csrf_exempt
@require_POST
def remove_favorite(request):
    """
    Hapus merchandise dari favorites user.
    Accepts favorite_id OR merchandise_id.
    """
    favorite_id = request.POST.get('favorite_id')
    merch_id = request.POST.get('merchandise_id') or request.POST.get('product_id')

    print(f"[REMOVE_FAVORITE] User: {request.user}, Fav ID: {favorite_id}, Merch ID: {merch_id}")

    # Option 1: Remove by favorite_id
    if favorite_id:
        try:
            fav = get_object_or_404(Favorite, pk=favorite_id, user=request.user)
            fav.delete()
            print(f"[REMOVE_FAVORITE] Success: removed {favorite_id}")
            return JsonResponse({
                'status': 'ok', 
                'action': 'removed'
            })
        except Exception as e:
            print(f"[REMOVE_FAVORITE] Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Favorite not found'
            }, status=404)

    # Option 2: Remove by merchandise_id
    if merch_id:
        try:
            UUID(merch_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'status': 'error',
                'message': 'invalid merchandise_id (expect UUID)'
            }, status=400)

        Merchandise = MerchandiseModel()
        try:
            merchandise = get_object_or_404(Merchandise, pk=merch_id)
            qs = Favorite.objects.filter(user=request.user, merchandise=merchandise)
            deleted, _ = qs.delete()
            
            if deleted:
                print(f"[REMOVE_FAVORITE] Success: removed merch {merch_id}")
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
            print(f"[REMOVE_FAVORITE] Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Merchandise not found'
            }, status=404)

    return JsonResponse({
        'status': 'error',
        'message': 'favorite_id or merchandise_id required'
    }, status=400)


@login_required
def favorites_json(request):
    """
    Return favorites sebagai JSON dengan complete merchandise data.
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
        
        if hasattr(merch, 'thumbnail') and merch.thumbnail:
            image_url = merch.thumbnail
        
        # Build merchandise data
        merchandise_data = {
            'merchandise_id': str(merch.pk),
            'name': getattr(merch, 'name', 'Unknown Product'),
            'slug': str(merch.pk),  # Use ID as slug if no slug field
            'image': image_url,
            'price': str(getattr(merch, 'price', 0)),
            'description': getattr(merch, 'description', ''),
        }
        
        # Add optional fields
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
    Check apakah merchandise tertentu sudah difavorite.
    """
    print(f"[CHECK_FAVORITE] User: {request.user}, Merch ID: {merchandise_id}")
    
    try:
        favorite = Favorite.objects.get(
            user=request.user, 
            merchandise_id=merchandise_id
        )
        print(f"[CHECK_FAVORITE] Found: {favorite.id}")
        return JsonResponse({
            'status': 'ok',
            'is_favorited': True,
            'favorite_id': str(favorite.id)
        })
    except Favorite.DoesNotExist:
        print(f"[CHECK_FAVORITE] Not found")
        return JsonResponse({
            'status': 'ok',
            'is_favorited': False,
            'favorite_id': None
        })
    except Exception as e:
        print(f"[CHECK_FAVORITE] Error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)