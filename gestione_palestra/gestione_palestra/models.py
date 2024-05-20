from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from datetime import datetime, date
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.utils.timezone import now
import re
from . import context_processors


class User(AbstractUser):
    is_manager = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class UserProfile(models.Model):
    user = models.OneToOneField('gestione_palestra.User', on_delete=models.CASCADE)
    # Attributi personalizzati
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices, null=False, blank=True)
    first_name = models.CharField(max_length=100, null=False,blank=True)
    last_name = models.CharField(max_length=100, null=False,blank=True)
    date_of_birth = models.DateField(null=False,blank=True,default=date.today)
    height = models.DecimalField(max_digits=5, decimal_places=0, null=False,blank=True)  # In centimetri
    weight = models.DecimalField(max_digits=5, decimal_places=0, null=False,blank=True)  # In chilogrammi
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    def clean(self):
        super().clean()
        if self.date_of_birth > context_processors.today.date():
            raise ValidationError({'date_of_birth': 'The date you inserted is in the future.'})
        
        age = context_processors.today.year - self.date_of_birth.year - ((context_processors.today.month, context_processors.today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        if age > 100 or age < 14:
            raise ValidationError({'date_of_birth': 'Age must be an integer between 14 and 100.'})
        
        if not re.match("^[a-zA-Z0-9]*$", self.name):
            raise ValidationError({'name': 'Only alphanumeric characters are allowed for first and last names.'})
        
        if not 55 <= self.height <= 230:
            raise ValidationError({'height': 'Height must be an integer between 55 and 230.'})
        
        if not 50 <= self.weight <= 150:
            raise ValidationError({'weight': 'Weight must be an integer between 50 and 150.'})
        
        if not 10 <= self.duration <= 120:
            raise ValidationError({'duration': 'Duration must be an integer between 10 and 120.'})
        
        if not 5 <= self.max_participants <= 30:
            raise ValidationError({'max_participants': 'Max participants must be an integer between 5 and 30.'})
        
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
        model = 'gestione_palestra.UserProfile'
        fields = '__all__'


class FitnessGoal(models.Model):
    name = models.CharField(max_length=100)


class TrainerProfile(models.Model):
    user = models.OneToOneField('gestione_palestra.User', on_delete=models.CASCADE)
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices, null=False, blank=True)
    first_name = models.CharField(max_length=100, null=False, blank=True)
    last_name = models.CharField(max_length=100, null=False, blank=True)
    date_of_birth = models.DateField(null=False, blank=True, default=date.today)
    certifications = models.FileField(upload_to='pt_CVs/', blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    fitness_goals = models.ManyToManyField(FitnessGoal, blank=True)  # Cambio qui
    pt_photo = models.ImageField(upload_to='pt_images/', null=True, blank=True)

    def clean(self):
        super().clean()
        
        if not re.match("^[a-zA-Z0-9]*$", self.first_name):
            raise ValidationError({'name': 'Only alphanumeric characters are allowed for first and last names.'})
        
        if not re.match("^[a-zA-Z0-9]*$", self.last_name):
            raise ValidationError({'name': 'Only alphanumeric characters are allowed for first and last names.'})
        
        if self.date_of_birth > context_processors.today.date():
            raise ValidationError({'date_of_birth': 'The date you inserted is in the future.'})
        
        age = context_processors.today.year - self.date_of_birth.year - ((context_processors.today.month, context_processors.today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        if age > 100 or age < 14:
            raise ValidationError({'date_of_birth': 'Age must be an integer between 14 and 100.'})


class Subscription(models.Model):
    user = models.OneToOneField('gestione_palestra.User', on_delete=models.CASCADE, unique=True)
    plan = models.ForeignKey('gestione_palestra.SubscriptionPlan', on_delete=models.CASCADE)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    age_reduction = models.BooleanField()

    def expired(self):
        return True if self.end_date < datetime.now().date() else False


class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('GROUP', 'Group Classes Only'),
        ('WEIGHTS', 'Gym Access Only'),
        ('BOTH', 'Group Classes + Gym Access'),
    ]

    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=10, choices=PLAN_CHOICES)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    age_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def clean(self):
        super().clean()

        if self.age_discount < 0 or self.age_discount > 100:
            raise ValidationError({'age_discount': 'The age discount must be between 0 an 100.'})
        
    def calculate_total_price(self, user_age):
        if user_age < 18 or user_age >= 65:
            return self.monthly_price - self.age_discount
        else:
            return self.monthly_price

    def __str__(self):
        return self.name


class DurationDiscount(models.Model):
    DURATION_CHOICES = [
        (1, '1 Month'),
        (3, '3 Months'),
        (6, '6 Months'),
        (12, '12 Months'),
    ]

    duration = models.IntegerField(choices=DURATION_CHOICES)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subscription_plan = models.ForeignKey('gestione_palestra.SubscriptionPlan', on_delete=models.CASCADE)

    def clean(self):
        super().clean()

        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValidationError({'age_discount': 'The discount percentage must be between 0 an 100.'})


class GroupTraining(models.Model):
    trainer = models.ForeignKey('TrainerProfile', on_delete=models.CASCADE)
    
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
    duration = models.PositiveIntegerField()  # Durata in minuti
    
    max_participants = models.PositiveIntegerField()
    total_partecipants = models.PositiveIntegerField(default=0)
    title = models.TextField()
    image = models.ImageField(upload_to='group-classes/', null=True, blank=True)

    def clean(self):
        super().clean()

        if not re.match("^[a-zA-Z0-9]*$", self.title):
            raise ValidationError({'name': 'Only alphanumeric characters are allowed for titles.'})

    def ended(self):
        ended = False

        today_day_index = context_processors.today.weekday()
        group_training_day_index = context_processors.day_mapping[self.day]

        if today_day_index > group_training_day_index:
            ended = True
        elif today_day_index == group_training_day_index:
            if context_processors.today.hour >= self.start_hour:
                ended = True
            else:
                ended = False
        else:
            ended = False

        return ended

class GroupClassReservation(models.Model):
    group_class = models.ForeignKey('gestione_palestra.GroupTraining', on_delete=models.CASCADE)
    user = models.ForeignKey('gestione_palestra.User', on_delete=models.CASCADE)


class PersonalTraining(models.Model):
    trainer = models.ForeignKey('TrainerProfile', on_delete=models.CASCADE)
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
    additional_info = models.TextField(blank=True)

    @property
    def training_type_choices(self):
        return [(str(goal.id), goal.name) for goal in FitnessGoal.objects.all()]
    



class TrainingReview(models.Model):
    user = models.ForeignKey('gestione_palestra.User', on_delete=models.CASCADE)
    stars = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(6)])
    title = models.TextField()
    date = models.DateField(default=now)
    additional_info = models.TextField(blank=True)

    class Meta:
        abstract = True

class GroupTrainingReview(TrainingReview):
    event = models.ForeignKey('gestione_palestra.GroupTraining', on_delete=models.CASCADE)

class PersonalTrainingReview(TrainingReview):
    event = models.ForeignKey('gestione_palestra.PersonalTraining', on_delete=models.CASCADE)