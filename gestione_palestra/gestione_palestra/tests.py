from django.test import TestCase
from datetime import datetime
from django.urls import reverse
from . import models


class GroupClassReservationTestCase(TestCase):
    def setUp(self):
        self.test_trainer = models.User.objects.create(email="a.b@c.d", password="123", is_instructor=True)
        self.test_trainer_profile = models.TrainerProfile.objects.create(user=self.test_trainer, gender='M', first_name="Lorem", last_name="Ipsum", date_of_birth=datetime(year=2000, month=10, day=10))
        self.groupClass = models.GroupTraining.objects.create(trainer=self.test_trainer_profile, day="Sunday", start_hour=18, duration=30, max_participants=20, title="test")
        self.expired_group_class = models.GroupTraining.objects.create(trainer=self.test_trainer_profile, day="Monday", start_hour=9, duration=30, max_participants=20, title="test")
        self.subscription_plan = models.SubscriptionPlan.objects.create(name="Full Access Plan", plan_type="FULL", monthly_price=50.00)
        self.wrong_subscription_plan = models.SubscriptionPlan.objects.create(name="Gym Access Plan", plan_type="WEIGHTS", monthly_price=50.00)
        self.user_with_profile = models.User.objects.create(username="ciao", email="user@example.com", password="123")
        self.user_without_profile = models.User.objects.create(username="no_profile", email="user@ciao.com", password="123")
        self.user_with_wrong_subscription = models.User.objects.create(username="wrong_sub", email="123@gmail.com", password="1234")
        
        models.UserProfile.objects.create(user=self.user_with_profile, first_name="John", last_name="Doe", date_of_birth=datetime(year=2000, month=10, day=10), height=180, weight=90) 
        models.UserProfile.objects.create(user=self.user_with_wrong_subscription, first_name="John", last_name="Doe", date_of_birth=datetime(year=2000, month=10, day=10), height=180, weight=90) 
        models.Subscription.objects.create(user=self.user_with_profile, plan=self.subscription_plan, monthly_price=10, start_date=datetime.now().date(), end_date=datetime(year=2030, month=10, day=10), age_reduction=False)
        models.Subscription.objects.create(user=self.user_with_wrong_subscription, plan=self.wrong_subscription_plan, monthly_price=10, start_date=datetime.now().date(), end_date=datetime(year=2030, month=10, day=10), age_reduction=False)

    def tearDown(self):
        self.groupClass.delete()
        self.test_trainer_profile.delete()
        self.test_trainer.delete()

    def test_user_not_authenticated(self):
        self.client.logout()  # Assicurati che l'utente sia disconnesso
        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento al login

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You must login first" in messages[0].message)

    def test_user_is_staff_member(self):
        self.client.force_login(self.test_trainer)
        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You are a staff member" in messages[0].message)

    def test_no_profile_info(self):
        self.client.force_login(self.user_without_profile)

        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule
        
        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You must complete your profile first" in messages[0].message)

    def test_user_wrong_subscription(self):
        self.client.force_login(self.user_with_wrong_subscription)
        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("does not allow that" in messages[0].message)

    def test_user_subscription_expired(self):
        self.client.force_login(self.user_with_profile)
        models.Subscription.objects.get(user=self.user_with_profile).delete()
        models.Subscription.objects.create(user=self.user_with_profile, plan=self.subscription_plan, monthly_price=10, start_date=datetime.now().date(), end_date=datetime(year=2010, month=10, day=10), age_reduction=False)
        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

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

        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)
        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule
        follow_response = self.client.get(response.url)

        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("group class you are trying to join is full" in messages[0].message)

    def test_group_class_ended_for_week(self):
        self.client.force_login(self.user_with_profile)
        response = self.client.post(reverse('classes-schedule'), {'class_id': self.expired_group_class.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("This group class has ended, come back the next week" in messages[0].message)

    def test_user_already_has_personal_training(self):
        self.client.force_login(self.user_with_profile)
        models.PersonalTraining.objects.create(user=self.user_with_profile, trainer=self.test_trainer_profile, day=self.groupClass.day, start_hour=self.groupClass.start_hour, training_type="General")

        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You have an upcoming personal training session already booked" in messages[0].message)

    def test_user_already_has_group_class(self):
        self.client.force_login(self.user_with_profile)        
        models.GroupClassReservation.objects.create(user=self.user_with_profile, group_class=self.groupClass)

        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertTrue("You are already booked in this class" in messages[0].message)

    def test_user_cancels_reservation(self):
        self.client.force_login(self.user_with_profile)
        reservation = models.GroupClassReservation.objects.create(user=self.user_with_profile, group_class=self.groupClass)
        old_partecipants = self.groupClass.total_partecipants
        response = self.client.post(reverse('dashboard'), {'group_training': self.groupClass.id}, follow=False)
        
        self.groupClass.refresh_from_db()
        new_partecipants = self.groupClass.total_partecipants

        self.assertEqual(new_partecipants, old_partecipants-1)

        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di schedule

        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        self.assertTrue("The Group Class reservation has been cancelled" in messages[0].message)

    def test_successful_group_class_reservation(self):
        self.client.force_login(self.user_with_profile)
        old_partecipants = self.groupClass.total_partecipants
        response = self.client.post(reverse('classes-schedule'), {'class_id': self.groupClass.id}, follow=False)
        


        self.assertEqual(response.status_code, 302)  # Verifica il reindirizzamento alla pagina di conferma
        
        follow_response = self.client.get(response.url)
        self.groupClass.refresh_from_db()
        new_partecipants = self.groupClass.total_partecipants
        
        self.assertEqual(new_partecipants, old_partecipants+1)

        messages = list(follow_response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        self.assertTrue("Group class joined successfully" in messages[0].message)
