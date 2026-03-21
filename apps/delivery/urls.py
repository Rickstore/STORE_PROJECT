from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('dashboard/', views.DeliveryDashboardView.as_view(), name='dashboard'),
    path('profile/', views.LivreurProfileView.as_view(), name='profile'),
    path('changer-mot-de-passe/', views.ForceChangePasswordView.as_view(), name='force_change_password'),
    path('order/<str:order_number>/', views.DeliveryDetailView.as_view(), name='order_detail'),
    path('order/<str:order_number>/change-status/', views.ChangeDeliveryStatusView.as_view(), name='change_status'),
    path('order/<str:order_number>/confirm/', views.ConfirmDeliveryView.as_view(), name='confirm_delivery'),
    path('order/<str:order_number>/report-incident/', views.ReportIncidentView.as_view(), name='report_incident'),
]
