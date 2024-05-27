from management import forms, models
from palestra.models import TrainerProfile
from utils import functions
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from datetime import datetime, timedelta
from utils.global_variables import today, day_mapping



class NewGroupTraining(View):    
    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_manager:
            messages.error(request, "You don't have the permission to do that")
            return redirect(reverse('login'))  
        
        form = forms.GroupTrainingForm()
        trainers = TrainerProfile.objects.all()

        return render(request, 'create-group-training.html', {'form': form, 'trainers':trainers})
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = forms.GroupTrainingForm(request.POST, request.FILES)
            trainers = TrainerProfile.objects.all()
            if form.is_valid():                
                all_courses = models.GroupTraining.objects.all()
                if all_courses:
                    this_monday = today - timedelta(days=today.weekday())
                    group_class_day = this_monday + timedelta(days=day_mapping[form.cleaned_data['day']])
                    new_start = datetime(year=group_class_day.year, month=group_class_day.month, day=group_class_day.day, hour=int(form.cleaned_data['start_hour']))
                    new_end = new_start + timedelta(minutes=form.cleaned_data['duration'])

                    overlapping = False
            
                    for course in all_courses:
                        start, end = course.get_date_interval()
                        if max(new_start, start) < min(new_end, end):
                            overlapping = True
                            break
                
                if not overlapping or not all_courses:
                    form.save()
                else:
                    messages.error(request, 'There is already a group class in that time frame')
                    return render(request, 'create-group-training.html', {'form': form, 'trainers':trainers})
            else:
                functions.print_errors(form, request)
                return render(request, 'create-group-training.html', {'form': form, 'trainers':trainers})
        
        messages.success(request, "Group training created successfully")
        return redirect(reverse('palestra:dashboard'))  
    


class CreatePlan(View):
    def get_context(self, request):
        context = {}

        if request.method == 'POST':
            form = forms.SubscriptionPlanForm(request.POST)
        else:
            form = forms.SubscriptionPlanForm()

        context['form'] = form
        
        choices = models.SubscriptionPlan.PLAN_CHOICES
        for plan in models.SubscriptionPlan.objects.all():
            for choice in choices:
                if choice[0] == plan.plan_type:
                    choices.remove(choice)
                    break
        
        context['available_plans'] =  choices
        return context

    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_manager:
            messages.error(request=request, message="You do not have the permission to do that")
            return redirect(reverse("home"))

        context = self.get_context(request)

        if not context['available_plans']:
            messages.error(request=request, message="All the available plans are already created, you must delete one first")
            return redirect(reverse('palestra:dashboard'))
        return render(request=request, template_name="create-plan.html", context=context)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request)
        form = context['form']
        if form.is_valid():
            form.save()
        else:
            functions.print_errors(form, request)

            return render(request=request, template_name="create-plan.html", context=self.get_context(request))

        messages.success(request=request, message="Subscription Plan created successfully")
        return redirect(reverse("palestra:dashboard"))


class EditDiscounts(View):
    def get_context(self, request, plan_id):
        context = {}
        
        if request.method == 'POST':
            form = forms.DurationDiscountForm(request.POST)
        else:
            form = forms.DurationDiscountForm()


        try:
            plan = models.SubscriptionPlan.objects.get(id=plan_id)
        except models.SubscriptionPlan.DoesNotExist:
            messages.error(request=request, message=f"Couldn't find a subscription plan with id = {plan_id}")
            return redirect(reverse("palestra:dashboard"))
        
        discount = {}
        for discount_object in models.DurationDiscount.objects.filter(subscription_plan=plan_id):
            duration_discount = discount_object.duration
            for duration, name in discount_object.DURATION_CHOICES:
                if duration_discount == duration:
                    discount[duration_discount] = discount_object.discount_percentage
                    break
        
        context['discount'] = discount
        context['plan'] = plan


        context['form'] = form

        return context

    def get(self, request, plan_id):
        if not request.user.is_authenticated or not request.user.is_manager:
            messages.error(request=request, message="You do not have the permission to do that")
            return redirect(reverse("home"))
        
        
        return render(request=request, template_name="edit-discounts.html", context=self.get_context(request,plan_id))

    def post(self, request, *args, **kwargs):
        context = self.get_context(request, request.POST.get('plan_id'))

        form = context['form']
        plan = context['plan']

        form=forms.DurationDiscountForm(request.POST)
        if form.is_valid():
            for duration, label in models.DurationDiscount.DURATION_CHOICES:
                obj, _ = models.DurationDiscount.objects.get_or_create(subscription_plan=plan, duration=duration)
                new_discount = form.cleaned_data[f'discount_{duration}']
                obj.discount_percentage = new_discount
                obj.save()
        else:
            functions.print_errors(form, request)
            
            return render(request=request, template_name="edit-discounts.html", context=self.get_context(request,request.POST.get('plan_id')))
        
        messages.success(request=request, message="Subscription Discounts edited successfully")
        return redirect(reverse("palestra:dashboard"))


