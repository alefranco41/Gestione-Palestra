import datetime 
from . import models

week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def global_context(request):
    plans = models.SubscriptionPlan.objects.all()
    fitness_goals_choices = models.FitnessGoal.objects.all()

    fitness_goals = [(goal.id, goal.name) for goal in fitness_goals_choices]
    for plan in plans:
        plan.discounted_price = plan.monthly_price - plan.age_discount

    context =   {
                    'gym_name': 'Fit4All',
                    'now': datetime.date.today,
                    'subscription_plans':plans,
                    'fitness_goals':fitness_goals,
                    'days':week_days,
                    'hours':range(9,19)
                }
    
    return context

