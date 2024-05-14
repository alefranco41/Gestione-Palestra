from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.urls import reverse
from . import forms
from . import models
from . import context_processors
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import pytz
from datetime import datetime, timedelta

today = datetime.now(pytz.timezone('Europe/Rome'))

day_mapping = {
                'Monday': 0,
                'Tuesday': 1,
                'Wednesday': 2,
                'Thursday': 3,
                'Friday': 4,
                'Saturday': 5,
                'Sunday': 6
            }


def homepage(request):
    context = {
        'gym_name' : 'Fit4All'
    }
    return render(request, 'home.html', context=context)

def get_fitness_goals(trainer_profile):
    fitness_goal_ids = models.TrainerProfile_FitnessGoals.objects.filter(trainerprofile=trainer_profile).values_list('fitnessgoal_id', flat=True)
    fitness_goals = models.FitnessGoal.objects.filter(id__in=fitness_goal_ids)
    fitness_goals = [fitness_goal.name for fitness_goal in fitness_goals]
    return fitness_goals

def get_event_date(event):
    week_day = day_mapping[event.day] 
    date = today.date() - timedelta(days=today.weekday()) + timedelta(days=week_day)
    date = datetime.combine(date, datetime.min.time())
    date = date.replace(hour=event.start_hour) 

    return date

def get_reviews(user):
    reviews = []
    if user.is_authenticated:
        pt_reviews = models.PersonalTrainingReview.objects.all()
        gc_reviews = models.GroupTrainingReview.objects.all()

        for review in pt_reviews:
            review.training_type = models.FitnessGoal.objects.get(id=review.event.training_type).name
        if user.is_manager:
            reviews.extend(pt_reviews)
            reviews.extend(gc_reviews)
        elif user.is_instructor:
            pt_events = models.PersonalTraining.objects.filter(trainer=user)
            gc_events = models.GroupTraining.objects.filter(trainer=user)

            for event in pt_events:
                reviews.extend(pt_reviews.filter(event=event))

            for event in gc_events:
                reviews.extend(gc_reviews.filter(event=event))
        else:
            reviews.extend(pt_reviews.filter(user=user))
            reviews.extend(gc_reviews.filter(user=user))
           
    return reviews


class GymClassesView(View):
    def get(self, request):
        classes = models.GroupTraining.objects.all()
        schedule = {}

        for day in context_processors.week_days:
            schedule[day] = {}
        
        for class_instance in classes:
            schedule[class_instance.day][class_instance.start_hour] = class_instance

        return render(request=request, template_name="classes-schedule.html", context={'schedule': schedule})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request=request, template_name="classes-schedule.html", context={'error': 'You need to login first!!'})
        
        if request.user.is_manager or request.user.is_instructor:
            return render(request=request, template_name="classes-schedule.html", context={'error': 'You are a staff member!!'})
        
        if not models.UserProfile.objects.get(user=request.user).profileInfo():
            return render(request=request, template_name="classes-schedule.html", context={'error':' You must complete your profile first!!'})
        
        class_id = request.POST.get('class_id')
        group_class = models.GroupTraining.objects.get(id=class_id)
            
        if group_class.total_partecipants == group_class.max_participants:
            return render(request=request, template_name="classes-schedule.html", context={'error': 'The class you are trying to access is full!!'})
        
        
        
        try:
            subscription = models.Subscription.objects.get(user=request.user)
            if subscription.expired():
                return render(request=request, template_name="classes-schedule.html", context={'error': 'Your subscription is expired!!'})
            if subscription.plan.name == 'Gym Access Only':
                return render(request=request, template_name="classes-schedule.html", context={'error': "Your subscription does not allow that!!"})
        except models.Subscription.DoesNotExist:
            return render(request=request, template_name="classes-schedule.html", context={'error': 'You are not a member!!'})
        
        try:
            if models.GroupClassReservation.objects.get(user=request.user,group_class=group_class):
                return render(request=request, template_name="classes-schedule.html", context={'error': 'You are already booked in this class!!'})
        except (models.GroupClassReservation.DoesNotExist):
            pass
        

        reservation = models.GroupClassReservation(user=request.user,group_class=group_class)
        
        group_class.total_partecipants += 1
        group_class.save()
        reservation.save()
        return redirect("dashboard")

