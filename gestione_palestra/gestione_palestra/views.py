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
from datetime import datetime, timedelta
from gestione_palestra.context_processors import today

def homepage(request):
    return render(request, 'home.html', context={})

def get_fitness_goals(trainer_profile):
    fitness_goal_ids = models.TrainerProfile_FitnessGoals.objects.filter(trainerprofile=trainer_profile).values_list('fitnessgoal_id', flat=True)
    fitness_goals = models.FitnessGoal.objects.filter(id__in=fitness_goal_ids)
    fitness_goals = [fitness_goal.name for fitness_goal in fitness_goals]
    return fitness_goals

def get_event_date(event):
    week_day = context_processors.day_mapping[event.day] 
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
            try:
                trainer = models.TrainerProfile.objects.get(user=user)
            except models.TrainerProfile.DoesNotExist:
                pass
            else:
                pt_events = models.PersonalTraining.objects.filter(trainer=trainer)
                gc_events = models.GroupTraining.objects.filter(trainer=trainer)

                for event in pt_events:
                    reviews.extend(pt_reviews.filter(event=event))

                for event in gc_events:
                    reviews.extend(gc_reviews.filter(event=event))
        else:
            reviews.extend(pt_reviews.filter(user=user))
            reviews.extend(gc_reviews.filter(user=user))
           
    return reviews


class GymClassesView(View):
    def get_context(self, request):
        context = {}
        schedule = {}
        classes = models.GroupTraining.objects.all()

        for day in context_processors.week_days:
            schedule[day] = {}
        
        for class_instance in classes:
            class_instance.ended = class_instance.ended()
            schedule[class_instance.day][class_instance.start_hour] = class_instance

        context['schedule'] = schedule
        return context
    
    def get(self, request):
        context = self.get_context(request)

        return render(request=request, template_name="classes-schedule.html", context=context)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request)

        if not request.user.is_authenticated:
            context['error'] = 'You need to login first!!'
            return render(request=request, template_name="classes-schedule.html", context=context)
        
        if request.user.is_manager or request.user.is_instructor:
            context['error'] = 'You are a staff member!!'
            return render(request=request, template_name="classes-schedule.html", context=context)
        
        if not models.UserProfile.objects.get(user=request.user).profileInfo():
            context['error'] = 'You must complete your profile first!!'
            return render(request=request, template_name="classes-schedule.html", context=context)
        
        class_id = request.POST.get('class_id')
        group_class = models.GroupTraining.objects.get(id=class_id)
        
        if group_class.ended():
            context['error'] = 'This group class has ended, come back the next week!!'
            return render(request=request, template_name="classes-schedule.html", context=context)
        
        if group_class.total_partecipants == group_class.max_participants:
            context['error'] = 'The class you are trying to access is full!!'
            return render(request=request, template_name="classes-schedule.html", context=context)
        
        try:
            subscription = models.Subscription.objects.get(user=request.user)
            if subscription.expired():
                context['error'] = 'Your subscription has expired!!'
                return render(request=request, template_name="classes-schedule.html", context=context)
            if subscription.plan.name == 'Gym Access Only':
                context['errror'] = f'Your subscription plan ({subscription.plan.name}) does not allow that!!'
                return render(request=request, template_name="classes-schedule.html", context=context)
        except models.Subscription.DoesNotExist:
            context['error'] = 'You are not a member!!'
            return render(request=request, template_name="classes-schedule.html", context=context)
        
        
        try:
            if models.GroupClassReservation.objects.get(user=request.user,group_class=group_class):
                context['error'] = 'You are already booked in this class!!'
                return render(request=request, template_name="classes-schedule.html", context=context)
        except models.GroupClassReservation.DoesNotExist:
            pass

        try:
            if models.PersonalTraining.objects.get(user=request.user,start_hour=group_class.start_hour, day=group_class.day):
                context['error'] = f'You have an upcoming personal training session already booked for {group_class.day} at {group_class.start_hour}!!'
                return render(request=request, template_name="classes-schedule.html", context=context)
        except (models.PersonalTraining.DoesNotExist):
            pass
        
        reservation = models.GroupClassReservation(user=request.user,group_class=group_class)
        
        group_class.total_partecipants += 1
        group_class.save()
        reservation.save()
        return redirect(reverse("dashboard"))

