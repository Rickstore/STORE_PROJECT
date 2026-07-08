from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('webhook/notchpay/', views.notchpay_webhook, name='notchpay_webhook'),
]