class TrainerListView(View):
    def get(self, request):
        trainers_users = models.User.objects.filter(is_instructor=True)
        trainers = []
        for trainer_user in trainers_users:
            trainer_profile = models.TrainerProfile.objects.get(user=trainer_user)

            fitness_goals = get_fitness_goals(trainer_profile)

            trainers.append((trainer_profile,fitness_goals))
            
        return render(request=request, template_name="trainer-list.html", context={'trainers':trainers})
        
    


class SubscriptionPlansView(View):
    def get(self, request):
        return render(request=request, template_name="subscription-plans.html", context={})
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request=request, template_name="subscription-plans.html", context={'error':' You need to login first!!'})
        
        if request.user.is_instructor or request.user.is_manager:
            return render(request=request, template_name="subscription-plans.html", context={'error':' You are a staff member!!'})
            
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
            if not user.is_manager:
                return redirect(reverse('profile'))
            else:
                return redirect(reverse('dashboard'))
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
            fitness_goals = get_fitness_goals(user_profile)
            context = {'form': form, 'user_profile':user_profile, 'user_fitness_goals':fitness_goals}
        elif request.user.is_manager:
            context = {}
        else:
            user_profile, created = models.UserProfile.objects.get_or_create(user=request.user)
            form = forms.UserProfileForm(instance=user_profile)
            context = {'form': form, 'user_profile':user_profile}
            try:
                user_subscription = models.Subscription.objects.get(user=request.user)
                plan_id = user_subscription.plan.id
                plan = models.SubscriptionPlan.objects.get(id=plan_id)
                user_subscription.plan_type = plan.plan_type
                context['user_subscription'] = user_subscription
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
        context = {}
        if request.user.is_instructor:
            user_profile = models.TrainerProfile.objects.get(user=request.user)
            fitness_goals = get_fitness_goals(user_profile)
            context = {'user_profile':user_profile, 'trainer_fitness_goals':fitness_goals}
        elif request.user.is_manager:
            pass
        else:
            user_profile = models.UserProfile.objects.get(user=request.user)
            context = {'user_profile':user_profile}
            #form = forms.UserProfileForm(request.POST, instance=user_profile)
        
        return render(request, 'update_profile.html', context)
    
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
            

            if request.user.is_instructor:
                instance = form.save(commit=False)
                fitness_goals_ids = request.POST.getlist('fitness_goals')
                models.TrainerProfile_FitnessGoals.objects.filter(trainerprofile=user_profile).delete()
                fitness_goals = models.FitnessGoal.objects.filter(pk__in=fitness_goals_ids)
                for fitness_goal in fitness_goals:
                    models.TrainerProfile_FitnessGoals(trainerprofile=user_profile, fitnessgoal=fitness_goal).save()

                instance.save()
            else:
                form.save()

            return redirect('profile')  # Reindirizza alla pagina del profilo
        
        return render(request, 'update_profile.html', {'form': form, 'user_profile':user_profile})
    
