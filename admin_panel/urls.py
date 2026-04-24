from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('',                          views.dashboard,       name='dashboard'),
    path('cooks/',                    views.cook_approvals,  name='cook_approvals'),
    path('cooks/<int:pk>/approve/',   views.approve_cook,    name='approve_cook'),
    path('cooks/<int:pk>/reject/',    views.reject_cook,     name='reject_cook'),
    path('orders/',                   views.all_orders,      name='all_orders'),
    path('stats/',                    views.platform_stats,  name='stats'),
]
