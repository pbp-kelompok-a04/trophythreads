from django.urls import path
from InformasiPertandingan.views import edit_match_flutter, delete_match_flutter, show_json_country, show_main, add_match, create_match_flutter, proxy_image, show_json, show_json_by_id, edit_match, delete_match, show_match, show_xml, show_xml_by_id
app_name = 'InformasiPertandingan'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('add-match/', add_match, name='add_match'),
    path('json/', show_json, name='show_json'),
    path('json/<str:match_id>/', show_json_by_id, name='show_json_by_id'),
    path('xml/', show_xml, name='show_xml'),
    path('xml/<str:match_id>/', show_xml_by_id, name='show_xml_by_id'),
    path('edit-match/<uuid:match_id>/', edit_match, name='edit_match'),
    path('edit-flutter/<str:match_id>/', edit_match_flutter, name='edit_match_flutter'),
    path('match/<uuid:id>/delete', delete_match, name='delete_match'),
    path('match/<str:id>/', show_match, name='show_match'),
    path('proxy-image/', proxy_image, name='proxy_image'),
    path('create-flutter/', create_match_flutter, name='create_match_flutter'),
    path('json-country/', show_json_country, name='show_json_country'),
    path('match/<str:id>/delete-flutter/', delete_match_flutter, name='delete_match_flutter')
]