from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('',               views.order_list,   name='order_list'),
    path('cart/',          views.cart,         name='cart'),
    path('place/',         views.place_order,  name='place_order'),
    path('<int:pk>/',      views.order_detail, name='order_detail'),
    path('<int:pk>/payment/', views.payment_page, name='payment_page'),
    path('<int:pk>/payment/callback/', views.payment_callback, name='payment_callback'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('<int:pk>/review/', views.submit_review, name='submit_review'),
    path('<int:pk>/archive/', views.archive_order, name='archive_order'),
    path('update-location/', views.update_location, name='update_location'),
]
