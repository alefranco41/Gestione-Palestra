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