class EditPlan(View):
    def get_context(self, request, plan_id):
        context = {}

        try:
            plan = models.SubscriptionPlan.objects.get(id=plan_id)
        except models.SubscriptionPlan.DoesNotExist:
            messages.error(request=request, message=f"Couldn't find a subscription plan with id = {plan_id}")
            return redirect(reverse("palestra:dashboard"))
        

        if request.method == 'POST':
            sub_form = forms.SubscriptionPlanForm(request.POST)
        else:
            sub_form = forms.SubscriptionPlanForm()

        context['plan'] = plan
        context['sub_form'] = sub_form

        return context
    
    def get(self, request, plan_id):
        if not request.user.is_authenticated or not request.user.is_manager:
            messages.error(request=request, message="You do not have the permission to do that")
            return redirect(reverse("home"))
        
        
        return render(request=request, template_name="edit-plan.html", context=self.get_context(request,plan_id))

    def post(self, request, *args, **kwargs):
        sub_form = forms.SubscriptionPlanForm(request.POST)

        plan_id = request.POST.get('plan_id')
        context = self.get_context(request, plan_id)


        if not sub_form.is_valid():
            functions.print_errors(sub_form, request) 
            return render(request=request, template_name='edit-plan.html', context=context)


        plan = context['plan']
        plan.name = sub_form.cleaned_data['name']
        plan.plan_type = sub_form.cleaned_data['plan_type']
        plan.monthly_price = sub_form.cleaned_data['monthly_price']
        plan.age_discount = sub_form.cleaned_data['age_discount']
        plan.save()

        messages.success(request=request, message="Subscription Plan edited successfully")
        return redirect(reverse("palestra:dashboard"))



class EditGroupTraining(View):
    def get(self, request, course_id):
        context = {}
        
        form = forms.GroupTrainingForm()
        trainers = TrainerProfile.objects.all()
        context['form'] = form
        context['trainers'] = trainers

        if not request.user.is_authenticated or not request.user.is_manager:
            messages.error(request, "You don't have the permission to do that")
            return redirect(reverse('login'))  
        try:
            class_item = models.GroupTraining.objects.get(id=course_id)
        except models.GroupTraining.DoesNotExist:
            messages.error(request, f"The group training that you are trying to edit (id = {course_id}) doesn't exist")
            return context
        else:
            context['class'] = class_item

        return render(request, 'edit-group-training.html', context)
    
    def post(self, request, *args, **kwargs):
        class_id = kwargs.get('course_id')
        trainers = TrainerProfile.objects.all()
        if class_id:
            try:
                class_item = models.GroupTraining.objects.get(id=class_id)
            except models.GroupTraining.DoesNotExist:
                messages.error(request, 'The class you are trying to edit does not exist')
                return render(request, 'edit-group-training.html', {'class':None, 'form':form, 'trainers':trainers})
            else:
                form = forms.GroupTrainingForm(request.POST, request.FILES, instance=class_item)
                if form.is_valid():
                    all_courses = models.GroupTraining.objects.all()
                    if all_courses:
                        this_monday = today - timedelta(days=today.weekday())
                        group_class_day = this_monday + timedelta(days=day_mapping[form.cleaned_data['day']])
                        new_start = datetime(year=group_class_day.year, month=group_class_day.month, day=group_class_day.day, hour=int(form.cleaned_data['start_hour']))
                        new_end = new_start + timedelta(minutes=form.cleaned_data['duration'])

                        overlapping = False
                
                        for course in all_courses:
                            if course == class_item:
                                continue
                            start, end = course.get_date_interval()
                            if max(new_start, start) < min(new_end, end):
                                overlapping = True
                                break
                        
                        if not overlapping:
                            form.save()
                        else:
                            messages.error(request, 'There is already a group class in that time frame')
                            return render(request, 'edit-group-training.html', {'class':class_item, 'form': form, 'trainers':trainers})
                    else:
                        form.save()
                else:
                    functions.print_errors(form, request)
                    return render(request, 'edit-group-training.html', {'class':class_item, 'form':form, 'trainers':trainers})
        else:
            messages.error(request, "You must specify the 'course_id' parameter")
            return render(request, 'edit-group-training.html', {'class': None, 'form': form, 'trainers': trainers})

        messages.success(request, f"Group training successfully edited")
        return redirect(reverse('palestra:classes-schedule'))  