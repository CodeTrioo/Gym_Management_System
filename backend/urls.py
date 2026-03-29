from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gym.urls')),
    path('', include('accounts.urls')),
    path('payments/', include('payments.urls')),
]
