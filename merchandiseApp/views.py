from django.shortcuts import render, redirect, get_object_or_404
from .models import Merchandise
from .forms import MerchandiseForm

from django.http import HttpResponse
from django.core import serializers

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def show_main_merchandise(request):
    merchandise_list = Merchandise.objects.all()

    context = {
        'merchandise_list': merchandise_list, 
        'last_login': request.COOKIES.get('last_login', 'Never')
    }

    return render(request, "main_merchandise.html", context)

def show_merchandise(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id)
    merchandise.increment_views()

    context = {
        'merchandise': merchandise
    }

    return render(request, "merchandise_detail.html", context)
   
@csrf_exempt
def create_merchandise_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated. Please login first.'}, status=401)
    
    # Cek role user
    if request.user.profile.role not in ['seller']:
        return JsonResponse({'error': 'Only seller can create merchandise.'}, status=403)
    
    if request.method == 'POST':
        name = request.POST.get("name")
        price = request.POST.get("price")
        category = request.POST.get("category")
        stock = request.POST.get("stock")
        thumbnail = request.POST.get("thumbnail")
        description = request.POST.get("description")
        is_featured = request.POST.get("is_featured") == 'true'

        is_featured = request.POST.get("is_featured")
        if is_featured == 'true':
            is_featured = True
        else:
            is_featured = False

        merchandise = Merchandise.objects.create(
            user=request.user,
            name=name,
            price=price,
            category=category,
            stock=stock,
            thumbnail=thumbnail,
            description=description,
            is_featured=is_featured
        )

        return JsonResponse({
            'message': 'Merchandise created successfully!',
            'merchandise_id': merchandise.id
        }, status=201)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def edit_merchandise_ajax(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated. Please login first.'}, status=401)
    
    # Cek role user
    if request.user.profile.role not in ['seller']:
        return JsonResponse({'error': 'Only seller can edit merchandise.'}, status=403)
    
    
    if request.method == 'POST':
        merchandise.name = request.POST.get("name")
        merchandise.price = request.POST.get("price")
        merchandise.category = request.POST.get("category")
        merchandise.stock = request.POST.get("stock")
        merchandise.description = request.POST.get("description")
        merchandise.thumbnail = request.POST.get("thumbnail")
        is_featured = request.POST.get("is_featured")
        if is_featured == 'true':
            merchandise.is_featured = True
        else:
            merchandise.is_featured = False
        merchandise.save()

        return JsonResponse({
            'message': 'Merchandise updated successfully!',
            'merchandise_id': merchandise.id
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def delete_merchandise_ajax(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated. Please login first.'}, status=401)
    
    # Cek role user
    if request.user.profile.role not in ['seller']:
        return JsonResponse({'error': 'Only seller can delete merchandise.'}, status=403)
    

    if merchandise.user != request.user:
        return JsonResponse({'error': 'You are not authorized to delete this merchandise'}, status=403)

    if request.method == 'DELETE':
        merchandise_id = merchandise.id
        merchandise.delete()
        return JsonResponse({
            'message': 'Merchandise deleted successfully!',
            'merchandise_id': str(merchandise_id)
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_merchandise_json(request):
    merchandise = Merchandise.objects.all()
    print(f"DEBUG: My merchandise count = {merchandise.count()}")

    merchandise_data = []
    for item in merchandise:
        merchandise_data.append({
            'id': str(item.id),  # Convert UUID to string
            'user': item.user.id if item.user else None,
            'name': item.name,
            'price': item.price,
            'category': item.category,
            'stock': item.stock,
            'thumbnail': item.thumbnail,
            'description': item.description,
            'product_views': item.product_views,
            'is_featured': item.is_featured,
            'rating': 0.0,  # Default value for rating
        })
    
    return JsonResponse(merchandise_data, safe=False)

def show_xml(request):
     merchandise_list = Merchandise.objects.all()
     xml_data = serializers.serialize("xml", merchandise_list)
     return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    merchandise_list = Merchandise.objects.all()
    json_data = serializers.serialize("json", merchandise_list)
    return HttpResponse(json_data, content_type="application/json")

def show_xml_by_id(request, merchandise_id):
   try:
       merchandise_item = Merchandise.objects.filter(pk=merchandise_id)
       xml_data = serializers.serialize("xml", merchandise_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Merchandise.DoesNotExist:
       return HttpResponse(status=404)

def show_json_by_id(request, merchandise_id):
   try:
       merchandise_item = Merchandise.objects.get(pk=merchandise_id)
       json_data = serializers.serialize("json", [merchandise_item])
       return HttpResponse(json_data, content_type="application/json")
   except Merchandise.DoesNotExist:
       return HttpResponse(status=404)
