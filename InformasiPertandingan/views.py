from django.shortcuts import render, get_object_or_404
from InformasiPertandingan.models import Informasi, Country
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core import serializers
from django.utils.html import strip_tags

# fungsi halaman utama page
def show_main(request):
    informasi_list = Informasi.objects.all()
    context = {
        'list_pertandingan': informasi_list,
    }
    return render(request, 'InformasiPertandingan/main.html', context)

# fungsi untuk menambahkan match baru
# match harus menyesuaikan dengan country valid (data di country.csv)
@csrf_exempt
@require_POST
def add_match(request):
    title = strip_tags(request.POST.get("title"))
    date = request.POST.get("date")
    city = strip_tags(request.POST.get("city"))
    country = strip_tags(request.POST.get("country"))
    home_team_name = request.POST.get("home_team")
    away_team_name = request.POST.get("away_team")
    score_home_team = request.POST.get("score_home_team")
    score_away_team = request.POST.get("score_away_team")
    user = request.user if request.user.is_authenticated else None
    
    home_team = get_object_or_404(Country, name=home_team_name)
    away_team = get_object_or_404(Country, name=away_team_name)

    new_match = Informasi(
        title=title,
        date=date,
        city=city,
        country=country,
        home_team=home_team,
        away_team=away_team,
        score_home_team=score_home_team,
        score_away_team=score_away_team,
        user=user
    )
    new_match.save()
    return JsonResponse({'success': True, 'id': new_match.id}, status=201)

# fungsi untuk menampilkan data dengan format json
def show_json(request):
    # select related untuk sekaligus mengambil data country
    informasi_list = Informasi.objects.select_related('home_team', 'away_team').all()
    data = []
    # menambahkan semua data matches
    for informasi in informasi_list:
        data.append({
            'id': str(informasi.id),
            'title': informasi.title,
            'date': informasi.date.isoformat(),
            'city': informasi.city,
            'country': informasi.country,
            'is_info_hot': informasi.is_info_hot,
            'home_team': {
                'name': informasi.home_team.name,
                'flag': informasi.home_team.flag
            },
            'away_team': {
                'name': informasi.away_team.name,
                'flag': informasi.away_team.flag
            },
            'score_home': informasi.score_home_team,
            'score_away': informasi.score_away_team,
            'views': informasi.views,
            'user_id': informasi.user_id if informasi.user else None,
        })
    return JsonResponse(data, safe=False)

# fungsi untuk menampilkan data json berdasarkan suatu id match
def show_json_by_id(request, match_id):
    try:
        informasi = Informasi.objects.select_related('user').get(pk=match_id)
        data = {
            'id': str(informasi.id),
            'title': informasi.title,
            'date': informasi.date.isoformat(),
            'city': informasi.city,
            'country': informasi.country,
            'is_info_hot': informasi.is_info_hot,
            'home_team': {
                'name': informasi.home_team.name,
                'flag': informasi.home_team.flag
            },
            'away_team': {
                'name': informasi.away_team.name,
                'flag': informasi.away_team.flag
            },
            'score_home_team': informasi.score_home_team,
            'score_away_team': informasi.score_away_team,
            'views': informasi.views,
            'user_id': informasi.user_id if informasi.user else None,
        }
        return JsonResponse(data)
    except Informasi.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

# fungsi untuk menghapus suatu match
def delete_match(request, id):
    match = get_object_or_404(Informasi, pk=id)
    match.delete()
    return HttpResponseRedirect(reverse('InformasiPertandingan:show_main'))

# fungsi untuk mengedit atau mengubah match
@csrf_exempt
@require_POST
def edit_match(request, match_id):
    match = get_object_or_404(Informasi, pk=match_id)
    home_team_name = request.POST.get("home_team")
    away_team_name = request.POST.get("away_team")
    
    if home_team_name:
        match.home_team = get_object_or_404(Country, name=home_team_name)
    if away_team_name:
        match.away_team = get_object_or_404(Country, name=away_team_name)
    
    match.title = request.POST.get("title", match.title)
    match.date = request.POST.get("date", match.date)
    match.city = request.POST.get("city", match.city)
    match.country = request.POST.get("country", match.country)
    match.score_home_team = request.POST.get("score_home_team", match.score_home_team)
    match.score_away_team = request.POST.get("score_away_team", match.score_away_team)
    match.save()
    return JsonResponse({'success': True})

# fungsi untuk menampilkan suatu match (detail match)
def show_match(request, id):
    informasi = get_object_or_404(Informasi, pk = id)
    informasi.increment_views() # menambah views setiap suatu match diakses
    context = {
        'match': informasi
    }
    return render(request, "InformasiPertandingan/match_detail.html", context)

# fungsi untuk menampilkan data dalam format xml
def show_xml(request):
    match_list = Informasi.objects.all()
    xml_data = serializers.serialize("xml", match_list)
    return HttpResponse(xml_data, content_type="application/xml")

# fungsi untuk menampilkan 1 match dalam format xml
def show_xml_by_id(request, match_id):
    try:
        match = Informasi.objects.get(pk=match_id)
        match_item_list = [match]
        xml_data = serializers.serialize("xml", match_item_list)
        return HttpResponse(xml_data, content_type="application/xml")
    
    except Informasi.DoesNotExist:
        return HttpResponse(status=404)