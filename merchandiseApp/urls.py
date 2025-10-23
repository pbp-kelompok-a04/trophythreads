from django.urls import path
from . import views
from .views import show_mainMerchandise, show_merchandise, create_merchandise_ajax, edit_merchandise_ajax, delete_merchandise_ajax, get_merchandise_json, show_xml, show_json, show_json_by_id, show_xml_by_id

app_name = 'merchandiseApp'

urlpatterns = [
    path('', show_mainMerchandise, name='show_mainMerchandise'),
    path('merchandise/<int:id>/', show_merchandise, name='show_merchandise'),
    path('merchandise/create/', create_merchandise_ajax, name='create_merchandise_ajax'),
    path('merchandise/edit/<uuid:id>/', edit_merchandise_ajax, name='edit_merchandise_ajax'),
    path('merchandise/delete/<uuid:id>/', delete_merchandise_ajax, name='delete_merchandise_ajax'),
    path('merchandise/json/', get_merchandise_json, name='get_merchandise_json'),
    path('merchandise/xml/', show_xml, name='show_xml'),
    path('merchandise/json/', show_json, name='show_json'),
    path('merchandise/json/<uuid:merchandise_id>/', show_json_by_id, name='show_json_by_id'),
    path('merchandise/xml/<uuid:merchandise_id>/', show_xml_by_id, name='show_xml_by_id'),
    # addition
    # path('', views.main_merchandise, name='main_merchandise'),
]  