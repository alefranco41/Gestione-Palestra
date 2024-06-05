# In tasks.py della tua app Django
from .celery import app
from management import models as management_models
from palestra import models as palestra_models
from utils.functions import get_event_date




@app.task()
def reset_training_info():
    print("Checking for ended events...")
    all_group_trainings = management_models.GroupTraining.objects.all().iterator()
    all_personal_training = palestra_models.PersonalTraining.objects.all().iterator()

    for group_training in all_group_trainings:
        if group_training.expired():
            reservation_objects = palestra_models.GroupClassReservation.objects.filter(group_class=group_training)
            if reservation_objects:
                print(f"The group training with id={group_training.id} has ended, deleting all reservations...")
            for reservation in reservation_objects:
                completed_group_training = palestra_models.CompletedGroupTrainingReservation(
                    group_class=group_training,
                    user=reservation.user,
                    completed_date=get_event_date(group_training)
                )
                completed_group_training.save()
                reservation.delete()

    for personal_training in all_personal_training:
        if personal_training.expired():
            print(f"The personal training session with id={personal_training.id} has ended, deleting the reservation...")
            completed_training = palestra_models.CompletedPersonalTraining(
                trainer=personal_training.trainer,
                user=personal_training.user,
                day=personal_training.day,
                start_hour=personal_training.start_hour,
                training_type=personal_training.training_type,
                additional_info=personal_training.additional_info,
                completed_date=get_event_date(personal_training)
            )
            completed_training.save()
            personal_training.delete()