# In tasks.py della tua app Django
from celery import shared_task
from . import models
import datetime
import pytz
from celery import Task

class DeleteReservations(Task):
    @shared_task
    def run(self, *args, **kwargs):
        today = datetime.now(pytz.timezone('Europe/Rome'))
        if today.weekday() == 6 and today.hour >= 18:
            models.GroupClassReservation.objects.all().delete()
            models.PersonalTraining.objects.all().delete()

class ResetTrainingInfo(Task):
    @shared_task
    def run(self, *args, **kwargs):
        all_group_trainings = models.GroupTraining.objects.all()
        for group_training in all_group_trainings:
            if group_training.ended():
                group_training.total_partecipants = 0
                group_training.save()