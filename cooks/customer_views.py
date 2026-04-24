from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from .models import CookProfile, DailyMenu
from orders.models import SavedAddress
import datetime


@login_required
def cook_list(request):
    # Get filters from GET params
    food_type = request.GET.get('food_type', '')
    meal_type = request.GET.get('meal_type', '')

    # Dates (defined early to prevent UnboundLocalError)
    today    = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    # Get customer's default address for distance calculation
    default_address = SavedAddress.objects.filter(
        customer=request.user, is_default=True
    ).first()

    # Get all approved active cooks
    cooks = CookProfile.objects.filter(
        is_approved=True, is_active=True
    ).annotate(
        avg_rating_val=Avg('reviews__rating'),
        review_count_val=Count('reviews')
    )

    # Build cook data with distance and delivery charge
    cook_data = []
    for cook in cooks:
        # Check menus based on filters
        # 1. Meal type filter (applies to tomorrow's menu or today's same-day)
        tomorrow_menu = DailyMenu.objects.filter(
            cook=cook, menu_date=tomorrow, status='PUBLISHED'
        )
        if meal_type:
            tomorrow_menu = tomorrow_menu.filter(meal_type=meal_type)

        today_menu = DailyMenu.objects.filter(
            cook=cook, menu_date=today, status='PUBLISHED'
        ) if cook.same_day_enabled else DailyMenu.objects.none()
        if meal_type:
            today_menu = today_menu.filter(meal_type=meal_type)

        has_tomorrow = tomorrow_menu.exists()
        has_today    = today_menu.exists()

        # If meal_type is specified, cook MUST have a menu for that type
        if meal_type and not (has_tomorrow or has_today):
            continue

        # 2. Food type filter (check dishes in active menus)
        if food_type:
            # Check if any dish in these menus matches food_type
            match_tomorrow = tomorrow_menu.filter(items__dish__food_type=food_type).exists()
            match_today    = today_menu.filter(items__dish__food_type=food_type).exists()
            if not (match_tomorrow or match_today):
                continue

        if default_address:
            distance = cook.distance_from(
                default_address.latitude,
                default_address.longitude
            )
            charge = cook.delivery_charge(
                default_address.latitude,
                default_address.longitude
            )
            pickup_ok = cook.is_within_pickup_range(
                default_address.latitude,
                default_address.longitude
            )
        else:
            distance = None
            charge   = None
            pickup_ok= False

        cook_data.append({
            'cook':         cook,
            'distance':     distance,
            'charge':       charge,
            'pickup_ok':    pickup_ok,
            'has_menu':     has_tomorrow,
            'same_day':     has_today,
            'avg_rating':   round(cook.avg_rating_val, 1) if cook.avg_rating_val else None,
            'review_count': cook.review_count_val,
        })

    # Sort by distance if we have location
    if default_address:
        cook_data.sort(key=lambda x: x['distance'] if x['distance'] else 999)

    context = {
        'cook_data':       cook_data,
        'default_address': default_address,
        'food_type':       food_type,
        'meal_type':       meal_type,
        'today':           today,
        'tomorrow':        tomorrow,
    }
    return render(request, 'customer/cook_list.html', context)


@login_required
def cook_detail(request, pk):
    cook = get_object_or_404(CookProfile, pk=pk, is_approved=True, is_active=True)

    import datetime
    today    = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    # Get published menus
    tomorrow_menus = DailyMenu.objects.filter(
        cook=cook, menu_date=tomorrow, status='PUBLISHED'
    ).prefetch_related('items__dish')

    today_menus = DailyMenu.objects.filter(
        cook=cook, menu_date=today, status='PUBLISHED'
    ).prefetch_related('items__dish') if cook.same_day_enabled else []

    # Delivery slots
    slots = cook.delivery_slots.filter(is_active=True)

    # Reviews
    reviews = cook.reviews.select_related('customer').order_by('-created_at')[:10]
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    # Customer distance
    from orders.models import SavedAddress
    default_address = SavedAddress.objects.filter(
        customer=request.user, is_default=True
    ).first()

    distance = None
    charge   = None
    pickup_ok= False
    if default_address:
        distance  = cook.distance_from(default_address.latitude, default_address.longitude)
        charge    = cook.delivery_charge(default_address.latitude, default_address.longitude)
        pickup_ok = cook.is_within_pickup_range(default_address.latitude, default_address.longitude)

    context = {
        'cook':           cook,
        'tomorrow_menus': tomorrow_menus,
        'today_menus':    today_menus,
        'slots':          slots,
        'reviews':        reviews,
        'avg_rating':     round(avg_rating, 1) if avg_rating else None,
        'distance':       distance,
        'charge':         charge,
        'pickup_ok':      pickup_ok,
        'tomorrow':       tomorrow,
        'today':          today,
    }
    return render(request, 'customer/cook_detail.html', context)