from django.contrib import admin
from django.urls import path, re_path, include
from . import views, settings
from django.conf.urls.static import static

urlpatterns = [
    #gestione_palestra
    re_path(r"^$|^/$|^home/$", views.HomePage.as_view(), name="homepage"),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name="logout"),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('admin/', admin.site.urls),
    path('management/', include(('management.urls', 'management'), namespace='management')),
    path('palestra/', include(('palestra.urls', 'palestra'), namespace='palestra')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