class Dashboard(View):
    def get_context(self, request):
        context = {}
        context['reviews'] = get_reviews(request.user)
        if request.user.is_manager:
            pass
        else:
            if request.user.is_instructor:
                trainer = models.TrainerProfile.objects.get(user=request.user)
                instructor_group_classes = models.GroupTraining.objects.filter(trainer=trainer)

                booked_group_classes = []
                for group_class in instructor_group_classes:
                    reservation_objects = models.GroupClassReservation.objects.filter(group_class=group_class)
                    
                    if reservation_objects:
                        participants_ids = reservation_objects.values_list('user_id', flat=True)
                        participants = []
                        for partecipant_id in participants_ids:
                            partecipant = models.UserProfile.objects.get(user_id=partecipant_id)
                            partecipant = models.UserProfileSerializer(partecipant).data
                            participants.append(partecipant)

                        reservation_object = reservation_objects.first()
                        reservation_object.participants = participants
                        booked_group_classes.append(reservation_object)

                booked_training_sessions = models.PersonalTraining.objects.filter(trainer=trainer)
            else:
                booked_group_classes = models.GroupClassReservation.objects.filter(user=request.user)
                booked_training_sessions = models.PersonalTraining.objects.filter(user=request.user)
                group_classes_reviews = models.GroupTrainingReview.objects.filter(user=request.user)
                training_sessions_reviews = models.PersonalTrainingReview.objects.filter(user=request.user)
                

            schedule = {}
            for day in context_processors.week_days:
                schedule[day] = {}
                for hour in range(9,19):
                    schedule[day][hour] = None
            
            for booked_group_class in booked_group_classes:
                if not booked_group_class:
                    continue

                group_class = booked_group_class.group_class
                if day_mapping[group_class.day] > today.weekday():
                    group_class.expired = False
                elif day_mapping[group_class.day] == today.weekday():
                    if group_class.start_hour >= today.hour:
                        group_class.expired = False
                    else:
                        group_class.expired = True
                else:
                    group_class.expired = True
                
                if hasattr(group_class, "participants"):
                    group_class.participants = booked_group_class.participants
                
                try:
                    review = group_classes_reviews.get(event=group_class.id)
                except Exception:
                    review = None

                group_class.review = review
                schedule[group_class.day][group_class.start_hour] = group_class
            
            for booked_training_session in booked_training_sessions:
                if request.user.is_instructor:
                    user_profile = models.UserProfile.objects.get(user_id=booked_training_session.user_id)
                    booked_training_session.user_profile = models.UserProfileSerializer(user_profile).data

                booked_training_session.training_type = models.FitnessGoal.objects.get(id=booked_training_session.training_type).name
                if day_mapping[booked_training_session.day] > today.weekday():
                    booked_training_session.expired = False
                elif day_mapping[booked_training_session.day] == today.weekday():
                    if booked_training_session.start_hour >= today.hour:
                        booked_training_session.expired = False
                    else:
                        booked_training_session.expired = True
                else:
                    booked_training_session.expired = True
                
                try:
                    review = training_sessions_reviews.get(event=booked_training_session.id)
                except Exception:
                    review = None
                booked_training_session.review = review
                schedule[booked_training_session.day][booked_training_session.start_hour] = booked_training_session

            context['schedule'] = schedule
        return context

    def get(self, request):
        

        event_type = request.GET.get('event_type')
        event_id =  request.GET.get('event_id')
        if event_id and event_type:
            if event_type == 'group_training':
                event = models.GroupTraining.objects.get(id=event_id)
                review = models.GroupTrainingReview.objects.get(user=request.user, event=event)
                review.delete()
            elif event_type == 'personal_training':
                event = models.PersonalTraining.objects.get(id=event_id)
                review = models.PersonalTrainingReview.objects.get(user=event.user, event=event)
                review.delete()
        
        context = self.get_context(request)
        return render(request=request, template_name="dashboard.html", context=context)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request)
        if not request.user.is_manager and not request.user.is_instructor:
            id_gt = request.POST.get('group_training')
            id_pt = request.POST.get('personal_training')
            try:
                if id_gt:
                    group_training = models.GroupTraining.objects.get(id=id_gt)
                    models.GroupClassReservation.objects.get(group_class_id=group_training.id, user_id=request.user.id).delete()
                    group_training.total_partecipants -= 1
                    group_training.save()
                    context['message'] = 'The Group Class reservation has been cancelled'
                else:
                    models.PersonalTraining.objects.get(id=id_pt).delete()
                    context['message'] = 'The training session has been cancelled'
            except (models.PersonalTraining.DoesNotExist, models.GroupClassReservation.DoesNotExist):
                pass
        return render(request=request, template_name="dashboard.html", context=context)
    
class NewGroupTraining(View):    
    def get(self, request):
        if not request.user.is_manager:
            return redirect('dashboard')  
        
        form = forms.GroupTrainingForm()
        trainers = models.TrainerProfile.objects.all()

        return render(request, 'create_group_training.html', {'form': form, 'trainers':trainers})
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = forms.GroupTrainingForm(request.POST, request.FILES)
            if form.is_valid():
                existing_courses = models.GroupTraining.objects.filter(day=form.cleaned_data.get('day'), start_hour=form.cleaned_data.get('start_hour'))
                if not existing_courses:
                    form.save()
                else:
                    trainers = models.TrainerProfile.objects.all()
                    return render(request, 'create_group_training.html', {'form': form, 'trainers':trainers, 'error':'There is already a group class in that time frame!!'})
            else:
                print(form.errors)
        return redirect('dashboard')  
    

class EditGroupTraining(View):
    def get(self, request, course_id):
        if not request.user.is_manager:
            return redirect('dashboard')  
        
        class_item = models.GroupTraining.objects.get(id=course_id)
        form = forms.GroupTrainingForm()
        trainers = models.TrainerProfile.objects.all()

        
        return render(request, 'edit_group_training.html', {'class':class_item, 'form':form, 'trainers':trainers})
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            class_id = kwargs.get('course_id')
            class_item = models.GroupTraining.objects.get(id=class_id)
            form = forms.GroupTrainingForm(request.POST, request.FILES, instance=class_item)

            if form.is_valid():
                form.save()
            
        return redirect('classes-schedule') 
    