class TrainerListView(View):
    def get(self, request):
        trainers_users = models.User.objects.filter(is_instructor=True)
        trainers = []
        for trainer_user in trainers_users:
            try:
                trainer_profile = models.TrainerProfile.objects.get(user=trainer_user)
            except models.TrainerProfile.DoesNotExist:
                continue
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
        try:
            subscription = models.Subscription.objects.get(user=request.user)
        except models.Subscription.DoesNotExist:
            pass
        else:
            if not subscription.expired():
                return render(request=request, template_name="subscription-plans.html", context={'error':' You already have a plan that is still valid!!'})
            else:
                old_subscription = subscription 

        try:
            user = models.UserProfile.objects.get(user=request.user)
        except models.UserProfile.DoesNotExist:
            return render(request=request, template_name="subscription-plans.html", context={'error':' You must complete your profile first!!'})
        
        if not user.profileInfo():
            return render(request=request, template_name="subscription-plans.html", context={'error':' You must complete your profile first!!'})
        
        try:
            plan = models.SubscriptionPlan.objects.get(id=request.POST.get('plan_id'))
        except models.SubscriptionPlan.DoesNotExist:
            return render(request=request, template_name="subscription-plans.html", context={'error':' The plan that you selected is currently unavailable!!'})
        
        duration = int(request.POST.get('duration_selected'))
        
        start_date = datetime.now()
        end_date = start_date + relativedelta(months=duration)

        duration_discounts = models.DurationDiscount.objects.filter(subscription_plan=plan)
        
        try:
            duration_discount = duration_discounts.get(duration=duration)
        except  models.DurationDiscount.DoesNotExist:
            discount_percentage = 0
        else:
            discount_percentage = duration_discount.discount_percentage

        
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

        return redirect(reverse('profile'))


class LoginView(View):
    def get(self, request):
        return render(request=request, template_name="login.html", context={})
    
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '')  
        password = request.POST.get('password', '')  

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            if user.is_manager:
                return redirect(reverse('dashboard'))
            else:
                return redirect(reverse('profile'))
        else:
            return render(request=request, template_name="login.html", context={'error_message': 'Username or password is incorrect.'})
        
    
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('homepage'))
    

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
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if request.user.is_instructor:
            user_profile, created = models.TrainerProfile.objects.get_or_create(user=request.user)
            form = forms.TrainerProfileForm(instance=user_profile)
            fitness_goals = get_fitness_goals(user_profile)
            context = {'form': form, 'user_profile':user_profile, 'user_fitness_goals':fitness_goals}
        elif request.user.is_manager:
            return redirect(reverse('dashboard'))
        else:
            user_profile, created = models.UserProfile.objects.get_or_create(user=request.user)
            form = forms.UserProfileForm(instance=user_profile)
            context = {'form': form, 'user_profile':user_profile}
            try:
                user_subscription = models.Subscription.objects.get(user=request.user)
                plan_id = user_subscription.plan.id
                plan = models.SubscriptionPlan.objects.get(id=plan_id)
            except (models.Subscription.DoesNotExist,models.SubscriptionPlan.DoesNotExist):
                pass
            else:
                user_subscription.plan_type = plan.plan_type
                context['user_subscription'] = user_subscription

        return render(request=request, template_name='profile.html', context=context)



class UpdateProfile(View):
    def get(self, request):
        context = {}
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if request.user.is_instructor:
            user_profile = models.TrainerProfile.objects.get(user=request.user)
            fitness_goals = get_fitness_goals(user_profile)
            context = {'user_profile':user_profile, 'trainer_fitness_goals':fitness_goals}
        elif request.user.is_manager:
            return redirect(reverse('dashboard'))
        else:
            user_profile = models.UserProfile.objects.get(user=request.user)
            context = {'user_profile':user_profile}
        
        return render(request, 'update-profile.html', context)
    
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

            return redirect(reverse('profile'))  # Reindirizza alla pagina del profilo
        
        return render(request, 'update-profile.html', {'form': form, 'user_profile':user_profile})
    
