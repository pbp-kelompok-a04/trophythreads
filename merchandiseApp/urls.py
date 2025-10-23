from django.urls import path
from .views import show_main, show_merchandise, create_merchandise_ajax, edit_merchandise_ajax, delete_merchandise_ajax, get_merchandise_json, show_xml, show_json, show_json_by_id, show_xml_by_id

urlpatterns = [
    path('', show_main, name='show_main'),
    path('merchandise/<int:id>/', show_merchandise, name='show_merchandise'),
    path('merchandise/create/', create_merchandise_ajax, name='create_merchandise_ajax'),
    path('merchandise/edit/<int:id>/', edit_merchandise_ajax, name='edit_merchandise_ajax'),
    path('merchandise/delete/<int:id>/', delete_merchandise_ajax, name='delete_merchandise_ajax'),
    path('merchandise/json/', get_merchandise_json, name='get_merchandise_json'),
    path('merchandise/xml/', show_xml, name='show_xml'),
    path('merchandise/json/', show_json, name='show_json'),
    path('merchandise/json/<int:merchandise_id>/', show_json_by_id, name='show_json_by_id'),
    path('merchandise/xml/<int:merchandise_id>/', show_xml_by_id, name='show_xml_by_id'),
]