from datetime import datetime, date
from . import models
import decimal
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
        plan.DURATION_CHOICES = models.DurationDiscount.DURATION_CHOICES     
        for duration, label in models.DurationDiscount.DURATION_CHOICES:
            try:
                plan.discount_percentage[duration] = models.DurationDiscount.objects.get(duration=duration, subscription_plan=plan).discount_percentage
            except models.DurationDiscount.DoesNotExist:
                plan.discount_percentage[duration] = decimal.Decimal(0)

        plan.full_3 =  round(3 * plan.monthly_price * (1 - plan.discount_percentage[3] / 100), 2)
        plan.reduced_3 = round(3 * (plan.monthly_price * (1 - plan.discount_percentage[3] / 100) - plan.age_discount), 2)

        plan.full_6 =  round(6 * plan.monthly_price * (1 - plan.discount_percentage[6] / 100), 2)
        plan.reduced_6 = round(6 * (plan.monthly_price * (1 - plan.discount_percentage[6] / 100) - plan.age_discount), 2)

        plan.full_12 =  round(12 * plan.monthly_price * (1 - plan.discount_percentage[12] / 100), 2)
        plan.reduced_12 = round(12 * (plan.monthly_price * (1 - plan.discount_percentage[12] / 100) - plan.age_discount), 2)



    fitness_goals_choices = models.FitnessGoal.objects.all()

    fitness_goals = [(goal.id, goal.name) for goal in fitness_goals_choices]
    
    trainers = models.TrainerProfile.objects.all()

    context =   {
                    'gym_name': 'Fit4All',
                    'now': date.today,
                    'subscription_plans':plans,
                    'fitness_goals':fitness_goals,
                    'days':week_days,
                    'hours':range(9,19),
                    'trainers':trainers
                }
    
    return context


