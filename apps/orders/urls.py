from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('success/<str:order_number>/', views.order_success, name='order_success'),
    path('history/', views.order_history, name='order_history'),
    path('export-pdf/<str:order_number>/', views.export_order_pdf, name='export_order_pdf'),
]
