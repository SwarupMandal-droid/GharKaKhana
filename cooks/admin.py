from django.contrib import admin
from .models import CookProfile, Dish, DeliverySlot, DailyMenu, MenuItem


@admin.register(CookProfile)
class CookProfileAdmin(admin.ModelAdmin):
    list_display  = ('kitchen_name', 'user', 'is_approved', 'is_active', 'daily_capacity', 'created_at')
    list_filter   = ('is_approved', 'is_active')
    search_fields = ('kitchen_name', 'user__email')
    actions       = ['approve_cooks']

    def approve_cooks(self, request, queryset):
        queryset.update(is_approved=True)
    approve_cooks.short_description = 'Approve selected cooks'


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display  = ('name', 'cook', 'food_type', 'spice_level', 'base_price', 'is_active')
    list_filter   = ('food_type', 'spice_level', 'is_active')
    search_fields = ('name', 'cook__kitchen_name')


@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    list_display = ('cook', 'label', 'start_time', 'end_time', 'is_active')
    list_filter  = ('is_active',)


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display  = ('cook', 'menu_date', 'meal_type', 'status', 'order_cutoff')
    list_filter   = ('meal_type', 'status')
    search_fields = ('cook__kitchen_name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('dish', 'menu', 'price_override', 'quantity_available')