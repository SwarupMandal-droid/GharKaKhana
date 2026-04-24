from django.db import models
from accounts.models import User
import math


class CookProfile(models.Model):
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cook_profile')
    kitchen_name    = models.CharField(max_length=150)
    bio             = models.TextField(blank=True)
    photo           = models.ImageField(upload_to='cook_photos/', blank=True, null=True)
    phone           = models.CharField(max_length=15)
    address         = models.TextField()
    latitude        = models.DecimalField(max_digits=9, decimal_places=6)
    longitude       = models.DecimalField(max_digits=9, decimal_places=6)
    cuisine_tags    = models.CharField(max_length=255, blank=True, help_text='e.g. Bengali, North Indian, Chinese')
    daily_capacity  = models.PositiveIntegerField(default=20)
    order_cutoff    = models.TimeField(help_text='Time after which no more orders accepted')
    same_day_enabled= models.BooleanField(default=False)
    same_day_limit  = models.PositiveIntegerField(default=5)
    is_approved     = models.BooleanField(default=False)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cook_profiles'

    def __str__(self):
        return self.kitchen_name

    def get_same_day_max(self):
        return math.floor(self.daily_capacity * 0.35)

    def distance_from(self, lat, lng):
        """Haversine formula — returns distance in km"""
        R = 6371
        lat1 = math.radians(float(self.latitude))
        lon1 = math.radians(float(self.longitude))
        lat2 = math.radians(float(lat))
        lon2 = math.radians(float(lng))
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return round(R * c, 2)

    def delivery_charge(self, lat, lng):
        """Returns delivery charge based on distance tier"""
        dist = self.distance_from(lat, lng)
        if dist <= 2:
            return 15
        elif dist <= 5:
            return 30
        else:
            return 50

    def is_within_pickup_range(self, lat, lng):
        return self.distance_from(lat, lng) <= 1.0


class Dish(models.Model):

    class FoodType(models.TextChoices):
        VEG    = 'VEG',    'Vegetarian'
        NONVEG = 'NONVEG', 'Non-Vegetarian'
        EGG    = 'EGG',    'Egg'

    class SpiceLevel(models.TextChoices):
        MILD   = 'MILD',   'Mild'
        MEDIUM = 'MEDIUM', 'Medium'
        SPICY  = 'SPICY',  'Spicy'

    cook        = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name='dishes')
    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    base_price  = models.DecimalField(max_digits=8, decimal_places=2)
    food_type   = models.CharField(max_length=10, choices=FoodType.choices, default=FoodType.VEG)
    spice_level = models.CharField(max_length=10, choices=SpiceLevel.choices, default=SpiceLevel.MEDIUM)
    allergens   = models.CharField(max_length=255, blank=True, help_text='e.g. nuts, dairy, gluten')
    photo       = models.ImageField(upload_to='dish_photos/', blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dishes'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.cook.kitchen_name})'


class DeliverySlot(models.Model):
    cook       = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name='delivery_slots')
    label      = models.CharField(max_length=50, help_text='e.g. 7-8 PM')
    start_time = models.TimeField()
    end_time   = models.TimeField()
    is_active  = models.BooleanField(default=True)

    class Meta:
        db_table = 'delivery_slots'
        ordering = ['start_time']
        unique_together = ('cook', 'start_time', 'end_time')

    def __str__(self):
        return f'{self.cook.kitchen_name} — {self.label}'


class DailyMenu(models.Model):

    class MealType(models.TextChoices):
        LUNCH  = 'LUNCH',  'Lunch'
        DINNER = 'DINNER', 'Dinner'

    class Status(models.TextChoices):
        DRAFT     = 'DRAFT',     'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'

    cook        = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name='daily_menus')
    slot        = models.ForeignKey(DeliverySlot, on_delete=models.SET_NULL, null=True, related_name='menus')
    menu_date   = models.DateField()
    meal_type   = models.CharField(max_length=10, choices=MealType.choices)
    order_cutoff= models.TimeField()
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_menus'
        unique_together = ('cook', 'menu_date', 'meal_type')
        ordering = ['-menu_date', 'meal_type']

    def __str__(self):
        return f'{self.cook.kitchen_name} — {self.meal_type} — {self.menu_date}'

    def is_published(self):
        return self.status == self.Status.PUBLISHED


class MenuItem(models.Model):
    menu               = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='items')
    dish               = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='menu_items')
    price_override     = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                              help_text='Leave blank to use dish base price')
    quantity_available = models.PositiveIntegerField(default=0)

    class Meta:
        db_table   = 'menu_items'
        unique_together = ('menu', 'dish')

    def __str__(self):
        return f'{self.dish.name} in {self.menu}'

    def effective_price(self):
        return self.price_override if self.price_override else self.dish.base_price