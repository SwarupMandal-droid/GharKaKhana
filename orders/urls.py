from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('',               views.order_list,   name='order_list'),
    path('cart/',          views.cart,         name='cart'),
    path('place/',         views.place_order,  name='place_order'),
    path('<int:pk>/',      views.order_detail, name='order_detail'),
    path('<int:pk>/review/', views.submit_review, name='submit_review'),
]
