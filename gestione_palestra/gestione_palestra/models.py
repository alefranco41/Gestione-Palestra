from django.contrib.auth.models import User
from django.db import models
from datetime import datetime, date

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


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.CASCADE)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

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