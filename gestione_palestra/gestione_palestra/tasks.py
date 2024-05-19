# In tasks.py della tua app Django
from . import models
from datetime import datetime
import pytz
from .celery import app


@app.task()
def delete_reservations():
    today = datetime.now(pytz.timezone('Europe/Rome'))
    if today.weekday() == 6 and today.hour >= 18:
        models.GroupClassReservation.objects.all().delete()
        models.PersonalTraining.objects.all().delete()

@app.task()
def reset_training_info():
    all_group_trainings = models.GroupTraining.objects.all()
    for group_training in all_group_trainings:
        if group_training.ended():
            group_training.total_partecipants = 0
            group_training.save()