from django.urls import path
from InformasiPertandingan.views import show_main, create_match, show_json, show_json_by_id, edit_match, delete_match, show_match
app_name = 'InformasiPertandingan'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('create-match/', create_match, name='create_match'),
    path('json/', show_json, name='show_json'),
    path('json/<str:match_id>/', show_json_by_id, name='show_json_by_id'),
    path('edit-match/<uuid:match_id>/', edit_match, name='edit_match'),
    path('match/<uuid:id>/delete', delete_match, name='delete_match'),
    path('match/<str:id>/', show_match, name='show_match')
]
