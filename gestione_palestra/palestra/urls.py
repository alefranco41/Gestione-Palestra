from django.urls import path
from palestra import views
from gestione_palestra import settings
from django.conf.urls.static import static

urlpatterns = [
    #palestra
    path('subscription-plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('trainer-list/', views.TrainerListView.as_view(), name='trainer-list'),
    path('classes-schedule/', views.GymClassesView.as_view(), name='classes-schedule'),
    path('book-workout/<int:pt_id>/', views.BookWorkout.as_view(), name="book-workout"),
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('update-profile/', views.UpdateProfile.as_view(), name='update-profile'),
    path('edit-review/', views.EditReview.as_view(), name='edit-review'),
    path('leave-review/', views.LeaveReview.as_view(), name='leave-review'),

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



