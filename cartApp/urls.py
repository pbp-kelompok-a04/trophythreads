# cartApp/urls.py
from django.urls import path
from . import views

app_name = 'cartApp'

urlpatterns = [
    path('', views.cart_page, name='cart_page'),
    path('add/', views.add_to_cart_ajax, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item_ajax, name='update_cart_item'),
    path('toggle/<int:item_id>/', views.toggle_select_ajax, name='toggle_select'),
    path('delete/<int:item_id>/', views.delete_item_ajax, name='delete_item'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('after/', views.after_checkout, name='after_checkout'),
    path('json/', views.cart_json, name='cart_json'),  # helper: return cart JSON
]
