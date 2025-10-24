from django.urls import path
from main.views import login_user, register, guest_login

app_name = 'main'

urlpatterns = [
    path('', login_user, name='login'),
    path('register/', register, name='register'),
    path('guest-login/', guest_login, name='guest_login'),
]
