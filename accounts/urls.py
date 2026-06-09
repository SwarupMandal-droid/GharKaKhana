from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('',          RedirectView.as_view(url='/accounts/login/')),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),
    path('register/', views.register_view, name='register'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('profile/',  views.profile_view,  name='profile'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/edit/<int:pk>/', views.edit_address, name='edit_address'),

    # Password reset flow
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/',
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset/complete/',
         ),
         name='password_reset_confirm'),

    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]