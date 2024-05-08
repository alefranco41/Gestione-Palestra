from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.contrib.auth.models import User
from django.urls import reverse

from . import forms

def homepage(request):
    context = {
        'gym_name' : 'Fit4All'
    }
    return render(request, 'home.html', context=context)

class GymClassesView(View):
    def get(self, request):
        return render(request=request, template_name="classes-schedule.html", context={})

class TrainerListView(View):
    def get(self, request):
        return render(request=request, template_name="trainer-list.html", context={})

class SubscriptionPlansView(View):
    def get(self, request):
        return render(request=request, template_name="subscription-plans.html", context={})

class LoginView(View):
    def get(self, request):
        return render(request=request, template_name="login.html", context={})
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '')  
        password = request.POST.get('password', '')  

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('account', kwargs={'user_id': user.id}))
        else:
            error_message = "Username or password is incorrect."
            return render(request=request, template_name="login.html", context={'error_message': error_message})
        
class AccountView(View):
    def get(self, request, user_id):
        return render(request, 'account.html', {})
    
    
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('homepage')
    

class RegistrationView(View):
    def get(self, request):
        return render(request=request, template_name="registration.html", context={})

    def post(self, request, *args, **kwargs):
        form = forms.UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Salva l'utente nel database
            # Qui puoi fare altre operazioni, come login automatico o reindirizzamento a una pagina di successo
            return redirect(request, 'account.html', context={})
        else:
            return render(request, 'registration.html', {'form': form})
    
class ProfileView(View):
    def get(self, request, user_id):
        return render(request, 'profile.html', {})