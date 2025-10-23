# favoritesApp/urls.py
from django.urls import path
from . import views

app_name = 'favoritesApp'

urlpatterns = [
    path('', views.favorites_list, name='list'),        # GET -> halaman favorites
    path('add/', views.add_favorite, name='add'),       # POST -> tambah favorite
    path('remove/', views.remove_favorite, name='remove'), # POST -> hapus favorite
    path('json/', views.favorites_json, name='json'),   # GET -> list favorites sebagai JSON
]