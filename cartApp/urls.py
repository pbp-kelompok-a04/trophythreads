# cartApp/urls.py
from django.urls import path
from . import views

app_name = 'cartApp'

urlpatterns = [
    path('', views.cart_page, name='cart_page'),
    path('json/', views.show_json, name='show_json'), # Fetch Cart Items
    path('checkout-json/', views.show_checkout_json, name='show_checkout_json'), # Get checkout items
    path('toggle-select/<int:item_id>/', views.toggle_select_item_ajax, name='toggle_select_item'),
    path('loading/', views.loading_view, name='loading'),
    path('after-checkout/', views.after_checkout, name='after_checkout'),
    # API Actions
    path('add/', views.add_to_cart_ajax, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item_ajax, name='update_cart_item'),
    path('delete/<int:item_id>/', views.delete_item_ajax, name='delete_item'),
    path('toggle/<int:item_id>/', views.toggle_select_ajax, name='toggle_select'),
    path('toggle-all/', views.toggle_select_all, name='toggle_select_all'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('buy-now/', views.buy_now_ajax, name='buy_now'),
]