from django.urls import path
from . import cook_views

app_name = 'cook'

urlpatterns = [
    path('dashboard/',  cook_views.dashboard,    name='dashboard'),
    path('dishes/',     cook_views.dish_list,    name='dish_list'),
    path('dishes/add/', cook_views.dish_add,     name='dish_add'),
    path('dishes/edit/<int:pk>/', cook_views.dish_edit, name='dish_edit'),
    path('menu/',       cook_views.menu_list,    name='menu_list'),
    path('menu/create/',cook_views.menu_create,  name='menu_create'),
    path('menu/edit/<int:pk>/', cook_views.menu_edit, name='menu_edit'),
    path('menu/<int:menu_id>/add-item/', cook_views.menu_item_add, name='menu_item_add'),
    path('menu/item/<int:item_id>/remove/', cook_views.menu_item_remove, name='menu_item_remove'),
    path('orders/',     cook_views.order_list,   name='order_list'),
    path('orders/<int:pk>/', cook_views.order_detail, name='order_detail'),
    path('orders/<int:pk>/status/', cook_views.order_status_update, name='order_status_update'),
    path('onboarding/', cook_views.onboarding,   name='onboarding'),
    path('slots/',      cook_views.slot_list,    name='slot_list'),
    path('slots/add/',  cook_views.slot_add,     name='slot_add'),
    path('slots/<int:pk>/delete/', cook_views.slot_delete, name='slot_delete'),
    path('settings/',   cook_views.settings_view,name='settings'),
]
