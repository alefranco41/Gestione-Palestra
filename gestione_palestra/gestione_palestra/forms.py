from django import forms
from . import models
from django.db import connection


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput) 

    class Meta:
        model = models.User
        fields = ['username', 'email', 'password', 'password2']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.", code="password_mismatch")

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'height', 'weight', 'profile_picture']

class TrainerProfileForm(forms.ModelForm):
    class Meta:
        model = models.TrainerProfile
        fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'profile_picture', 'pt_photo', 'certifications', 'fitness_goals']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ottieni le scelte dinamicamente
        fitness_goals_choices = [(goal.id, goal.name) for goal in models.FitnessGoal.objects.all()]
        self.fields['fitness_goals'].choices = fitness_goals_choices
        self.fields['fitness_goals'].widget = forms.CheckboxSelectMultiple()



class GroupTrainingForm(forms.ModelForm):
    day = forms.ChoiceField(choices=models.GroupTraining.DAY_CHOICES)
    start_hour = forms.ChoiceField(choices=models.GroupTraining.START_HOUR_CHOICES)

    class Meta:
        model = models.GroupTraining
        fields = ['trainer', 'day', 'start_hour', 'duration', 'max_participants', 'title', 'image']


class PersonalTrainingForm(forms.ModelForm):
    class Meta:
        model = models.PersonalTraining
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.fields['training_type'].choices = kwargs['instance'].training_type_choices
        else:
            self.fields['training_type'].choices = models.PersonalTraining().training_type_choices



class GroupTrainingReviewForm(forms.ModelForm):
    class Meta:
        model = models.GroupTrainingReview
        fields = ['user', 'stars', 'title', 'additional_info', 'event']

class PersonalTrainingReviewForm(forms.ModelForm):
    class Meta:
        model = models.PersonalTrainingReview
        fields = ['user', 'stars', 'title', 'additional_info', 'event', 'trainer']



class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = models.SubscriptionPlan
        fields = ['name', 'plan_type', 'monthly_price', 'age_discount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'plan_type': forms.Select(attrs={'class': 'form-control'}),
            'monthly_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'age_discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class DurationDiscountForm(forms.Form):
    discount_1 = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    discount_3 = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    discount_6 = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    discount_12 = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))