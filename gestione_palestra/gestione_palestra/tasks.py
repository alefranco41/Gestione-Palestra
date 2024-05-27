# In tasks.py della tua app Django
from datetime import datetime
import pytz
from .celery import app
from management import models as management_models
from palestra import models as palestra_models

@app.task()
def delete_reservations():
    today = datetime.now(pytz.timezone('Europe/Rome'))
    if today.weekday() == 6 and today.hour >= 18:
        palestra_models.GroupClassReservation.objects.all().delete()
        palestra_models.PersonalTraining.objects.all().delete()

@app.task()
def reset_training_info():
    all_group_trainings = management_models.GroupTraining.objects.all()
    for group_training in all_group_trainings:
        if group_training.expired():
            group_training.total_partecipants = 0
            group_training.save()