class Dashboard(View):
    def get_context(self, request):
        context = {}
        group_classes_reviews = None
        training_sessions_reviews = None

        context['reviews'] = get_reviews(request.user)
        if request.user.is_manager:
            pass
        else:
            if request.user.is_instructor:
                try:
                    trainer = models.TrainerProfile.objects.get(user=request.user)
                except models.TrainerProfile.DoesNotExist:
                    context['error'] = f"personal trainer not found: {request.user.username}"
                    return context
                

                instructor_group_classes = models.GroupTraining.objects.filter(trainer=trainer)

                booked_group_classes = []
                for group_class in instructor_group_classes:
                    reservation_objects = models.GroupClassReservation.objects.filter(group_class=group_class)
                    
                    if reservation_objects:
                        participants_ids = reservation_objects.values_list('user_id', flat=True)
                        participants = []
                        for partecipant_id in participants_ids:
                            try:
                                partecipant = models.UserProfile.objects.get(user_id=partecipant_id)
                            except models.UserProfile.DoesNotExist:
                                continue
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
                group_class = booked_group_class.group_class
                if context_processors.day_mapping[group_class.day] > today.weekday():
                    group_class.expired = False
                elif context_processors.day_mapping[group_class.day] == today.weekday():
                    if group_class.start_hour >= today.hour:
                        group_class.expired = False
                    else:
                        group_class.expired = True
                else:
                    group_class.expired = True
                
                if hasattr(group_class, "participants"):
                    group_class.participants = booked_group_class.participants
                
                review = None
                if group_classes_reviews:
                    try:
                        review = group_classes_reviews.get(event=group_class.id)
                    except models.GroupTrainingReview.DoesNotExist:
                        review = None

                group_class.review = review
                schedule[group_class.day][group_class.start_hour] = group_class
            
            for booked_training_session in booked_training_sessions:
                if request.user.is_instructor:
                    try:
                        user_profile = models.UserProfile.objects.get(user_id=booked_training_session.user_id)
                    except models.UserProfile.DoesNotExist:
                        continue

                    booked_training_session.user_profile = models.UserProfileSerializer(user_profile).data
                
                try:
                    booked_training_session.training_type = models.FitnessGoal.objects.get(id=booked_training_session.training_type).name
                except models.FitnessGoal.DoesNotExist:
                    booked_training_session.training_type = None

                if context_processors.day_mapping[booked_training_session.day] > today.weekday():
                    booked_training_session.expired = False
                elif context_processors.day_mapping[booked_training_session.day] == today.weekday():
                    if booked_training_session.start_hour >= today.hour:
                        booked_training_session.expired = False
                    else:
                        booked_training_session.expired = True
                else:
                    booked_training_session.expired = True
                
                review = None
                if training_sessions_reviews:
                    try:
                        review = training_sessions_reviews.get(event=booked_training_session.id)
                    except models.PersonalTrainingReview.DoesNotExist:
                        review = None
                booked_training_session.review = review
                schedule[booked_training_session.day][booked_training_session.start_hour] = booked_training_session

            context['schedule'] = schedule
        return context

    def get(self, request):
        context = {}
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        event_type = request.GET.get('event_type')
        event_id =  request.GET.get('event_id')
        if event_id and event_type:
            if event_type == 'group_training':
                try:
                    event = models.GroupTraining.objects.get(id=event_id)
                    review = models.GroupTrainingReview.objects.get(user=request.user, event=event)
                    review.delete()
                except (models.GroupTraining.DoesNotExist, models.GroupTrainingReview.DoesNotExist):
                    context['error'] = f'Group training review not found with user: {request.user}'
            elif event_type == 'personal_training':
                try:
                    event = models.PersonalTraining.objects.get(id=event_id)
                    review = models.PersonalTrainingReview.objects.get(user=event.user, event=event)
                    review.delete()
                except (models.PersonalTraining.DoesNotExist, models.PersonalTrainingReview.DoesNotExist):
                    context['error'] = f'Personal training review not found with user: {request.user}'
        
        context.update(self.get_context(request))
        return render(request=request, template_name="dashboard.html", context=context)

    def post(self, request, *args, **kwargs):
        context = {}
        if not request.user.is_manager and not request.user.is_instructor:
            id_gt = request.POST.get('group_training')
            id_pt = request.POST.get('personal_training')
            try:
                if id_gt:
                    group_training = models.GroupTraining.objects.get(id=id_gt)
                    models.GroupClassReservation.objects.get(group_class_id=group_training.id, user_id=request.user.id).delete()
                    group_training.total_partecipants -= 1
                    group_training.save()
                    context['error'] = 'The Group Class reservation has been cancelled'
                else:
                    models.PersonalTraining.objects.get(id=id_pt).delete()
                    context['error'] = 'The training session has been cancelled'
            except (models.PersonalTraining.DoesNotExist, models.GroupClassReservation.DoesNotExist, models.GroupTraining.DoesNotExist):
                context['error'] = 'Event not found'
        context.update(self.get_context(request))
        return render(request=request, template_name="dashboard.html", context=context)
    
