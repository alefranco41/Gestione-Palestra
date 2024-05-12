from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime, date
from django.utils.translation import gettext_lazy as _

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
    date_of_birth = models.DateField(null=False,blank=True,default=date.today)
    height = models.DecimalField(max_digits=5, decimal_places=0, null=False,blank=True)  # In centimetri
    weight = models.DecimalField(max_digits=5, decimal_places=0, null=False,blank=True)  # In chilogrammi
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    AGE_OF_RETIREMENT = 65  # Età di pensionamento
    LEGAL_ADULT_AGE = 18  # Età maggiore

    def ageReduction(self):
        today = date.today()
        age_in_days = (today - self.date_of_birth).days
        return True if age_in_days >= self.AGE_OF_RETIREMENT * 365 or age_in_days <= self.LEGAL_ADULT_AGE * 365 else False

    def profileInfo(self):
        return True if self.first_name and self.last_name and self.date_of_birth else False

class FitnessGoal(models.Model):
    name = models.CharField(max_length=100)

class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices, null=False, blank=True)
    first_name = models.CharField(max_length=100, null=False,blank=True)
    last_name = models.CharField(max_length=100, null=False,blank=True)
    date_of_birth = models.DateField(null=False,blank=True,default=date.today)
    certifications = models.FileField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    fitness_goals = models.ManyToManyField(FitnessGoal, blank=True)  # Cambio qui
    pt_photo = models.ImageField(upload_to='pt_images/', null=True, blank=True)

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.CASCADE)
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

    DURATION_CHOICES = [
        (1, '1 Month'),
        (3, '3 Months'),
        (6, '6 Months'),
        (12, '12 Months'),
    ]

    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=10, choices=PLAN_CHOICES)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    age_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def calculate_total_price(self, user_age):
        if user_age < 18 or user_age >= 65:
            return self.monthly_price - self.age_discount
        else:
            return self.monthly_price

    def __str__(self):
        return self.name


class DurationDiscount(models.Model):
    duration = models.IntegerField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)



class GroupTraining(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE)
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
    training_type = models.CharField(max_length=10, choices=[(goal.id, goal.name) for goal in FitnessGoal.objects.all()])
    max_participants = models.PositiveIntegerField()
    total_partecipants = models.PositiveIntegerField(default=0)
    description = models.TextField()
    image = models.ImageField(upload_to='group-classes/', null=True, blank=True)

class GroupClassReservation(models.Model):
    group_class = models.ForeignKey(GroupTraining, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)



class PersonalTraining(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    training_type = models.CharField(max_length=10, choices=[(str(goal.id), goal.name) for goal in FitnessGoal.objects.all()])
    additional_info = models.TextField(blank=True)