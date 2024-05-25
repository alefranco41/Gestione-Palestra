from django.contrib import messages
from datetime import timedelta, datetime
from . import global_variables

def print_errors(form, request):
    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f"{field}: {error}")

def get_fitness_goals(trainer_profile):
    fitness_goals = trainer_profile.fitness_goals.all()
    fitness_goal_names = [fitness_goal.name for fitness_goal in fitness_goals]
    return fitness_goal_names

def get_event_date(event):
    week_day = global_variables.day_mapping[event.day] 
    date = global_variables.today.date() - timedelta(days=global_variables.today.weekday()) + timedelta(days=week_day)
    date = datetime.combine(date, datetime.min.time())
    date = date.replace(hour=event.start_hour) 

    return date