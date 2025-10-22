from django.urls import path
from forumApp.views import show_landing_page

app_name = 'forumApp'

urlpatterns = [
    path('', show_landing_page, name='show_landing_page'),
]
