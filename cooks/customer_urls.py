from django.urls import path
from . import customer_views

app_name = 'customer'

urlpatterns = [
    path('',           customer_views.cook_list,   name='home'),
    path('<int:pk>/',  customer_views.cook_detail,  name='cook_detail'),
]
