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
from . import settings
from django.conf.urls.static import static

urlpatterns = [
    re_path(r"^$|^/$|^home/$", views.homepage, name="homepage"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
    path('create-group-training/', views.NewGroupTraining.as_view(), name='create-group-training'),
    path('edit-review/', views.EditReview.as_view(), name='edit-review'),
    path('edit-group-training/<int:course_id>/', views.EditGroupTraining.as_view(), name='edit-group-training'),
    path('book-workout/<int:pt_id>/', views.BookWorkout.as_view(), name="book-workout"),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('update-profile/', views.UpdateProfile.as_view(), name='update-profile'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('trainer-list/', views.TrainerListView.as_view(), name='trainer-list'),
    path('subscription-plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
    path('classes-schedule/', views.GymClassesView.as_view(), name='classes-schedule'),
    path('leave-review/', views.LeaveReview.as_view(), name='leave-review'),
    path('admin/', admin.site.urls)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



