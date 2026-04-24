from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('dashboard/',                    views.dashboard,        name='dashboard'),
    path('confirm/<int:order_id>/',       views.confirm_delivery, name='confirm_delivery'),
    path('failed/<int:order_id>/',        views.report_failed,    name='report_failed'),
]
