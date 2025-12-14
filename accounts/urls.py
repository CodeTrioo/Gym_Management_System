from django.contrib import admin
from django.urls import path
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/register/', views.register_user),
    path('api/login/', views.login_user),
    path('api/logout/', views.logout_user),
   
]
