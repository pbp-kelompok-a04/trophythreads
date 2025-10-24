from django.urls import path
from .views import show_main_merchandise, show_merchandise, create_merchandise_ajax, edit_merchandise_ajax, delete_merchandise_ajax, get_merchandise_json, show_xml, show_json, show_json_by_id, show_xml_by_id

app_name = 'merchandiseApp'

urlpatterns = [
    path('', show_main_merchandise, name='show_main'),
    path('<uuid:id>/', show_merchandise, name='show_merchandise'),
    path('create/', create_merchandise_ajax, name='create_merchandise_ajax'),
    path('edit/<uuid:id>/', edit_merchandise_ajax, name='edit_merchandise_ajax'),
    path('delete/<uuid:id>/', delete_merchandise_ajax, name='delete_merchandise_ajax'),
    path('xml/', show_xml, name='show_xml'),
    path('json/', show_json, name='show_json'),
    path('json/<uuid:merchandise_id>/', show_json_by_id, name='show_json_by_id'),
    path('xml/<uuid:merchandise_id>/', show_xml_by_id, name='show_xml_by_id'),
    path('get-merchandise/', get_merchandise_json, name='get_merchandise_json'),
]