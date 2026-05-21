from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Client account
    path('profile/', views.profile_view, name='profile'),

    path('orders/', views.order_history_view, name='order_history'),
    path('orders/<str:order_number>/track/', views.order_track_view, name='order_track'),
    path('orders/<str:order_number>/invoice/', views.invoice_download, name='invoice_download'),

    # Password reset (Django built-in)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        html_email_template_name='users/password_reset_email_html.html',
        subject_template_name='users/password_reset_subject.txt',
        success_url='/auth/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url='/auth/reset/done/',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html',
    ), name='password_reset_complete'),
]
