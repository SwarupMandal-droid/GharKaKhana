from django.contrib import admin
from .models import SavedAddress, Order, OrderItem, FailedDelivery


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display  = ('customer', 'label', 'address', 'is_default')
    search_fields = ('customer__name', 'address')


class OrderItemInline(admin.TabularInline):
    model  = OrderItem
    extra  = 0
    fields = ('dish_name', 'quantity', 'unit_price')
    readonly_fields = ('dish_name', 'unit_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display   = ('id', 'customer', 'cook', 'order_type', 'status',
                      'payment_method', 'payment_status', 'total', 'placed_at')
    list_filter    = ('status', 'order_type', 'payment_method', 'payment_status')
    search_fields  = ('customer__name', 'cook__kitchen_name')
    readonly_fields= ('pin_code', 'placed_at', 'platform_fee', 'total')
    inlines        = [OrderItemInline]


@admin.register(FailedDelivery)
class FailedDeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'reason', 'reported_at')
    list_filter  = ('reason',)