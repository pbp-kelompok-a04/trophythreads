from django.shortcuts import render, redirect, get_object_or_404
from InformasiPertandingan.models import Informasi, Country
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def show_main(request):
    informasi_list = Informasi.objects.all()
    context = {
        'list_pertandingan': informasi_list,
    }
    return render(request, 'InformasiPertandingan/main.html', context)

@csrf_exempt
@require_POST
def add_match_entry_ajax(request):
    title = request.POST.get("title")
    date = request.POST.get("date")
    city = request.POST.get("city")
    country = request.POST.get("country")
    home_team_id = request.POST.get("home_team")
    away_team_id = request.POST.get("away_team")
    score_home_team = request.POST.get("score_home_team")
    score_away_team = request.POST.get("score_away_team")
    user = request.user

    home_team = get_object_or_404(Country, pk=home_team_id)
    away_team = get_object_or_404(Country, pk=away_team_id)

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

    return HttpResponse(b"CREATED", status=201)

def show_json(request):
    informasi_list = Informasi.objects.select_related('home_team', 'away_team').all()
    data = []
    for informasi in informasi_list:
        data.append({
            'id': str(informasi.id),
            'title': informasi.title,
            'date': informasi.date.isoformat(),
            'city': informasi.city,
            'country': informasi.country,
            'home_team': informasi.home_team.name,
            'away_team': informasi.away_team.name,
            'home_flag': informasi.home_team.flag,
            'away_flag': informasi.away_team.flag,
            'score_home': informasi.score_home_team,
            'score_away': informasi.score_away_team,
            'views': informasi.views,
            'user_id': informasi.user_id if informasi.user else None,
        })

    return JsonResponse(data, safe=False)

def show_json_by_id(request, match_id):
    try:
        informasi = Informasi.objects.select_related('user').get(pk=match_id)
        data = {
            'id': str(informasi.id),
            'title': informasi.title,
            'date': informasi.date.isoformat(),
            'city': informasi.city,
            'country': informasi.country,
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
    except informasi.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)
    
def delete_match(request, id):
    match = get_object_or_404(Informasi, pk=id)
    match.delete()
    return HttpResponseRedirect(reverse('InformasiPertandingan:show_main'))

@csrf_exempt
@require_POST
def edit_match(request, match_id):
    match = get_object_or_404(Informasi, pk=match_id)
    home_team_id = request.POST.get("home_team")
    away_team_id = request.POST.get("away_team")
    
    if home_team_id:
        match.home_team = get_object_or_404(Country, pk=home_team_id)
    if away_team_id:
        match.away_team = get_object_or_404(Country, pk=away_team_id)
    
    match.title = request.POST.get("title")
    match.date = request.POST.get("date")
    match.city = request.POST.get("city")
    match.country = request.POST.get("country")
    match.score_home_team = request.POST.get("score_home_team")
    match.score_away_team = request.POST.get("score_away_team")
    match.save()

    return JsonResponse({'success': True})

def show_match(request, id):
    informasi = get_object_or_404(Informasi, pk = id)
    context = {
        'match': informasi
    }
    return render(request, "InformasiPertandingan/match_detail.html", context)
