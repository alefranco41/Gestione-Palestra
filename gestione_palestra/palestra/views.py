from palestra import forms, models
from management.models import GroupTraining, SubscriptionPlan, DurationDiscount
from utils import functions, global_variables
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from datetime import datetime


"""
Controllare che l'utente abbia effettivamente partecipato all'evento quando lascia una recensione
"""

def get_reviews(user):
    reviews = []
    if user.is_authenticated:
        pt_reviews = models.PersonalTrainingReview.objects.all()
        gc_reviews = models.GroupTrainingReview.objects.all()

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
                gc_events = GroupTraining.objects.filter(trainer=trainer)

                for event in pt_events:
                    reviews.extend(pt_reviews.filter(event=event))

                for event in gc_events:
                    reviews.extend(gc_reviews.filter(event=event))
        else:
            reviews.extend(pt_reviews.filter(user=user))
            for review in reviews:
                review.training_type = models.FitnessGoal.objects.get(id=review.event.training_type).name
                
            reviews.extend(gc_reviews.filter(user=user))
        
        for review in reviews:
            if isinstance(review, models.GroupTrainingReview):
                review.event_type = "group_training"
            else:
                review.event_type = "personal_training"
            
    return reviews

class GymClassesView(View):
    def get_context(self, request):
        print(request)
        context = {}
        schedule = {}
        classes = GroupTraining.objects.all()

        for day in global_variables.week_days:
            schedule[day] = {}
        
        for class_instance in classes:
            class_instance.expired = class_instance.expired()
            schedule[class_instance.day][class_instance.start_hour] = class_instance

        context['schedule'] = schedule
        return context
    
    def get(self, request):
        context = self.get_context(request)

        return render(request=request, template_name="classes-schedule.html", context=context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must login first')
            return redirect(reverse('palestra:classes-schedule'))
        
        if request.user.is_manager or request.user.is_instructor:
            messages.error(request, 'You are a staff member')
            return redirect(reverse('palestra:classes-schedule'))
        
        try:
            user_profile = models.UserProfile.objects.get(user=request.user).profileInfo()
        except models.UserProfile.DoesNotExist:
            messages.error(request, 'You must complete your profile first')
            return redirect(reverse('palestra:classes-schedule'))
        
        class_id = request.POST.get('class_id')
        group_class = GroupTraining.objects.get(id=class_id)
        
        if group_class.expired():
            messages.error(request, 'This group class has ended, come back the next week')
            return redirect(reverse('palestra:classes-schedule'))
        
        if group_class.total_partecipants == group_class.max_participants:
            messages.error(request, 'The group class you are trying to join is full')
            return redirect(reverse('palestra:classes-schedule'))
        
        try:
            subscription = models.Subscription.objects.get(user=request.user)
            if subscription.expired():
                messages.error(request, 'Your subscription has expired')
                return redirect(reverse('palestra:subscription-plans'))
            if subscription.plan.plan_type == 'WEIGHTS':
                messages.error(request, f'Your subscription plan ({subscription.plan.name}) does not allow that')
                return redirect(reverse('palestra:classes-schedule'))
        except models.Subscription.DoesNotExist:
            messages.error(request, 'You are not a member')
            return redirect(reverse('palestra:subscription-plans'))
        
        
        try:
            if models.GroupClassReservation.objects.get(user=request.user,group_class=group_class):
                messages.error(request, 'You are already booked in this class')
                return redirect(reverse('palestra:classes-schedule'))
        except models.GroupClassReservation.DoesNotExist:
            pass

        try:
            if models.PersonalTraining.objects.get(user=request.user,start_hour=group_class.start_hour, day=group_class.day):
                messages.error(request, f'You have an upcoming personal training session already booked for {group_class.day} at {group_class.start_hour}')
                return redirect(reverse('palestra:classes-schedule'))
        except (models.PersonalTraining.DoesNotExist):
            pass
        
        reservation = models.GroupClassReservation(user=request.user,group_class=group_class)
        
        group_class.save()
        reservation.save()
        messages.success(request, 'Group class joined successfully')
        return redirect(reverse('palestra:dashboard'))

class TrainerListView(View):
    def get(self, request):
        trainers_users = models.User.objects.filter(is_instructor=True)
        trainers = []
        for trainer_user in trainers_users:
            try:
                trainer_profile = models.TrainerProfile.objects.get(user=trainer_user)
            except models.TrainerProfile.DoesNotExist:
                continue
            fitness_goals = functions.get_fitness_goals(trainer_profile)
            trainers.append((trainer_profile,fitness_goals))
        
        return render(request=request, template_name="trainer-list.html", context={'trainers':trainers})
        
    


class SubscriptionPlansView(View):
    def get(self, request):
        return render(request=request, template_name="subscription-plans.html", context={})
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must login first')
            return redirect(reverse('palestra:subscription-plans'))
        
        if request.user.is_instructor or request.user.is_manager:
            messages.error(request, 'You are a staff member')
            return redirect(reverse('palestra:subscription-plans'))
            
        old_subscription = None
        try:
            subscription = models.Subscription.objects.get(user=request.user)
        except models.Subscription.DoesNotExist:
            pass
        else:
            if not subscription.expired():
                messages.error(request, 'You already own a plan that is not expired')
                return redirect(reverse('palestra:subscription-plans'))
            else:
                old_subscription = subscription 

        try:
            user = models.UserProfile.objects.get(user=request.user)
        except models.UserProfile.DoesNotExist:
            messages.error(request, 'You must complete your profile first')
            return redirect(reverse('palestra:subscription-plans'))
        
        if not user.profileInfo():
            messages.error(request, 'You must complete your profile first')
            return redirect(reverse('palestra:subscription-plans'))
        
        try:
            plan = SubscriptionPlan.objects.get(id=request.POST.get('plan_id'))
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, 'The plan that you selected is currently unavailable')
            return redirect(reverse('palestra:subscription-plans'))
        
        duration = int(request.POST.get('duration_selected'))
        
        start_date = datetime.now()
        end_date = start_date + relativedelta(months=duration)

        duration_discounts = DurationDiscount.objects.filter(subscription_plan=plan)
        
        try:
            duration_discount = duration_discounts.get(duration=duration)
        except  DurationDiscount.DoesNotExist:
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
            message = "Your subscription has been successfully renewed"
        else:
            message = "You have successfully subscribed"
            sub = models.Subscription(user=request.user, plan=plan, monthly_price=price, start_date=start_date, end_date=end_date, age_reduction=age_reduction)
            sub.save()

        messages.success(request, message)
        return redirect(reverse('palestra:profile'))

    