class BookWorkout(View):
    def get(self, request, pt_id):
        
        trainer = models.TrainerProfile.objects.get(id=pt_id)

        trainer_fitness_goals = get_fitness_goals(trainer)
        
        today_day_name = today.strftime("%A")
        today_hour = today.hour 

        available_days = [context_processors.week_days[i] for i in range(context_processors.week_days.index(today_day_name), len(context_processors.week_days))]
        available_hours_today = [i for i in range(9,19) if i > today_hour]

        personal_trainings = models.PersonalTraining.objects.filter(trainer_id=pt_id)
        group_trainings = models.GroupTraining.objects.filter(trainer_id=pt_id)

        availability = {}
        for day in available_days:
            if day == today_day_name:
                availability[day] = available_hours_today
                continue
            
            availability[day] = [i for i in range(9,19)]
            
            for group_training in group_trainings:
                if group_training.day == day:
                    availability[day].remove(group_training.start_hour)
            
            
            for personal_training in personal_trainings:
                if personal_training.day == day:
                    availability[day].remove(personal_training.start_hour)

        context = {'trainer':trainer, 'trainer_fitness_goals':trainer_fitness_goals, 'availability':availability, 'form':forms.PersonalTrainingForm()}

        if not request.user.is_authenticated:
            context['error'] = 'You need to login first!!'
        elif request.user.is_manager or request.user.is_instructor:
            context['error'] = 'You are a staff member!!'

        return render(request, template_name="book-workout.html", context=context)
    
    def post(self, request, *args, **kwargs):
        form = forms.PersonalTrainingForm(data=request.POST)
        
        if form.is_valid():
            form.save()
        
        return redirect("dashboard")
    

def get_LeaveReview_context(request=None, event_id=None, event_type=None):
        context = {}
        if not event_id or not event_type:
            event_id = request.GET.get('event_id')
            event_type = request.GET.get('event_type')

        
        if event_type == 'group_training':
            event = models.GroupTraining.objects.get(id=event_id)
            event.date = get_event_date(event)
            try:
                context['review'] = models.GroupTrainingReview.objects.get(user=request.user, event=event)
            except Exception:
                pass
        elif event_type == 'personal_training':
            event = models.PersonalTraining.objects.get(id=event_id)
            try:
                context['review'] = models.PersonalTrainingReview.objects.get(user=event.user, event=event)
            except Exception:
                pass

            event.date = get_event_date(event)
        else:
            event = None

        context['event'] = event
        
        return context


class LeaveReview(View):
    
    def post(self, request, *args, **kwargs):
        
        context = get_LeaveReview_context(request)
        event_type = request.GET.get('event_type')

        if event_type == 'group_training':
            form = forms.GroupTrainingReviewForm(request.POST)
        elif event_type == 'personal_training':
            form = forms.PersonalTrainingReviewForm(request.POST)

        context['form'] = form

        if form.is_valid():
            form.save()
            return redirect("dashboard")
        else:
            return render(request=request, template_name="leave-review.html", context=context)
    

    def get(self, request):
        context = get_LeaveReview_context(request)
        return render(request=request, template_name="leave-review.html", context=context)
    
class EditReview(View):
    def get(self, request):
        context = get_LeaveReview_context(request)
        return render(request=request, template_name="edit-review.html", context=context)

    def post(self, request, *args, **kwargs):
        user = request.POST.get('user')
        event = request.POST.get('event')
        event_type = request.POST.get('event_type')
        context = get_LeaveReview_context(request)
        
        if event_type == 'personal_training':
            form = forms.PersonalTrainingReviewForm(request.POST)
            old_review = models.PersonalTrainingReview.objects.get(user=user, event=event)
            
        elif event_type == 'group_training':
            form = forms.GroupTrainingReviewForm(request.POST)
            old_review = models.GroupTrainingReview.objects.get(user=user, event=event)
        
        if form.is_valid: 
            form.save()
            old_review.delete()
            return redirect("dashboard")
        
        context['review'] = old_review
        return render(request=request, template_name="edit-review.html", context=context)