from django.urls import path
from django.contrib.auth import views as auth_views
from accounts import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('activate/<str:token>/', views.activate_account, name='activate_account'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_user, name='logout'),
    # API endpoints
    path('api/register/', views.register_user, name='register_user'),
    path('api/login/', views.login_user, name='login_user'),
    path('api/create-staff/', views.create_staff, name='create_staff'),
    path('api/update-staff/<int:staff_id>/', views.update_staff_profile, name='update_staff_profile'),
    path('api/update-profile/', views.update_profile, name='update_profile'),

    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
