from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser
from django.contrib import messages
from main.models import Profile
from django.http import HttpResponseRedirect, JsonResponse
import datetime
from django.urls import reverse

# Helper function to extract form errors for JSON
def get_form_errors_json(form):
    """Converts Django form errors into a clean dictionary for JSON response."""
    errors = {
        'non_field_errors': [],
        'field_errors': {}
    }

    # Handle __all__ and other non-field errors
    if form.non_field_errors():
        errors['non_field_errors'] = [str(e) for e in form.non_field_errors()]

    # Handle specific field errors
    for field in form.fields:
        if form.errors.get(field):
            # Convert ErrorList/ValidationErrors to strings
            errors['field_errors'][field] = [str(e) for e in form.errors.get(field)]
            
    return errors

def register(request):
    is_ajax = request.POST.get('is_ajax') == 'true'
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        
        if form.is_valid():
            role = request.POST.get("role")
            if not role:
                 pass 

            user = form.save()
            Profile.objects.create(user=user, role=role if role else 'user') 
            
            success_message = 'Your account has been successfully created!'
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'redirect_url': reverse('main:login')
                })
            
            messages.success(request, success_message)
            return redirect('main:login')
        
        if is_ajax:
            return JsonResponse({
                'success': False,
                'errors': get_form_errors_json(form)
            }, status=400) 
        
    context = {'form':form}
    return render(request, 'register.html', context)

def login_user(request):
    is_ajax = request.POST.get('is_ajax') == 'true'
    form = AuthenticationForm()
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            redirect_url = reverse("InformasiPertandingan:show_main")
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'redirect_url': redirect_url
                })

            response = HttpResponseRedirect(redirect_url)
            response.set_cookie('last_login', str(datetime.datetime.now()))
            return response

        if is_ajax:
            return JsonResponse({
                'success': False,
                'errors': get_form_errors_json(form)
            }, status=400) 

    context = {'form': form}
    return render(request, 'login.html', context)

def guest_login(request):
    logout(request)
    request.session.flush()

    request.session['is_guest'] = True
    request.session['guest_name'] = "Guest"

    return redirect('InformasiPertandingan:show_main')

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response