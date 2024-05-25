from django.db import models
from django.core.exceptions import ValidationError
from utils.global_variables import today, day_mapping

class GroupTraining(models.Model):
    trainer = models.ForeignKey('palestra.TrainerProfile', on_delete=models.CASCADE)
    
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
        
        if self.max_participants and self.max_participants <= 0 or self.max_participants > 50:
            raise ValidationError({'max_participants': 'Insert a number between 1 and 50'})
        
        if self.duration and self.duration <= 0 or self.duration > 120:
            raise ValidationError({'duration': 'Insert a number between 1 and 120'})

    def ended(self):
        ended = False

        today_day_index = today.weekday()
        group_training_day_index = day_mapping[self.day]

        if today_day_index > group_training_day_index:
            ended = True
        elif today_day_index == group_training_day_index:
            if today.hour >= self.start_hour:
                ended = True
            else:
                ended = False
        else:
            ended = False

        return ended
    
class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('GROUP', 'Group Classes Only'),
        ('WEIGHTS', 'Gym Access Only'),
        ('FULL', 'Group Classes + Gym Access'),
    ]

    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=10, choices=PLAN_CHOICES)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    age_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def clean(self):
        super().clean()

        if self.age_discount < 0 or self.age_discount > self.monthly_price:
            raise ValidationError({'age_discount': 'The age discount must be between 0 and monthly_price.'})
        
        if self.monthly_price < 0 or self.monthly_price > 100:
            raise ValidationError({'monthly_price': 'The monthly price must be between 0 and 100.'})
        
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
    discount_percentage = models.DecimalField(null=True, max_digits=5, decimal_places=2, default=0)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)

    def clean(self):
        super().clean()

        if self.discount_percentage and self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValidationError({'age_discount': 'The discount percentage must be between 0 an 100.'})

class FitnessGoal(models.Model):
    name = models.CharField(max_length=100)