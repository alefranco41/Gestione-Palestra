# In tasks.py della tua app Django
from datetime import datetime
import pytz
from .celery import app
from management import models as management_models
from palestra import models as palestra_models

@app.task()
def reset_training_info():
    all_group_trainings = management_models.GroupTraining.objects.all()
    all_personal_training = palestra_models.PersonalTraining.objects.all()

    for group_training in all_group_trainings:
        if group_training.expired():
            palestra_models.GroupClassReservation.objects.filter(group_class=group_training).delete()
            group_training.total_partecipants = 0
            group_training.save()
    
    for personal_training in all_personal_training:
        if personal_training.expired():
            personal_training.delete()