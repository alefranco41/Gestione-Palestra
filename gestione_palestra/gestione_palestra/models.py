from django.contrib.auth.models import User
from django.db import models
import datetime
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
    date_of_birth = models.DateField(null=False,blank=True,default=datetime.date.today)
    height = models.DecimalField(max_digits=5, decimal_places=0, null=False,blank=True)  # In centimetri
    weight = models.DecimalField(max_digits=5, decimal_places=0, null=False,blank=True)  # In chilogrammi
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
