from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'my_django_app/base.html')

def about(request):
    return HttpResponse("This is the about page.")