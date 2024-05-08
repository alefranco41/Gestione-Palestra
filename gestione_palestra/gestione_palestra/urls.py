"""
URL configuration for gestione_palestra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path(r"^$|^/$|^home/$", views.homepage, name="homepage"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
    path('account/<int:user_id>/', views.AccountView.as_view(), name='account'),
    path('profile/<int:user_id>/', views.ProfileView.as_view(), name='profile'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('trainer-list/', views.TrainerListView.as_view(), name='trainer-list'),
    path('subscription-plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('classes-schedule/', views.GymClassesView.as_view(), name='classes-schedule'),
    path('admin/', admin.site.urls)
]