class NewGroupTraining(View):    
    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_manager:
            return redirect(reverse('login'))  
        
        form = forms.GroupTrainingForm()
        trainers = models.TrainerProfile.objects.all()

        return render(request, 'create-group-training.html', {'form': form, 'trainers':trainers})
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = forms.GroupTrainingForm(request.POST, request.FILES)
            trainers = models.TrainerProfile.objects.all()
            if form.is_valid():
                existing_courses = models.GroupTraining.objects.filter(day=form.cleaned_data.get('day'), start_hour=form.cleaned_data.get('start_hour'))
                if not existing_courses:
                    form.save()
                else:   
                    return render(request, 'create-group-training.html', {'form': form, 'trainers':trainers, 'error':'There is already a group class in that time frame!!'})
            else:
                return render(request, 'create-group-training.html', {'form': form, 'trainers':trainers})
            
        return redirect(reverse('dashboard'))  
    

class EditGroupTraining(View):
    def get(self, request, course_id):
        context = {}
        
        form = forms.GroupTrainingForm()
        trainers = models.TrainerProfile.objects.all()
        context['form'] = form
        context['trainers'] = trainers

        if not request.user.is_authenticated or not request.user.is_manager:
            return redirect(reverse('dashboard'))  
        try:
            class_item = models.GroupTraining.objects.get(id=course_id)
        except models.GroupTraining.DoesNotExist:
            context['error'] = f"The group training that you are trying to edit (id = {course_id}) doesn't exist"
            return context
        else:
            context['class'] = class_item

        return render(request, 'edit-group-training.html', context)
    
    def post(self, request, *args, **kwargs):
        class_id = kwargs.get('course_id')
        trainers = models.TrainerProfile.objects.all()
        if class_id:
            try:
                class_item = models.GroupTraining.objects.get(id=class_id)
            except models.GroupTraining.DoesNotExist:
                return render(request, 'edit-group-training.html', {'class':None, 'form':form, 'trainers':trainers, 'error':'The class you are trying to edit does not exist!!'})
            else:
                form = forms.GroupTrainingForm(request.POST, request.FILES, instance=class_item)
                if form.is_valid():
                    form.save()
                else:
                    return render(request, 'edit-group-training.html', {'class':class_item, 'form':form, 'trainers':trainers})
        else:
            return render(request, 'edit-group-training.html', {'class': None, 'form': form, 'trainers': trainers, 'error': "You need to specify the 'course_id' parameter."})

        
        return redirect(reverse('classes-schedule'))  
    

class BookWorkout(View):
    def get_context(self, request, pt_id):
        context = {}
        try:
            trainer = models.TrainerProfile.objects.get(id=pt_id)
        except models.TrainerProfile.DoesNotExist:
            context['error'] = "The selected personal trainer couldn't be found"
            return context
        
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
                if not available_hours_today:
                    continue

                availability[day] = available_hours_today
                continue
            
            availability[day] = [i for i in range(9,19)]
            
            for group_training in group_trainings:
                if group_training.day == day:
                    availability[day].remove(group_training.start_hour)
            
            
            for personal_training in personal_trainings:
                if personal_training.day == day:
                    availability[day].remove(personal_training.start_hour)

        context['trainer'] = trainer
        context['trainer_fitness_goals'] = trainer_fitness_goals
        context['availability'] = availability
        context['form'] = forms.PersonalTrainingForm()

        if request.method == 'POST':
            if not request.user.is_authenticated:
                context['error'] = 'You need to login first!!'
                return context
            elif request.user.is_manager or request.user.is_instructor:
                context['error'] = 'You are a staff member!!'
                return context
            
        if request.method == 'POST':
            try:
                day = request.POST.get('day')
                if day not in models.PersonalTraining.DAY_CHOICES:
                    context['error'] = f"{day} is an invalid day choice!!"
                    return context
                
                hour = request.POST.get('start_hour')
                if hour not in models.PersonalTraining.START_HOUR_CHOICES:
                    context['error'] = f"{hour} is an invalid hour choice!!"
                    return context
                
                user = request.POST.get('user')
                group_classes = models.GroupTraining.objects.filter(day=day, start_hour=hour)
                for group_class in group_classes:
                    if not group_class.ended():
                        if models.GroupClassReservation.objects.get(user=user, group_class=group_class):
                            context['error'] = f'You have an upcoming group class training session already booked for {group_class.day} at {group_class.start_hour}!!'
                            return context
            except (models.GroupClassReservation.DoesNotExist, models.GroupTraining.DoesNotExist):
                context['error'] = f"Group class reservation not found for user: {user}!!"
                return context
                
        return context
    
    def get(self, request, pt_id):
        context = self.get_context(request, pt_id)
        return render(request, template_name="book-workout.html", context=context)
    
    def post(self, request, *args, **kwargs):
        form = forms.PersonalTrainingForm(data=request.POST)
        context = self.get_context(request, request.POST.get('trainer'))

        if context.get('error'):
            return render(request, template_name="book-workout.html", context=context)
        if form.is_valid():
            form.save()
        else:
            return render(request, template_name="book-workout.html", context=context)
        
        return redirect(reverse('dashboard'))
    

