from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from datetime import datetime, date
from django.db.models.signals import post_save, post_delete
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.utils.timezone import now
from django.dispatch import receiver
import re
from management.models import FitnessGoal
from utils import functions, global_variables

class User(AbstractUser):
    is_manager = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Attributi personalizzati
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices, null=False, blank=True)
    first_name = models.CharField(max_length=100, null=False,blank=True)
    last_name = models.CharField(max_length=100, null=False,blank=True)
    date_of_birth = models.DateField(null=True,blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=0, null=True,blank=True)  # In centimetri
    weight = models.DecimalField(max_digits=5, decimal_places=0, null=True,blank=True)  # In chilogrammi
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    def clean(self):
        super().clean()
        if self.date_of_birth and self.date_of_birth > global_variables.today.date():
            raise ValidationError({'date_of_birth': 'The date you inserted is in the future.'})
        
        if self.date_of_birth.year:
            age = global_variables.today.year - self.date_of_birth.year - ((global_variables.today.month, global_variables.today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            if age > 100 or age < 14:
                raise ValidationError({'date_of_birth': 'Your age must be between 14 and 100.'})
        
        if not re.match("^[a-zA-Z0-9]*$", self.first_name):
            raise ValidationError({'first_name': 'Only alphanumeric characters are allowed for first and last names.'})
        
        if not re.match("^[a-zA-Z0-9]*$", self.last_name):
            raise ValidationError({'last_name': 'Only alphanumeric characters are allowed for first and last names.'})
        
        if self.height and not 55 <= self.height <= 230:
            raise ValidationError({'height': 'Height must be an integer between 55 and 230.'})
        
        if self.weight and not 50 <= self.weight <= 150:
            raise ValidationError({'weight': 'Weight must be an integer between 50 and 150.'})
        
        
    AGE_OF_RETIREMENT = 65  # Età di pensionamento
    LEGAL_ADULT_AGE = 18  # Età maggiore

    def ageReduction(self):
        today = date.today()
        age_in_days = (today - self.date_of_birth).days
        return True if age_in_days >= self.AGE_OF_RETIREMENT * 365 or age_in_days <= self.LEGAL_ADULT_AGE * 365 else False

    def profileInfo(self):
        return True if self.first_name and self.last_name and self.date_of_birth else False


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices, null=False, blank=True)
    first_name = models.CharField(max_length=100, null=False, blank=True)
    last_name = models.CharField(max_length=100, null=False, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    certifications = models.FileField(upload_to='pt_CVs/', blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    fitness_goals = models.ManyToManyField(FitnessGoal, blank=True)  # Cambio qui
    pt_photo = models.ImageField(upload_to='pt_images/', null=True, blank=True)

    def clean(self):
        super().clean()
        
        if not re.match("^[a-zA-Z0-9]*$", self.first_name):
            raise ValidationError({'first_name': 'Only alphanumeric characters are allowed for first and last names.'})
        
        if not re.match("^[a-zA-Z0-9]*$", self.last_name):
            raise ValidationError({'last_name': 'Only alphanumeric characters are allowed for first and last names.'})
        
        if self.date_of_birth and self.date_of_birth > global_variables.today.date():
            raise ValidationError({'date_of_birth': 'The date you inserted is in the future.'})
        
        if self.date_of_birth:
            age = global_variables.today.year - self.date_of_birth.year - ((global_variables.today.month, global_variables.today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            if age > 100 or age < 18:
                raise ValidationError({'date_of_birth': 'Your age must be between 14 and 100.'})


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    plan = models.ForeignKey('management.SubscriptionPlan', on_delete=models.CASCADE)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    age_reduction = models.BooleanField()

    def expired(self):
        return True if self.end_date < datetime.now().date() else False

class GroupClassReservation(models.Model):
    group_class = models.ForeignKey('management.GroupTraining', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

@receiver(post_save, sender=GroupClassReservation)
def increment_total_partecipants(sender, instance, created, **kwargs):
    if created:
        instance.group_class.total_partecipants += 1
        instance.group_class.save()

@receiver(post_delete, sender=GroupClassReservation)
def decrement_total_partecipants(sender, instance, **kwargs):
    instance.group_class.total_partecipants -= 1
    instance.group_class.save()

class PersonalTraining(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    
    START_HOUR_CHOICES = [
        (9, '9:00'),
        (10, '10:00'),
        (11, '11:00'),
        (12, '12:00'),
        (13, '13:00'),
        (14, '14:00'),
        (15, '15:00'),
        (16, '16:00'),
        (17, '17:00'),
        (18, '18:00'),
    ]
    start_hour = models.PositiveSmallIntegerField(choices=START_HOUR_CHOICES)

    training_type = models.CharField(max_length=10)
    additional_info = models.TextField(blank=True, max_length=500)

    @property
    def training_type_choices(self):
        return [(str(goal.id), goal.name) for goal in FitnessGoal.objects.all()]
    
    def expired(self):
        print(global_variables.today.hour, self.start_hour)
        if global_variables.day_mapping[self.day] > global_variables.today.weekday():
            return False
        elif global_variables.day_mapping[self.day] == global_variables.today.weekday():
            if global_variables.today.hour >= self.start_hour:
                return True
            else:
                return False
        else:
            return True



class TrainingReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stars = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(6)])
    title = models.TextField(max_length=100)
    date = models.DateField(default=now)
    additional_info = models.TextField(blank=True, max_length=500)

    class Meta:
        abstract = True

class GroupTrainingReview(TrainingReview):
    event = models.ForeignKey('management.GroupTraining', on_delete=models.CASCADE)

class PersonalTrainingReview(TrainingReview):
    event = models.ForeignKey(PersonalTraining, null=True, on_delete=models.SET_NULL)
    trainer = models.ForeignKey(TrainerProfile, null=True, on_delete=models.CASCADE, related_name='reviews')