from django.urls import path
from main.views import login_user, register

app_name = 'main'

urlpatterns = [
    path('', login_user, name='login_user'),
    path('register/', register, name='register'),
]
