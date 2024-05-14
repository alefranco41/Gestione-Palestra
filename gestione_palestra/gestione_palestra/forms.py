from django import forms
from . import models
from django.db import connection


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput) 

    class Meta:
        model = models.User
        fields = ['username', 'email', 'password', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

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
    
    fitness_goals_choices = models.FitnessGoal.objects.all()

    choices = [(goal.id, goal.name) for goal in fitness_goals_choices]

    fitness_goals = forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = models.TrainerProfile
        fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'profile_picture', 'pt_photo', 'certifications']



class GroupTrainingForm(forms.ModelForm):
    day = forms.ChoiceField(choices=models.GroupTraining.DAY_CHOICES)
    start_hour = forms.ChoiceField(choices=models.GroupTraining.START_HOUR_CHOICES)

    class Meta:
        model = models.GroupTraining
        fields = ['trainer', 'day', 'start_hour', 'duration', 'max_participants', 'title']


class PersonalTrainingForm(forms.ModelForm):
    day = forms.ChoiceField(choices=models.GroupTraining.DAY_CHOICES)
    start_hour = forms.ChoiceField(choices=models.GroupTraining.START_HOUR_CHOICES)
    fitness_goals_choices = models.FitnessGoal.objects.all()

    choices = [(str(goal.id), goal.name) for goal in fitness_goals_choices]
    
    training_type = forms.ChoiceField(choices=choices)

    class Meta:
        model = models.PersonalTraining
        fields = ['trainer', 'user', 'day', 'start_hour', 'training_type', 'additional_info']



class GroupTrainingReviewForm(forms.ModelForm):
    class Meta:
        model = models.GroupTrainingReview
        fields = ['user', 'stars', 'title', 'additional_info', 'event']

class PersonalTrainingReviewForm(forms.ModelForm):
    class Meta:
        model = models.PersonalTrainingReview
        fields = ['user', 'stars', 'title', 'additional_info', 'event']