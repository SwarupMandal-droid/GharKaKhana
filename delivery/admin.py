from django.contrib import admin
from .models import DeliveryPerson, Delivery


@admin.register(DeliveryPerson)
class DeliveryPersonAdmin(admin.ModelAdmin):
    list_display  = ('user', 'cook', 'phone', 'is_active')
    search_fields = ('user__name', 'cook__kitchen_name')
    list_filter   = ('is_active',)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'delivery_person', 'status', 'sequence', 'cash_collected', 'delivered_at')
    list_filter  = ('status',)