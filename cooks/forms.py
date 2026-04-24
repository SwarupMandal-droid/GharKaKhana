from django import forms
from .models import CookProfile, Dish, DailyMenu, MenuItem, DeliverySlot

class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['name', 'description', 'base_price', 'food_type', 'spice_level', 'allergens', 'photo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class DailyMenuForm(forms.ModelForm):
    class Meta:
        model = DailyMenu
        fields = ['menu_date', 'meal_type', 'slot', 'order_cutoff', 'status']
        widgets = {
            'menu_date': forms.DateInput(attrs={'type': 'date'}),
            'order_cutoff': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.cook = kwargs.pop('cook', None)
        super().__init__(*args, **kwargs)
        if self.cook:
            self.fields['slot'].queryset = DeliverySlot.objects.filter(cook=self.cook, is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        menu_date = cleaned_data.get('menu_date')
        meal_type = cleaned_data.get('meal_type')

        if self.cook and menu_date and meal_type:
            # Check for existing menu with same date and meal type for this cook
            overlap = DailyMenu.objects.filter(
                cook=self.cook,
                menu_date=menu_date,
                meal_type=meal_type
            )
            
            # If editing, exclude current instance
            if self.instance and self.instance.pk:
                overlap = overlap.exclude(pk=self.instance.pk)
            
            if overlap.exists():
                raise forms.ValidationError(
                    f"You already have a {dict(DailyMenu.MealType.choices)[meal_type]} menu scheduled for {menu_date}."
                )
        
        return cleaned_data

class CookProfileForm(forms.ModelForm):
    class Meta:
        model = CookProfile
        fields = [
            'kitchen_name', 'bio', 'phone', 'address', 'latitude', 'longitude', 
            'cuisine_tags', 'daily_capacity', 'order_cutoff', 'same_day_enabled'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'order_cutoff': forms.TimeInput(attrs={'type': 'time'}),
        }

class DeliverySlotForm(forms.ModelForm):
    class Meta:
        model = DeliverySlot
        fields = ['label', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
