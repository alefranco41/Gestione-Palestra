from django.test import TestCase
from datetime import datetime
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
import random
import math
from utils.functions import get_event_date
from palestra import views as palestra_views, models as palestra_models
from management import models as management_models



class GymClassesViewTestCase(TestCase):

    """
        Test prenotazione corsi di gruppo
        1)  Utente non autenticato
        2)  Utente membro dello staff
        3)  Utente con abbonamento sbagliato
        4)  Utente con abbonamento scaduto
        5)  Corso di gruppo pieno
        6)  Corso di gruppo terminato per questa settimnana
        7)  Utente ha già un allenamento prenotato allo stesso orario dello stesso giorno
        8)  Utente tenta di prenotarsi una seconda volta per un corso di gruppo a cui è già iscritto
        9) Utente cancella prenotazione
        10) Caso OK
        11) Utente non è abbonato
    """

    def setUp(self):
        self.test_trainer = palestra_models.User.objects.create(email="a.b@c.d", password="123", is_instructor=True)
        self.test_trainer_profile = palestra_models.TrainerProfile.objects.create(user=self.test_trainer, gender='M', first_name="Lorem", last_name="Ipsum", date_of_birth=datetime(year=2000, month=10, day=10))
        
        
        self.groupClass = management_models.GroupTraining.objects.create(trainer=self.test_trainer_profile, day="Sunday", start_hour=18, duration=30, max_participants=20, title="test")
        self.expired_group_class = management_models.GroupTraining.objects.create(trainer=self.test_trainer_profile, day="Monday", start_hour=9, duration=30, max_participants=20, title="test")
        
        self.subscription_plan = management_models.SubscriptionPlan.objects.create(name="Full Access Plan", plan_type="FULL", monthly_price=50.00)
        self.wrong_subscription_plan = management_models.SubscriptionPlan.objects.create(name="Gym Access Plan", plan_type="WEIGHTS", monthly_price=50.00)
        
        self.user_with_profile = palestra_models.User.objects.create(username="ciao", email="user@example.com", password="123")
        self.user_without_profile = palestra_models.User.objects.create(username="no_profile", email="user@ciao.com", password="123")
        self.user_with_wrong_subscription = palestra_models.User.objects.create(username="wrong_sub", email="123@gmail.com", password="1234")
        
        palestra_models.UserProfile.objects.create(user=self.user_with_profile, first_name="John", last_name="Doe", date_of_birth=datetime(year=2000, month=10, day=10), height=180, weight=90) 
        palestra_models.UserProfile.objects.create(user=self.user_with_wrong_subscription, first_name="John", last_name="Doe", date_of_birth=datetime(year=2000, month=10, day=10), height=180, weight=90) 
        palestra_models.Subscription.objects.create(user=self.user_with_profile, plan=self.subscription_plan, monthly_price=10, start_date=datetime.now().date(), end_date=datetime(year=2030, month=10, day=10), age_reduction=False)
        palestra_models.Subscription.objects.create(user=self.user_with_wrong_subscription, plan=self.wrong_subscription_plan, monthly_price=10, start_date=datetime.now().date(), end_date=datetime(year=2030, month=10, day=10), age_reduction=False)

    def tearDown(self):
        self.groupClass.delete()
        self.test_trainer_profile.delete()
        self.test_trainer.delete()

    def test_user_not_authenticated(self):
        self.client.logout()  # Assicurati che l'utente sia disconnesso
        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento al login

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You must login first" in messages[0].message)


    def test_user_is_staff_member(self):
        self.client.force_login(self.test_trainer)
        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You are a staff member" in messages[0].message)
    
    

    def test_no_profile_info(self):
        self.client.force_login(self.user_without_profile)

        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule
        
        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You must complete your profile first" in messages[0].message)

    def test_user_wrong_subscription(self):
        self.client.force_login(self.user_with_wrong_subscription)
        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("does not allow that" in messages[0].message)

    def test_user_subscription_expired(self):
        self.client.force_login(self.user_with_profile)
        palestra_models.Subscription.objects.get(user=self.user_with_profile).delete()
        palestra_models.Subscription.objects.create(user=self.user_with_profile, plan=self.subscription_plan, monthly_price=10, start_date=datetime.now().date(), end_date=datetime(year=2010, month=10, day=10), age_reduction=False)
        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina dei piani di abbonamento

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("Your subscription has expired" in messages[0].message)

    def test_group_class_full(self):
        self.client.force_login(self.user_with_profile)
        self.groupClass.total_partecipants = self.groupClass.max_participants
        self.groupClass.save()

        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)
        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule
        follow_response = self.client.get(response.url)

        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("group class you are trying to join is full" in messages[0].message)

    def test_group_class_ended_for_week(self):
        self.client.force_login(self.user_with_profile)
        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.expired_group_class.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("This group class has ended, come back the next week" in messages[0].message)

    def test_user_already_has_personal_training(self):
        self.client.force_login(self.user_with_profile)
        palestra_models.PersonalTraining.objects.create(user=self.user_with_profile, trainer=self.test_trainer_profile, day=self.groupClass.day, start_hour=self.groupClass.start_hour, training_type="General")

        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You have an upcoming personal training session already booked" in messages[0].message)


    def test_user_already_booked(self):
        self.client.force_login(self.user_with_profile)        
        palestra_models.GroupClassReservation.objects.create(user=self.user_with_profile, group_class=self.groupClass)

        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You are already booked in this class" in messages[0].message)

    def test_user_cancels_reservation(self):
        self.client.force_login(self.user_with_profile)
        reservation = palestra_models.GroupClassReservation.objects.create(user=self.user_with_profile, group_class=self.groupClass)
        old_partecipants = self.groupClass.total_partecipants
        response = self.client.post(reverse('palestra:dashboard'), {'group_training': self.groupClass.id}, follow=False)
        
        self.groupClass.refresh_from_db()
        new_partecipants = self.groupClass.total_partecipants

        self.assertEqual(new_partecipants, old_partecipants-1)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        self.assertTrue("The Group Class reservation has been cancelled" in messages[0].message)

    def test_successful_reservation(self):
        self.client.force_login(self.user_with_profile)
        old_partecipants = self.groupClass.total_partecipants
        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)
    
        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di conferma
        
        follow_response = self.client.get(response.url)
        self.groupClass.refresh_from_db()
        new_partecipants = self.groupClass.total_partecipants
        
        self.assertEqual(new_partecipants, old_partecipants+1)

        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        self.assertTrue("Group class joined successfully" in messages[0].message)
    
    def test_user_is_not_a_member(self):
        self.client.force_login(self.user_with_profile)
        management_models.SubscriptionPlan.objects.get(id=self.subscription_plan.id).delete()
        response = self.client.post(reverse('palestra:classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You are not a member" in messages[0].message)



class GetReviewsTestCase(TestCase):
    """
        Test funzione che mostra le recensioni nella dashboard in base al tipo di utente
        1)  Utente non autenticato -> verificare che non vengano mostrate recensioni
        2)  Utente autenticato -> verificare che vengano mostrate tutte le recensioni che ha scritto
        2)  Utente Istruttore -> verificare che venagno mostrate solo le recensioni su di lui
        3)  Utente Manager -> verificare che vengano mostrate tutte le recensioni
        6)  Dopo cancellazione -> verificare che vengano mostrate tutte le recensioni tranne quella cancellata per ogni tipo di utente
        7)  Dopo modifica -> verificare che la recensione modificata venga visualizzata correttamente per ogni tipo di utente
    """
    def setUp(self):

        self.manager = palestra_models.User.objects.create(username=f"manager", email=f"manager@gmail.com", password="123", is_manager=True)
        self.manager.save()

        normal_users = []
        for i in range(100):
            random_user = palestra_models.User.objects.create(username=f"user_{i}", email=f"email_user_{i}@gmail.com", password="123")
            random_user.save()
            random_user_profile = palestra_models.UserProfile.objects.create(user_id=random_user.id, user=random_user, first_name=f"first name {i}", last_name=f"last name {i}", date_of_birth=datetime(1999, 10, 10), height=189, weight=100)
            random_user_profile.save()
            normal_users.append(random_user)
        
        self.normal_users = normal_users

        random_trainers = []
        for i in range(1):
            random_trainer = palestra_models.User.objects.create(username=f"trainer_{i}", email=f"email_{i}@gmail.com", password="123", is_instructor=True)
            random_trainer.save()
            random_trainer_profile = palestra_models.TrainerProfile.objects.create(user_id=random_trainer.id, user=random_trainer, first_name=f"first name {i}", last_name=f"last name {i}", date_of_birth=datetime(1999, 10, 10))
            random_trainer_profile.save()
            random_trainers.append(random_trainer_profile)

        self.trainers = random_trainers

        reviews = []
        for i in range(500):
            random_fitness_goal = management_models.FitnessGoal.objects.create(name=f"Fitness Goal {i}")
            random_fitness_goal.save()
            trainer=random.choice(random_trainers)
            user = random.choice(self.normal_users)

            if i % 2:
                pt_event = palestra_models.CompletedPersonalTraining.objects.create(trainer=trainer,
                                                                  user=user,
                                                                  day=random.choice(palestra_models.PersonalTraining.DAY_CHOICES)[0],
                                                                  start_hour=random.choice(palestra_models.PersonalTraining.START_HOUR_CHOICES)[0],
                                                                  training_type=random_fitness_goal.id, completed_date=datetime.now())
                pt_event.save()
                
                review = palestra_models.PersonalTrainingReview.objects.create(event=pt_event, trainer=trainer, user=user, stars=math.floor(i/2), title=f"Title_{i}")
                review.event_type = "personal_training"
                review.save()
            else:
                gt_event = management_models.GroupTraining.objects.create(trainer=trainer, max_participants=30, duration=30, title=f"title{i}",
                                                               day=random.choice(palestra_models.PersonalTraining.DAY_CHOICES)[0],
                                                               start_hour=random.choice(palestra_models.PersonalTraining.START_HOUR_CHOICES)[0])
                gt_event.save()

                completed_group_training = palestra_models.CompletedGroupTrainingReservation(
                    group_class=gt_event,
                    user=user,
                    completed_date=get_event_date(gt_event)
                )
                completed_group_training.save()

                review = palestra_models.GroupTrainingReview.objects.create(event=completed_group_training, user=user, stars=math.floor(i/2), title=f"Title_{i}")
                review.trainer = trainer
                review.event_type = "group_training"
                review.save()
            
            reviews.append(review)
        
        self.reviews = reviews

                
    def test_user_not_authenticated(self):
        reviews = palestra_views.get_reviews(AnonymousUser())
        #l'utente anonimo non vede recensioni
        self.assertListEqual(reviews, [])
    
    #All'inizio
    def test_user_authenticated(self):
        random_user = random.choice(self.normal_users)
        reviews = palestra_views.get_reviews(random_user)
        
        filtered_reviews = set()
        for review in self.reviews:
            if review.user == random_user:
                filtered_reviews.add(review)
        #l'utente vede tutte le sue recensioni
        self.assertSetEqual(set(reviews),  filtered_reviews)

    #Dopo la modifica
    def test_user_authenticated_after_edit(self):
        random_user = random.choice(self.normal_users)
        self.client.force_login(random_user)
        review_to_edit = random.choice([review for review in self.reviews if review.user == random_user])


        if isinstance(review_to_edit, palestra_models.PersonalTrainingReview):
            data = {
                        'user': random_user.id,
                        'event':review_to_edit.event.id,
                        'event_type':review_to_edit.event_type,
                        'stars':3,
                        'title':"NEW TITLE",
                        'additional_info':"NEW ADDITIONAL INFO",
                        'trainer':review_to_edit.event.trainer.id,
                    }
        else:
            data = {
                        'user': random_user.id,
                        'event':review_to_edit.event.id,
                        'event_type':review_to_edit.event_type,
                        'stars':3,
                        'title':"NEW TITLE",
                        'additional_info':"NEW ADDITIONAL INFO",
                    }
        
        response = self.client.post(path=reverse('palestra:edit-review'), data=data, follow=False)
        self.assertEqual(response.status_code, 302)  
        follow_response = self.client.get(response.url)

        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        self.assertTrue("Your review has been successfully edited" in messages[0].message)
        
        review_to_edit.refresh_from_db()
        #l'utente vede la recensione modificata

        for review in palestra_views.get_reviews(random_user):
            if review.id == review_to_edit.id:
                new_review = review
                break

        self.assertEqual(new_review.title, "NEW TITLE")
        self.assertEqual(new_review.additional_info, "NEW ADDITIONAL INFO")

        filtered_reviews = set()
        for review in self.reviews:
            if review.user == random_user:
                filtered_reviews.add(review)
        self.assertSetEqual(set(palestra_views.get_reviews(random_user)),  filtered_reviews)

    #Dopo la cancellazione
    def test_user_authenticated_after_deletion(self):
        random_user = random.choice(self.normal_users)
        self.client.force_login(random_user)
        filtered_reviews = [review for review in self.reviews if review.user == random_user]
        review_to_delete = random.choice(filtered_reviews)
        data = {
                'event_id':review_to_delete.event.id,
                'event_type':review_to_delete.event_type,
                }

        response = self.client.get(path=reverse('palestra:dashboard'), data=data, follow=False)
        self.assertEqual(response.status_code, 302)  
        follow_response = self.client.get(response.url)

        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        self.assertTrue("Review deleted successfully" in messages[0].message)
        #La recensione non c'è più
        
        if isinstance(review_to_delete, palestra_models.GroupTrainingReview):
            with self.assertRaises(palestra_models.GroupTrainingReview.DoesNotExist):
                review_to_delete.refresh_from_db()
        else:
            with self.assertRaises(palestra_models.PersonalTrainingReview.DoesNotExist):
                review_to_delete.refresh_from_db()

        #l'utente vede una recensione in meno dopom la cancellazione
        self.assertEqual(len(filtered_reviews) - 1, len(palestra_views.get_reviews(random_user)))

    def test_trainer(self):
        random_trainer_profile = random.choice(self.trainers)
        random_trainer = palestra_models.User.objects.get(username=random_trainer_profile.user)
        reviews = palestra_views.get_reviews(random_trainer)
        
        
        filtered_reviews = set([review for review in self.reviews if review.trainer.user == random_trainer])
        
        #Il personal trainer vede tutte le sue recensioni
        self.assertSetEqual(set(reviews),  filtered_reviews)

    def test_trainer_after_edit(self):
        random_user = random.choice(self.normal_users)
        self.client.force_login(random_user)
        review_to_edit = random.choice([review for review in self.reviews if review.user == random_user and isinstance(review, palestra_models.PersonalTrainingReview)])

        if isinstance(review_to_edit, palestra_models.PersonalTrainingReview):
            data = {
                        'user': random_user.id,
                        'event':review_to_edit.event.id,
                        'event_type':review_to_edit.event_type,
                        'stars':3,
                        'title':"NEW TITLE",
                        'additional_info':"NEW ADDITIONAL INFO",
                        'trainer':review_to_edit.event.trainer.id,
                    }
        else:
            data = {
                        'user': random_user.id,
                        'event':review_to_edit.event.id,
                        'event_type':review_to_edit.event_type,
                        'stars':3,
                        'title':"NEW TITLE",
                        'additional_info':"NEW ADDITIONAL INFO",
                    }
        

        response = self.client.post(path=reverse('palestra:edit-review'), data=data, follow=False)
        review_to_edit.refresh_from_db()

        
        random_trainer = palestra_models.User.objects.get(username=review_to_edit.event.trainer.user)
        self.client.force_login(random_trainer)
        
        for review in palestra_views.get_reviews(random_trainer):  
            if review.id == review_to_edit.id and review.event_type == review_to_edit.event_type:
                new_review = review
                break

        #il Personal trainer vede la recensione modificata
        self.assertEqual(new_review.title, "NEW TITLE")
        self.assertEqual(new_review.additional_info, "NEW ADDITIONAL INFO")
        
        filtered_reviews = set([review for review in self.reviews if review.trainer.user == random_trainer])
        self.assertSetEqual(set(palestra_views.get_reviews(random_trainer)),  filtered_reviews)

    def test_trainer_after_deletion(self):
        random_user = random.choice(self.normal_users)
        self.client.force_login(random_user)
        review_to_delete = random.choice([review for review in self.reviews if review.user == random_user and isinstance(review, palestra_models.PersonalTrainingReview)])

        data = {
                'event_id':review_to_delete.event.id,
                'event_type':review_to_delete.event_type,
                }
        
        response = self.client.get(path=reverse('palestra:dashboard'), data=data, follow=False)
        
        random_trainer = palestra_models.User.objects.get(username=review_to_delete.event.trainer.user)
        self.client.force_login(random_trainer)
        if isinstance(review_to_delete, palestra_models.GroupTrainingReview):
            with self.assertRaises(palestra_models.GroupTrainingReview.DoesNotExist):
                review_to_delete.refresh_from_db()
        else:
            with self.assertRaises(palestra_models.PersonalTrainingReview.DoesNotExist):
                review_to_delete.refresh_from_db()

        
        self.assertEqual(len([review for review in self.reviews if review.trainer.user == random_trainer]) - 1, len(palestra_views.get_reviews(random_trainer)))
        


    def test_manager(self):
        #Il manager vede tutte le recensioni
        self.assertTrue(len(self.reviews), len(palestra_views.get_reviews(self.manager)))

    def test_manager_after_edit(self):
        random_user = random.choice(self.normal_users)
        self.client.force_login(random_user)
        review_to_edit = random.choice([review for review in self.reviews if review.user == random_user])

        if isinstance(review_to_edit, palestra_models.PersonalTrainingReview):
            data = {
                        'user': random_user.id,
                        'event':review_to_edit.event.id,
                        'event_type':review_to_edit.event_type,
                        'stars':3,
                        'title':"NEW TITLE",
                        'additional_info':"NEW ADDITIONAL INFO",
                        'trainer':review_to_edit.event.trainer.id,
                    }
        else:
            data = {
                        'user': random_user.id,
                        'event':review_to_edit.event.id,
                        'event_type':review_to_edit.event_type,
                        'stars':3,
                        'title':"NEW TITLE",
                        'additional_info':"NEW ADDITIONAL INFO",
                    }
        

        response = self.client.post(path=reverse('palestra:edit-review'), data=data, follow=False)
        review_to_edit.refresh_from_db()

        
        
        self.client.force_login(self.manager)

        for review in palestra_views.get_reviews(self.manager):  
            if review.id == review_to_edit.id and review.event_type == review_to_edit.event_type:
                new_review = review
                break

        #il Personal trainer vede la recensione modificata
        self.assertEqual(new_review.title, "NEW TITLE")
        self.assertEqual(new_review.additional_info, "NEW ADDITIONAL INFO")
        
        self.assertEqual(len(self.reviews), len(palestra_views.get_reviews(self.manager)))

    def test_manager_after_deletion(self):
        random_user = random.choice(self.normal_users)
        self.client.force_login(random_user)
        filtered_reviews = [review for review in self.reviews if review.user == random_user]
        review_to_delete = random.choice(filtered_reviews)
        data = {
                'event_id':review_to_delete.event.id,
                'event_type':review_to_delete.event_type,
                }

        response = self.client.get(path=reverse('palestra:dashboard'), data=data, follow=False)
        if isinstance(review_to_delete, palestra_models.GroupTrainingReview):
            with self.assertRaises(palestra_models.GroupTrainingReview.DoesNotExist):
                review_to_delete.refresh_from_db()
        else:
            with self.assertRaises(palestra_models.PersonalTrainingReview.DoesNotExist):
                review_to_delete.refresh_from_db()

        self.client.force_login(self.manager)
        self.assertEqual(len(self.reviews) - 1, len(palestra_views.get_reviews(self.manager)))