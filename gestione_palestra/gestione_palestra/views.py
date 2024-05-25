from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from utils import functions
from palestra import forms

class HomePage(View):
    def get(self, request):
        return render(request, 'home.html', context={})

    def post(self, request, *args, **kwargs):
        pass

class LoginView(View):
    def get(self, request):
        return render(request=request, template_name="login.html", context={})
    
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '')  
        password = request.POST.get('password', '')  

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome to Fit4All, {user}")
            if user.is_manager:
                return redirect(reverse('palestra:dashboard'))
            else:
                return redirect(reverse('palestra:profile'))
        else:
            messages.error(request, 'Username or password is incorrect')
            return redirect(reverse('login'))
        
    
class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have successfully logged out")
        return redirect(reverse('homepage'))
    

class RegistrationView(View):
    def get(self, request):
        return render(request=request, template_name="registration.html", context={})

    def post(self, request, *args, **kwargs):
        form = forms.UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Salva l'utente nel database
            login(request, user)
            messages.success(request, f"Welcome to Fit4All, {user}")
            return redirect(reverse('palestra:profile'))
        else:
            functions.print_errors(form, request)
            return render(request, 'registration.html', {'form': form})
        



    






