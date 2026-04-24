from django.urls import path
from django.views.generic import RedirectView
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
]