import datetime 
from . import models

def global_context(request):
    plans = models.SubscriptionPlan.objects.all()
    for plan in plans:
        plan.discounted_price = plan.monthly_price - plan.age_discount

    context =   {
                    'gym_name': 'Fit4All',
                    'now': datetime.date.today,
                    'subscription_plans':plans
                }
    
    return context


