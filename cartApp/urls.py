# cartApp/urls.py
from django.urls import path
from . import views

app_name = 'cartApp'

urlpatterns = [
    path('', views.cart_page, name='cart_page'),
    path('<int:item_id>/', views.cart_item_detail, name='cart_item_detail'),
    path('add/', views.add_to_cart_ajax, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item_ajax, name='update_cart_item'),
    path('toggle/<int:item_id>/', views.toggle_select_ajax, name='toggle_select'),
    path('toggle-all/', views.toggle_select_all, name='toggle_select_all'),  
    path('delete/<int:item_id>/', views.delete_item_ajax, name='delete_item'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('buy-now/', views.buy_now_ajax, name='buy_now'),
    path('after/', views.after_checkout, name='after_checkout'),
    path('loading/', views.loading_view, name='loading'),
    # JSON ENDPOINT
    path('json/', views.show_json, name='show_json'),
    path('json/<int:item_id>/', views.show_json_by_id, name='show_json_by_id'),
    path('checkout/json/', views.show_checkout_json, name='show_checkout_json'),
]