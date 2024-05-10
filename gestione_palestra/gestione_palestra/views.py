from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.urls import reverse
from . import forms
from . import models
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.db import connection


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
        trainers_users = models.User.objects.filter(is_instructor=True)
        trainers = []
        for trainer_user in trainers_users:
            trainer_profile = models.TrainerProfile.objects.get(user=trainer_user)
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT fg.name FROM gestione_palestra_fitnessgoal AS fg WHERE fg.id IN (SELECT fitnessgoal_id FROM gestione_palestra_trainerprofile_fitness_goals WHERE trainerprofile_id = {trainer_profile.id})")
                fitness_goals = [row[0] for row in cursor.fetchall()]

            trainers.append((trainer_profile,fitness_goals))
            
        return render(request=request, template_name="trainer-list.html", context={'trainers':trainers})

class SubscriptionPlansView(View):
    def get(self, request):
        return render(request=request, template_name="subscription-plans.html", context={})
    
    def post(self, request, *args, **kwargs):
        if request.user.is_instructor:
            return render(request=request, template_name="subscription-plans.html", context={'error':' You are a personal trainer!!'})
        
        old_subscription = None
        if models.Subscription.objects.filter(user=request.user).exists(): #utente già abbonato, assicurarsi che non sia scaduto
            subscription = models.Subscription.objects.get(user=request.user)
            
            if not subscription.expired():
                return render(request=request, template_name="subscription-plans.html", context={'error':' You already have a plan that is still valid!!'})
            else:
                old_subscription = subscription 

        user = models.UserProfile.objects.get(user=request.user)
        if not user.profileInfo():
            return render(request=request, template_name="subscription-plans.html", context={'error':' You must complete your profile first!!'})
        
        plan = models.SubscriptionPlan.objects.get(id=request.POST.get('plan_id'))
        duration = int(request.POST.get('duration_selected'))
        
        start_date = datetime.now()
        end_date = start_date + relativedelta(months=duration)

        duration_discounts = models.DurationDiscount.objects.filter(subscription_plan=plan)
        duration_discount = duration_discounts.get(duration=duration)
        
        if duration_discount:
            discount_percentage = duration_discount.discount_percentage
        else:
            discount_percentage = 0
        
        age_discount = 0
        age_reduction = False
        if user.ageReduction():
            age_discount = plan.age_discount
            age_reduction = True

        price = plan.monthly_price * (Decimal(1) - Decimal(discount_percentage) / Decimal(100)) - age_discount

        if old_subscription:
            old_subscription.plan = plan
            old_subscription.monthly_price = price
            old_subscription.start_date = start_date
            old_subscription.end_date = end_date
            old_subscription.age_reduction = age_reduction
            old_subscription.save()
        else:
            sub = models.Subscription(user=request.user, plan=plan, monthly_price=price, start_date=start_date, end_date=end_date, age_reduction=age_reduction)
            sub.save()

        return redirect('profile')


class LoginView(View):
    def get(self, request):
        return render(request=request, template_name="login.html", context={})
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '')  
        password = request.POST.get('password', '')  

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('profile'))
        else:
            error_message = "Username or password is incorrect."
            return render(request=request, template_name="login.html", context={'error_message': error_message})
        
    
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
            return HttpResponseRedirect(reverse('profile'))
        else:
            return render(request, 'registration.html', {'form': form})
    

class ProfileView(View):
    def get(self, request):
        if request.user.is_instructor:
            user_profile, created = models.TrainerProfile.objects.get_or_create(user=request.user)
            form = forms.TrainerProfileForm(instance=user_profile)
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT fg.name FROM gestione_palestra_fitnessgoal AS fg WHERE fg.id IN (SELECT fitnessgoal_id FROM gestione_palestra_trainerprofile_fitness_goals WHERE trainerprofile_id = {user_profile.id})")
                fitness_goals = [row[0] for row in cursor.fetchall()]
            context = {'form': form, 'user_profile':user_profile, 'user_fitness_goals':fitness_goals}
        elif request.user.is_manager:
            pass
        else:
            user_profile = models.UserProfile.objects.get(user=request.user)
            form = forms.UserProfileForm(instance=user_profile)
            try:
                user_subscription = models.Subscription.objects.get(user=request.user)
                plan_id = user_subscription.plan.id
                plan = models.SubscriptionPlan.objects.get(id=plan_id)
                user_subscription.plan_type = plan.plan_type
                context = {'form': form, 'user_profile':user_profile, 'user_subscription':user_subscription}
            except Exception:
                pass
                

        return render(request=request, template_name='profile.html', context=context)

    def post(self, request, *args, **kwargs):
        if request.user.is_instructor:
            form = forms.TrainerProfileForm(request.POST)
            user_profile = get_object_or_404(models.TrainerProfile, user=request.user)
        elif request.user.is_manager:
            pass
        else:
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
        if request.user.is_instructor:
            user_profile = models.TrainerProfile.objects.get(user=request.user)
            form = forms.TrainerProfileForm(request.POST, instance=user_profile)
            
            
        elif request.user.is_manager:
            pass
        else:
            user_profile = models.UserProfile.objects.get(user=request.user)
            form = forms.UserProfileForm(request.POST, instance=user_profile)
            
        return render(request, 'update_profile.html', {'form': form, 'user_profile':user_profile})
    
    def post(self, request, *args, **kwargs):
        if request.user.is_instructor:
            user_profile = models.TrainerProfile.objects.get(user=request.user)
            form = forms.TrainerProfileForm(request.POST, request.FILES, instance=user_profile)

        elif request.user.is_manager:
            pass
        else:
            user_profile = models.UserProfile.objects.get(user=request.user)
            form = forms.UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        
        if form.is_valid():
            instance = form.save(commit=False)

            if request.user.is_instructor:
                fitness_goals_ids = request.POST.getlist('fitness_goals')
                fitness_goals_objects = models.FitnessGoal.objects.filter(pk__in=fitness_goals_ids)
                instance.fitness_goals.set(fitness_goals_objects)
                instance.save()

            return redirect('profile')  # Reindirizza alla pagina del profilo
        
        return render(request, 'update_profile.html', {'form': form, 'user_profile':user_profile})
    
class Dashboard(View):
    def get(self, request):
        return render(request=request, template_name="dashboard.html", context={})

    def post(self, request, *args, **kwargs):
        pass