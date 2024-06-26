from datetime import date
import decimal
from palestra import models as palestra_models
import random
from management import models as management_models
from utils import global_variables

def global_context(request):
    plans = management_models.SubscriptionPlan.objects.all()
    n_plans = len([plan for plan in plans if plan.is_active])
    for plan in plans:
        plan.discount_percentage = {}
        plan.full_price = plan.monthly_price
        plan.discounted_price = plan.monthly_price - plan.age_discount
        plan.full_discounted_price = plan.discounted_price   
        plan.DURATION_CHOICES = management_models.DurationDiscount.DURATION_CHOICES     
        for duration, label in management_models.DurationDiscount.DURATION_CHOICES:
            try:
                discount = management_models.DurationDiscount.objects.get(duration=duration, subscription_plan=plan).discount_percentage
                if discount:
                    plan.discount_percentage[duration] = discount
                else:
                    plan.discount_percentage[duration] = decimal.Decimal(0)
            except management_models.DurationDiscount.DoesNotExist:
                plan.discount_percentage[duration] = decimal.Decimal(0)

        plan.full_3 =  round(3 * plan.monthly_price * (1 - plan.discount_percentage[3] / 100), 2)
        plan.reduced_3 = round(3 * (plan.monthly_price * (1 - plan.discount_percentage[3] / 100) - plan.age_discount), 2)

        plan.full_6 =  round(6 * plan.monthly_price * (1 - plan.discount_percentage[6] / 100), 2)
        plan.reduced_6 = round(6 * (plan.monthly_price * (1 - plan.discount_percentage[6] / 100) - plan.age_discount), 2)

        plan.full_12 =  round(12 * plan.monthly_price * (1 - plan.discount_percentage[12] / 100), 2)
        plan.reduced_12 = round(12 * (plan.monthly_price * (1 - plan.discount_percentage[12] / 100) - plan.age_discount), 2)


    pt_reviews = palestra_models.PersonalTrainingReview.objects.all()
    gc_reviews = palestra_models.GroupTrainingReview.objects.all()

    all_reviews = []
    all_reviews.extend(pt_reviews)
    all_reviews.extend(gc_reviews)
    
    for review in all_reviews:
        if isinstance(review, palestra_models.GroupTrainingReview):
            review.event_type = "group_training"
        else:
            review.training_type = palestra_models.FitnessGoal.objects.get(id=review.event.training_type).name
            review.event_type = "personal_training"

    random.shuffle(all_reviews)
    fitness_goals_choices = management_models.FitnessGoal.objects.all()

    fitness_goals = [(goal.id, goal.name) for goal in fitness_goals_choices]
    
    n_fitness_goals = len(fitness_goals)
    
    trainers = palestra_models.TrainerProfile.objects.all()
    n_trainers = len(trainers)

    n_group_classes = len(management_models.GroupTraining.objects.all())
    context =   {
                    'gym_name': 'Fit4All',
                    'now': date.today,
                    'subscription_plans':plans,
                    'fitness_goals':fitness_goals,
                    'days':global_variables.week_days,
                    'hours':range(9,19),
                    'trainers':trainers,
                    'n_trainers':n_trainers,
                    'n_group_classes':n_group_classes,
                    'n_fitness_goals':n_fitness_goals,
                    'n_plans':n_plans,
                    'reviews':all_reviews
                }
    
    return context


