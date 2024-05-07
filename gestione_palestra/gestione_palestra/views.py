from django.shortcuts import render
from django.views import View


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
        username = request.POST.get('username', '')  # Ottiene il valore del campo 'username' dal form
        password = request.POST.get('password', '')  # Ottiene il valore del campo 'password' dal form
        
        return render(request=request, template_name="login.html", context={})
        

class LogoutView(View):
    def get(self, request):
        return render(request=request, template_name="logout.html", context={})

class RegistrationView(View):
    def get(self, request):
        return render(request=request, template_name="registration.html", context={})