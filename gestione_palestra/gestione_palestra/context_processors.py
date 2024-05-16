from datetime import datetime, date
from . import models
import pytz

week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_mapping = {
                'Monday': 0,
                'Tuesday': 1,
                'Wednesday': 2,
                'Thursday': 3,
                'Friday': 4,
                'Saturday': 5,
                'Sunday': 6
            }
today = datetime.now(pytz.timezone('Europe/Rome'))

def global_context(request):
    plans = models.SubscriptionPlan.objects.all()
    for plan in plans:
        plan.discount_percentage = {}
        plan.full_price = plan.monthly_price
        plan.discounted_price = plan.monthly_price - plan.age_discount
        plan.full_discounted_price = plan.discounted_price
        for duration, label in plan.DURATION_CHOICES:
            plan.discount_percentage[duration] = models.DurationDiscount.objects.get(duration=duration, subscription_plan=plan).discount_percentage

    fitness_goals_choices = models.FitnessGoal.objects.all()

    fitness_goals = [(goal.id, goal.name) for goal in fitness_goals_choices]
        

    context =   {
                    'gym_name': 'Fit4All',
                    'now': date.today,
                    'subscription_plans':plans,
                    'fitness_goals':fitness_goals,
                    'days':week_days,
                    'hours':range(9,19)
                }
    
    return context