def get_LeaveReview_context(request=None, event_id=None, event_type=None):
        context = {}
        if not event_id or not event_type:
            event_id = request.GET.get('event_id')
            event_type = request.GET.get('event_type')

        
        if event_type == 'group_training':
            try:
                event = models.GroupTraining.objects.get(id=event_id)
            except models.GroupTraining.DoesNotExist:
                context['errror'] = f"Group training not found with id: {event_id}"
                return context
            
            event.date = get_event_date(event)
            try:
                context['review'] = models.GroupTrainingReview.objects.get(user=request.user, event=event)
            except models.GroupTrainingReview.DoesNotExist:
                context['error'] = f"Review not found with user: {request.user.username} and group training id: {event.id}"
                return context
            
        elif event_type == 'personal_training':
            event = models.PersonalTraining.objects.get(id=event_id)
            try:
                context['review'] = models.PersonalTrainingReview.objects.get(user=event.user, event=event)
            except models.PersonalTrainingReview.DoesNotExist:
                context['error'] = f"Personal training review not found with user: {request.user.username}"
                return context
            
            event.date = get_event_date(event)
        else:
            context['error'] = f'invalid event type: {event_type}'
            event = None

        context['event'] = event
        
        return context


class LeaveReview(View):
    def post(self, request, *args, **kwargs):
        context = get_LeaveReview_context(request)
        event_type = request.GET.get('event_type')

        if event_type == 'group_training':
            form = forms.GroupTrainingReviewForm(request.POST)
            context['form'] = form
        elif event_type == 'personal_training':
            form = forms.PersonalTrainingReviewForm(request.POST)
            context['form'] = form
        else:
            context['error'] = f'invalid event type: {event_type}'
        
        if not request.user.is_authenticated:
            context['error'] = 'You need to login first'
        
        if request.user.is_manager or request.user.is_instructor:
            context['error'] = 'You are a staff member'

        if context['error']:
            return render(request=request, template_name="leave-review.html", context=context)
        
        if form.is_valid():
            form.save()
            return redirect(reverse('dashboard'))
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
        old_review = None

        if event_type == 'personal_training':
            form = forms.PersonalTrainingReviewForm(request.POST)
            try:
                old_review = models.PersonalTrainingReview.objects.get(user=user, event=event)
            except models.PersonalTrainingReview.DoesNotExist:
                context['error'] = f"Couldn't edit the review!!"
            
        elif event_type == 'group_training':
            form = forms.GroupTrainingReviewForm(request.POST)
            try:
                old_review = models.GroupTrainingReview.objects.get(user=user, event=event)
            except models.GroupTrainingReview.DoesNotExist:
                context['error'] = f"Couldn't edit the review!!"

        else:
            context['error'] = f"Invalid choice for event_type: {event_type}"

        if form.is_valid and old_review: 
            form.save()
            old_review.delete()
            return redirect(reverse("dashboard"))
        
        context['review'] = old_review
        return render(request=request, template_name="edit-review.html", context=context)