class ProfileView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.error(request, "You have to login first")
            return redirect(reverse('login'))
        
        if request.user.is_instructor:
            user_profile, created = models.TrainerProfile.objects.get_or_create(user=request.user)
            form = forms.TrainerProfileForm(instance=user_profile)
            fitness_goals = functions.get_fitness_goals(user_profile)
            context = {'form': form, 'user_profile':user_profile, 'user_fitness_goals':fitness_goals}
        elif request.user.is_manager:
            messages.success(request, f"Welcome to Fit4All, {request.user}")
            return redirect(reverse('palestra:dashboard'))
        else:
            user_profile, created = models.UserProfile.objects.get_or_create(user=request.user)
            form = forms.UserProfileForm(instance=user_profile)
            context = {'form': form, 'user_profile':user_profile}
            try:
                user_subscription = models.Subscription.objects.get(user=request.user)
                plan_id = user_subscription.plan.id
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except (models.Subscription.DoesNotExist,SubscriptionPlan.DoesNotExist):
                pass
            else:
                user_subscription.plan_type = plan.plan_type
                context['user_subscription'] = user_subscription

        return render(request=request, template_name='profile.html', context=context)

    def post(self, request, *args, **kwargs):
        try:
            user_subscription = models.Subscription.objects.get(user=request.user)
        except models.Subscription.DoesNotExist:
            messages.error(request=request, message=f"Error, could not find a subscription plan")
            return redirect(reverse('palestra:profile'))

        if user_subscription.expired():
            return redirect(reverse('palestra:subscription-plans'))
        else:
            messages.success(request=request, message=f"Successfully deleted your subscription")
            user_subscription.delete()
        
        return redirect(reverse('palestra:profile'))


