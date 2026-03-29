from django.urls import path
from payments import views

urlpatterns = [
    path('pay/<int:plan_id>/', views.initiate_payment, name='initiate_payment'),
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),
]
