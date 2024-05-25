from django.urls import path
from management import views
from gestione_palestra import settings
from django.conf.urls.static import static

urlpatterns = [
    #management
    path('create-group-training/', views.NewGroupTraining.as_view(), name='create-group-training'),
    path('create-plan/', views.CreatePlan.as_view(), name='create-plan'),
    path('edit-discounts/<int:plan_id>/', views.EditDiscounts.as_view(), name="edit-discounts"),
    path('edit-plan/<int:plan_id>/', views.EditPlan.as_view(), name="edit-plan"),
    path('edit-group-training/<int:course_id>/', views.EditGroupTraining.as_view(), name='edit-group-training'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