class UpdateProfile(View):
    def get(self, request):
        context = {}
        if not request.user.is_authenticated:
            messages.error(request, "You have to login first")
            return redirect(reverse('login'))
        
        if request.user.is_instructor:
            user_profile = models.TrainerProfile.objects.get(user=request.user)
            fitness_goals = functions.get_fitness_goals(user_profile)
            context = {'user_profile':user_profile, 'trainer_fitness_goals':fitness_goals}
        elif request.user.is_manager:
            messages.success(request, f"Welcome to Fit4All, {request.user}")
            return redirect(reverse('palestra:dashboard'))
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
                fitness_goals = models.FitnessGoal.objects.filter(pk__in=fitness_goals_ids)
                user_profile.fitness_goals.set(fitness_goals)
                user_profile.save()
                instance.save()
            else:
                form.save()

            messages.success(request, "Your profile has been updated")
            return redirect(reverse('palestra:profile'))  # Reindirizza alla pagina del profilo
        
        functions.print_errors(form, request)
        return render(request, 'update-profile.html', {'form': form, 'user_profile':user_profile})
    
class Dashboard(View):
    def get_context(self, request):
        context = {}
        group_classes_reviews = None
        training_sessions_reviews = None

        context['reviews'] = get_reviews(request.user)
        if request.user.is_manager:
            context['group_classes'] = GroupTraining.objects.all()
        else:
            if request.user.is_instructor:
                try:
                    trainer = models.TrainerProfile.objects.get(user=request.user)
                except models.TrainerProfile.DoesNotExist:
                    messages.error(request, f"personal trainer not found: {request.user.username}")
                    return context
                

                instructor_group_classes = GroupTraining.objects.filter(trainer=trainer)

                booked_group_classes = []
                for group_class in instructor_group_classes:
                    
                    reservation_objects = models.GroupClassReservation.objects.filter(group_class=group_class)
                    
                    participants = []
                    if reservation_objects:
                        participants_ids = reservation_objects.values_list('user_id', flat=True)
                        
                        for partecipant_id in participants_ids:
                            try:
                                partecipant = models.UserProfile.objects.get(user_id=partecipant_id)
                            except models.UserProfile.DoesNotExist:
                                continue
                            
                            partecipant = models.UserProfileSerializer(partecipant).data
                            participants.append(partecipant)

                    group_class.participants = participants
                    booked_group_classes.append(group_class)
                    
                booked_training_sessions = models.PersonalTraining.objects.filter(trainer=trainer)
            else:
                booked_group_classes = models.GroupClassReservation.objects.filter(user=request.user)
                booked_training_sessions = models.PersonalTraining.objects.filter(user=request.user)
                group_classes_reviews = models.GroupTrainingReview.objects.filter(user=request.user)
                training_sessions_reviews = models.PersonalTrainingReview.objects.filter(user=request.user)
                

            schedule = {}
            for day in global_variables.week_days:
                schedule[day] = {}
                for hour in range(9,19):
                    schedule[day][hour] = None
            
            for group_class in booked_group_classes:
                if isinstance(group_class, models.GroupClassReservation):
                    try:
                        group_class = GroupTraining.objects.get(id=group_class.group_class.id)
                    except GroupTraining.DoesNotExist:
                        continue

                if global_variables.day_mapping[group_class.day] > global_variables.today.weekday():
                    group_class.expired = False
                elif global_variables.day_mapping[group_class.day] == global_variables.today.weekday():
                    if group_class.start_hour >= global_variables.today.hour:
                        group_class.expired = False
                    else:
                        group_class.expired = True
                else:
                    group_class.expired = True


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

                if global_variables.day_mapping[booked_training_session.day] > global_variables.today.weekday():
                    booked_training_session.expired = False
                elif global_variables.day_mapping[booked_training_session.day] == global_variables.today.weekday():
                    if booked_training_session.start_hour >= global_variables.today.hour:
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
            messages.error(request, "You have to login first")
            return redirect(reverse('login'))
        
        event_type = request.GET.get('event_type')
        event_id =  request.GET.get('event_id')
        if event_id and event_type:
            if event_type == 'group_training':
                try:
                    event = GroupTraining.objects.get(id=event_id)
                    review = models.GroupTrainingReview.objects.get(user=request.user, event=event)
                    review.delete()
                    messages.success(request=request, message="Review deleted successfully")
                    return redirect(reverse('palestra:dashboard'))
                except (GroupTraining.DoesNotExist, models.GroupTrainingReview.DoesNotExist):
                    messages.error(request, f'Group training review not found')
            elif event_type == 'personal_training':
                try:
                    event = models.PersonalTraining.objects.get(id=event_id)
                    review = models.PersonalTrainingReview.objects.get(user=event.user, event=event)
                    review.delete()
                    messages.success(request=request, message="Review deleted successfully")
                    return redirect(reverse('palestra:dashboard'))
                except (models.PersonalTraining.DoesNotExist, models.PersonalTrainingReview.DoesNotExist):
                    messages.error(request, f'Personal training review not found')
        
        context.update(self.get_context(request))
        return render(request=request, template_name="dashboard.html", context=context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_manager and not request.user.is_instructor:
            id_gt = request.POST.get('group_training')
            id_pt = request.POST.get('personal_training')
            try:
                if id_gt:
                    group_training = GroupTraining.objects.get(id=id_gt)
                    models.GroupClassReservation.objects.get(group_class_id=group_training.id, user_id=request.user.id).delete()
                    messages.success(request, 'The Group Class reservation has been cancelled')
                else:
                    models.PersonalTraining.objects.get(id=id_pt).delete()
                    messages.success(request, 'The training session has been cancelled')
            except (models.PersonalTraining.DoesNotExist, models.GroupClassReservation.DoesNotExist, GroupTraining.DoesNotExist):
                pass
        
        class_id = request.POST.get('class_id')
        plan_id = request.POST.get('plan_id')
        fg_delete = request.POST.get('fitness_goal_delete')
        fg_rename = request.POST.get('fitness_goal_rename')
        new_fg = request.POST.get('new_fitness_goal')
        if request.user.is_manager:
            if class_id:
                try:
                    GroupTraining.objects.get(id=class_id).delete()
                    messages.success(request=request, message=f"Successfully deleted the group training with id = {class_id}")
                except GroupTraining.DoesNotExist:
                    messages.error(request=request, message=f"Couldn't delete group training with id = {class_id}")
            if plan_id:
                try:
                    SubscriptionPlan.objects.get(id=plan_id).delete()
                    messages.success(request=request, message=f"Successfully deleted the subscription plan with id = {plan_id}")
                except SubscriptionPlan.DoesNotExist:
                    messages.error(request=request, message=f"Couldn't delete the subscription plan with id = {plan_id}")

            if fg_delete is not None:
                try:
                    fg = models.FitnessGoal.objects.get(name=fg_delete)
                except models.FitnessGoal.DoesNotExist:
                    messages.error(request=request, message=f"Couldn't delete the fitness goal with name = {fg_delete}")
                else:
                    fg.delete()
                    messages.success(request=request, message=f"Successfully deleted the fitness goal with name = {fg_delete}")
            
            if fg_rename is not None:
                try:
                    fg = models.FitnessGoal.objects.get(name=fg_rename)
                except models.FitnessGoal.DoesNotExist:
                    messages.error(request=request, message=f"Couldn't rename the fitness goal with name = {fg_rename}")
                else:
                    fg.name = request.POST.get('new_name')
                    if fg.name:
                        fg.save()
                        messages.success(request=request, message=f"Successfully renamed the fitness goal with name = {fg_rename}")
                    else:
                        messages.error(request=request, message=f"The new name can't be blank")
            
            if new_fg is not None:
                if new_fg == '':
                    messages.error(request=request, message=f"The name can't be blank")
                else:
                    try:
                        fg = models.FitnessGoal.objects.get(name=new_fg)
                    except models.FitnessGoal.DoesNotExist:
                        fg = models.FitnessGoal(name=new_fg)
                        fg.save()
                        messages.success(request=request, message=f"Successfully added the fitness goal with name = {new_fg}")
                    else:
                        messages.error(request=request, message=f"An existing fitness goal with name = {new_fg} has been found")

        return redirect(reverse('palestra:dashboard'))
    

class BookWorkout(View):
    def get_context(self, request, pt_id):
        context = {}
        try:
            trainer = models.TrainerProfile.objects.get(id=pt_id)
        except models.TrainerProfile.DoesNotExist:
            messages.error(request, "The selected personal trainer couldn't be found")
        
        trainer_fitness_goals = functions.get_fitness_goals(trainer)
        
        today_day_name = global_variables.today.strftime("%A")
        today_hour = global_variables.today.hour 

        available_days = [global_variables.week_days[i] for i in range(global_variables.week_days.index(today_day_name), len(global_variables.week_days))]
        available_hours_today = [i for i in range(9,19) if i > today_hour]

        personal_trainings = models.PersonalTraining.objects.filter(trainer_id=pt_id)
        group_trainings = GroupTraining.objects.filter(trainer_id=pt_id)

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
            try:
                day = request.POST.get('day')

                if day not in [day for day,day in models.PersonalTraining.DAY_CHOICES]:
                    messages.error(request, f"{day} is an invalid day choice")
                    return context
                
                hour = request.POST.get('start_hour')
                if int(hour) not in [hour for hour,hour_str in models.PersonalTraining.START_HOUR_CHOICES]:
                    messages.error(request, f"{hour} is an invalid hour choice")
                    return context
                
                user = request.POST.get('user')
                group_classes = GroupTraining.objects.filter(day=day, start_hour=hour)
                for group_class in group_classes:
                    if not group_class.expired():
                        if models.GroupClassReservation.objects.get(user=user, group_class=group_class):
                            messages.error(request, f'You have an upcoming group class training session already booked for {group_class.day} at {group_class.start_hour}')
                            return context
            except (models.GroupClassReservation.DoesNotExist, GroupTraining.DoesNotExist):
                messages.error(request, f"Group class reservation not found for user: {user}")
                return context
                
        return context
    
    def get(self, request, pt_id):
        context = self.get_context(request, pt_id)
        return render(request, template_name="book-workout.html", context=context)
    
    def post(self, request, *args, **kwargs):
        form = forms.PersonalTrainingForm(data=request.POST)

        if not request.user.is_authenticated:
            messages.error(request, 'You must login first')
            return redirect(reverse('login'))

        elif request.user.is_manager or request.user.is_instructor:
            messages.error(request, 'You are a staff member')
            return redirect(reverse('palestra:trainer-list'))

        try:
            subscription = models.Subscription.objects.get(user=request.user)
            if subscription.expired():
                messages.error(request, 'Your subscription has expired')
                return redirect(reverse('palestra:profile'))
            if subscription.plan.plan_type == 'GROUP':
                messages.error(request, f'Your subscription plan ({subscription.plan.name}) does not allow that')
                return redirect(reverse('palestra:profile'))
        except models.Subscription.DoesNotExist:
            messages.error(request, 'You are not a member')
            return redirect(reverse('palestra:subscription-plans'))

        context = self.get_context(request, request.POST.get('trainer'))

        all_messages = messages.get_messages(request)
        if all_messages:
            for message in all_messages:
                if message.level == messages.ERROR:
                    return render(request, template_name="book-workout.html", context=context)
        
        if form.is_valid():
            form.save()
        else:
            functions.print_errors(form, request)
            return render(request, template_name="book-workout.html", context=context)
        
        messages.success(request, f"Workout session booked successfully")
        return redirect(reverse('palestra:dashboard'))
    

def get_LeaveReview_context(request=None, event_id=None, event_type=None, edit=False):
        context = {}
        if not event_id or not event_type:
            event_id = request.GET.get('event_id')
        
        if not event_type:
            event_type = request.GET.get('event_type')

        
        if event_type == 'group_training':
            try:
                event = GroupTraining.objects.get(id=event_id)
            except GroupTraining.DoesNotExist:
                context['errror'] = f"Group training not found with id: {event_id}"
                return context
            
            event.date = functions.get_event_date(event)
            
            if edit:
                try:
                    context['review'] = models.GroupTrainingReview.objects.get(user=request.user, event=event)
                except models.GroupTrainingReview.DoesNotExist:
                    messages.error(request, f"Group training review not found")
                    return context
            
        elif event_type == 'personal_training':
            try:
                event = models.PersonalTraining.objects.get(id=event_id)
            except models.PersonalTraining.DoesNotExist:
                messages.error(request, f"Personal training session not found with id: {event_id}")
                return context
            if edit:
                try:
                    context['review'] = models.PersonalTrainingReview.objects.get(user=event.user, event=event)
                except models.PersonalTrainingReview.DoesNotExist:
                    messages.error(request, f"Personal training review not found")
                    return context
            
            event.date = functions.get_event_date(event)
            event.training_type = models.FitnessGoal.objects.get(id=event.training_type).name
        else:
            messages.error(request, f'invalid event type: {event_type}')
            event = None

        
        context['event'] = event
        
        return context


class LeaveReview(View):
    def post(self, request, *args, **kwargs):
        context = get_LeaveReview_context(request=request)
        event_type = request.GET.get('event_type')

        if event_type == 'group_training':
            form = forms.GroupTrainingReviewForm(request.POST)
            context['form'] = form
        elif event_type == 'personal_training':
            form = forms.PersonalTrainingReviewForm(request.POST)
            context['form'] = form
        else:
            messages.error(request, f'invalid event type: {event_type}')
            return redirect(reverse('palestra:dashboard'))
        
        all_messages = messages.get_messages(request)
        if all_messages:
            for message in all_messages:
                if message.level == messages.ERROR:
                    return render(request=request, template_name="leave-review.html", context=context)
                
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for your review")
            return redirect(reverse('palestra:dashboard'))
        else:
            functions.print_errors(form, request)
            return render(request=request, template_name="leave-review.html", context=context)
    

    def get(self, request):
        context = get_LeaveReview_context(request)
        event = context.get('event', None)

        if not request.user.is_authenticated:
            messages.error(request, 'You must login first')
            return redirect(reverse('login'))
        
        if not event:
            messages.error(request, 'invalid event')
            return redirect(reverse('palestra:dashboard'))
        
        if request.user.is_manager or request.user.is_instructor:
            messages.error(request, 'You are a staff member')
            return redirect(reverse('palestra:dashboard'))
        
        try:
            if not event.expired():
                messages.error(request, "You can't leave a review for this event yet")
                return redirect(reverse('palestra:dashboard'))
            
            if isinstance(event, GroupTraining):
                reservation = models.GroupClassReservation.objects.get(group_class=event, user=request.user)

        except (models.GroupClassReservation.DoesNotExist):   
            messages.error(request, 'You did not partecipate to that event')
            return redirect(reverse('palestra:dashboard'))

                    
        return render(request=request, template_name="leave-review.html", context=context)
    
class EditReview(View):
    def get(self, request):
        context = get_LeaveReview_context(request=request, edit=True)

        event = context.get('event', None)

        if not request.user.is_authenticated:
            messages.error(request, 'You must login first')
            return redirect(reverse('login'))
        
        if not event:
            messages.error(request, 'invalid event')
            return redirect(reverse('palestra:dashboard'))
        
        if request.user.is_manager or request.user.is_instructor:
            messages.error(request, 'You are a staff member')
            return redirect(reverse('palestra:dashboard'))
        
        return render(request=request, template_name="edit-review.html", context=context)

    def post(self, request, *args, **kwargs):
        user = request.POST.get('user')
        event = request.POST.get('event')
        event_type = request.POST.get('event_type')
        context = get_LeaveReview_context(request=request, event_type=event_type, event_id=event, edit=True)
        old_review = None

        if event_type == 'personal_training':
            try:
                old_review = models.PersonalTrainingReview.objects.get(user=user, event=event)
            except models.PersonalTrainingReview.DoesNotExist:
                messages.error(request, f"Couldn't edit the review")
            else:
                form = forms.PersonalTrainingReviewForm(request.POST, instance=old_review)
        elif event_type == 'group_training':
            
            try:
                old_review = models.GroupTrainingReview.objects.get(user=user, event=event)
            except models.GroupTrainingReview.DoesNotExist:
                messages.error(request, f"Couldn't edit the review")
            else:
                form = forms.GroupTrainingReviewForm(request.POST, instance=old_review)

        else:
            messages.error(request, f"Invalid choice for event_type: {event_type}")

        if form.is_valid(): 
            form.save()
            messages.success(request, "Your review has been successfully edited")
            return redirect(reverse('palestra:dashboard'))
        else:
            functions.print_errors(form, request)

        
        for message in messages.get_messages(request):
            print(message)

        context['review'] = old_review
        return render(request=request, template_name="edit-review.html", context=context)