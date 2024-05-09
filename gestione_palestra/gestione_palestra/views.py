from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.urls import reverse
from . import forms
from . import models
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect


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
            return redirect(reverse('account'))
        else:
            error_message = "Username or password is incorrect."
            return render(request=request, template_name="login.html", context={'error_message': error_message})
        
class AccountView(View):
    def get(self, request):
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
            login(request, user)
            # Qui puoi fare altre operazioni, come login automatico o reindirizzamento a una pagina di successo
            return HttpResponseRedirect(reverse('account'))
        else:
            return render(request, 'registration.html', {'form': form})
    

class ProfileView(View):
    def get(self, request):
        form = forms.UserProfileForm()
        user_profile, created = models.UserProfile.objects.get_or_create(user=request.user)
        return render(request, 'profile.html', {'form': form, 'user_profile':user_profile})

    def post(self, request, *args, **kwargs):
        form = forms.UserProfileForm(request.POST)
        user_profile = get_object_or_404(models.UserProfile, user=request.user)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('profile')
        
        return render(request, 'profile.html', {'form': form, 'user_profile':user_profile})


class UpdateProfile(View):
    def get(self, request):
        user_profile = models.UserProfile.objects.get(user=request.user)
        form = forms.UserProfileForm(request.POST, instance=user_profile)
        return render(request, 'update_profile.html', {'form': form})
    
    def post(self, request, *args, **kwargs):
        user_profile = models.UserProfile.objects.get(user=request.user)
        form = forms.UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Reindirizza alla pagina del profilo
        
        return render(request, 'update_profile.html', {'form': form})