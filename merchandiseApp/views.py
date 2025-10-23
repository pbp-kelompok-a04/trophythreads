from django.shortcuts import render, redirect, get_object_or_404
from .models import Merchandise
from .forms import MerchandiseForm

from django.http import HttpResponse
from django.core import serializers

from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import csv
import os
from django.conf import settings
from django.http import Http404

def show_mainMerchandise(request):
    csv_path = os.path.join(settings.BASE_DIR, 'merchandise.csv')
    merchandise_list = []

    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                merchandise_list.append({
                    'name': row.get('name', ''),
                    'price': row.get('price', ''),
                    'category': row.get('category', ''),
                    'stock': row.get('stock', ''),
                    'description': row.get('description', ''),
                    'thumbnail': row.get('thumbnail', ''),
                })
    except FileNotFoundError:
        merchandise_list = []

    if request.user.is_authenticated:
        last_login = request.COOKIES.get('last_login', 'Never')
        username = request.user.username
    else:
        last_login = 'Guest'
        username = request.session.get('guest_name', 'Guest')

    context = {
        'merchandise_list': merchandise_list,
        'last_login': last_login,
        'username': username,
    }

    return render(request, "main_merchandise.html", context)

def show_merchandise(request, id):
    import csv, os
    from django.conf import settings
    from django.http import Http404

    csv_path = os.path.join(settings.BASE_DIR, 'merchandise.csv')
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.DictReader(csvfile))
            if id < 0 or id >= len(reader):
                raise Http404("Invalid merchandise ID")
            selected = reader[id]
    except FileNotFoundError:
        raise Http404("Merchandise data not found")

    return render(request, 'merchandise_detail.html', {'merchandise': selected})
   
# @csrf_exempt
@login_required(login_url='/login/')
@require_POST
def create_merchandise_ajax(request):
    # cek role seller
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        return JsonResponse({'error': 'Profile not found. Contact admin.'}, status=403)
    if profile.role != 'seller':
        return JsonResponse({'error': 'Permission denied. Sellers only.'}, status=403)
    # ambil data dari request.POST / FILES
    name = request.POST.get("name")
    price = request.POST.get("price")
    category = request.POST.get("category")
    stock = request.POST.get("stock")
    description = request.POST.get("description")
    # thumbnail mungkin datang di FILES
    thumbnail = request.FILES.get("thumbnail") if 'thumbnail' in request.FILES else None

    if not name or price is None:
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    try:
        price = float(price)
        stock = int(stock) if stock is not None else 0
    except ValueError:
        return JsonResponse({'error': 'Invalid numeric fields'}, status=400)

    merchandise = Merchandise.objects.create(
        user=request.user,
        name=name,
        price=price,
        category=category or '',
        stock=stock,
        description=description or '',
    )

    if thumbnail:
        merchandise.thumbnail = thumbnail
        merchandise.save()

    return JsonResponse({
        'message': 'Merchandise created successfully',
        'id': str(merchandise.id)
    }, status=201)

# @csrf_exempt
@login_required(login_url='/login/')
@require_POST
def edit_merchandise_ajax(request, id):
    # cek role seller
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        return JsonResponse({'error': 'Profile not found. Contact admin.'}, status=403)
    if profile.role != 'seller':
        return JsonResponse({'error': 'Permission denied. Sellers only.'}, status=403)

    merchandise = get_object_or_404(Merchandise, pk=id)

    if getattr(merchandise, 'user', None) != request.user:
        return JsonResponse({'error': 'You are not authorized to edit this merchandise'}, status=403)

    name = request.POST.get("name")
    price = request.POST.get("price")
    category = request.POST.get("category")
    stock = request.POST.get("stock")
    description = request.POST.get("description")

    if name is not None:
        merchandise.name = name
    if price is not None:
        try:
            merchandise.price = float(price)
        except ValueError:
            return JsonResponse({'error': 'Invalid price'}, status=400)
    if category is not None:
        merchandise.category = category
    if stock is not None:
        try:
            merchandise.stock = int(stock)
        except ValueError:
            return JsonResponse({'error': 'Invalid stock'}, status=400)
    if description is not None:
        merchandise.description = description

    if 'thumbnail' in request.FILES:
        merchandise.thumbnail = request.FILES['thumbnail']

    merchandise.save()

    return JsonResponse({'message': 'Merchandise updated', 'id': str(merchandise.id)}, status=200)


# @csrf_exempt
@login_required(login_url='/login/')
def delete_merchandise_ajax(request, id):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        return JsonResponse({'error': 'Profile not found. Contact admin.'}, status=403)
    if profile.role != 'seller':
        return JsonResponse({'error': 'Permission denied. Sellers only.'}, status=403)

    merchandise = get_object_or_404(Merchandise, pk=id)

    if getattr(merchandise, 'user', None) != request.user:
        return JsonResponse({'error': 'You are not authorized to delete this merchandise'}, status=403)

    if request.method in ('POST', 'DELETE'):
        merchandise_id = str(merchandise.id)
        merchandise.delete()
        return JsonResponse({'message': 'Product deleted', 'id': merchandise_id}, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required(login_url='/login/')
def get_merchandise_json(request):
    print(f"DEBUG: Current user = {request.user} (ID: {request.user.id})")
    merchandise = Merchandise.objects.filter(user=request.user)
    print(f"DEBUG: My merchandise count = {merchandise.count()}")
    return HttpResponse(serializers.serialize('json', merchandise), content_type='application/json')

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
