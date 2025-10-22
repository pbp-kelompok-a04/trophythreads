# cartApp/urls.py
from django.urls import path
from . import views

app_name = 'cartApp'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),                # POST AJAX
    path('cart/update-quantity/', views.update_quantity, name='update_qty'),# POST AJAX
    path('cart/toggle-select/', views.toggle_select, name='toggle_select'), # POST AJAX
    path('cart/delete/', views.delete_item, name='delete_item'),            # POST AJAX
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/place-order/', views.place_order, name='place_order'),   # POST
    path('after-checkout/', views.after_checkout_view, name='after_checkout'),
]
