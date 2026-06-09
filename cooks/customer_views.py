import datetime
import datetime
import json

from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, OuterRef, Exists
from .models import CookProfile, DailyMenu
from orders.models import SavedAddress, Order


def _build_repeat_order_payload(source_order, today_menus, tomorrow_menus):
    menu_candidates = list(today_menus) + list(tomorrow_menus)
    if not menu_candidates:
        return None

    best_payload = None
    best_match_count = 0

    for menu in menu_candidates:
        available_by_dish = {
            item.dish_id: item
            for item in menu.items.all()
            if item.quantity_available > 0
        }
        matched_items = {}
        missing_items = []

        for order_item in source_order.items.all():
            dish_id = order_item.menu_item.dish_id
            menu_item = available_by_dish.get(dish_id)
            if not menu_item:
                missing_items.append(order_item.dish_name)
                continue

            qty = min(order_item.quantity, menu_item.quantity_available)
            if qty <= 0:
                missing_items.append(order_item.dish_name)
                continue

            matched_items[str(menu_item.pk)] = {
                'name': menu_item.dish.name,
                'price': float(menu_item.effective_price()),
                'qty': qty,
                'menuId': menu.pk,
                'slot': menu.slot.label if menu.slot else '',
                'slotId': menu.slot.pk if menu.slot else None,
            }

        if len(matched_items) > best_match_count:
            best_match_count = len(matched_items)
            best_payload = {
                'menu_id': menu.pk,
                'slot_id': menu.slot.pk if menu.slot else None,
                'items': matched_items,
                'missing_items': missing_items,
            }

    return best_payload if best_match_count > 0 else None


@login_required
def cook_list(request):
    default_address = SavedAddress.objects.filter(
        customer=request.user, is_default=True
    ).first()

    cooks = CookProfile.objects.filter(
        is_approved=True, is_active=True
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )

    # Filters from GET params
    food_type   = request.GET.get('food_type', '')
    meal_type   = request.GET.get('meal_type', '')
    search      = request.GET.get('search', '').strip()
    sort_by     = request.GET.get('sort', 'distance')
    max_dist    = request.GET.get('max_dist', '')

    # Search by kitchen name or cuisine
    if search:
        cooks = cooks.filter(
            kitchen_name__icontains=search
        ) | CookProfile.objects.filter(
            is_approved=True, is_active=True,
            cuisine_tags__icontains=search
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )
        cooks = cooks.distinct()

    # Filter by food type
    if food_type:
        cooks = cooks.filter(
            dishes__food_type=food_type,
            dishes__is_active=True
        ).distinct()

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    today    = datetime.date.today()

    # Filter by meal type
    if meal_type:
        cooks = cooks.filter(
            daily_menus__menu_date=tomorrow,
            daily_menus__meal_type=meal_type,
            daily_menus__status='PUBLISHED',
        ).distinct()

    # Optimize by checking menu existence in a single query (Rule: Performance)
    tomorrow_menu_exists = DailyMenu.objects.filter(
        cook=OuterRef('pk'), menu_date=tomorrow, status='PUBLISHED'
    )
    today_menu_exists = DailyMenu.objects.filter(
        cook=OuterRef('pk'), menu_date=today, status='PUBLISHED'
    )

    cooks = cooks.annotate(
        has_tomorrow_menu=Exists(tomorrow_menu_exists),
        has_today_menu=Exists(today_menu_exists)
    )

    cook_data = []
    for cook in cooks:
        if default_address:
            distance  = cook.distance_from(default_address.latitude, default_address.longitude)
            charge    = cook.delivery_charge(default_address.latitude, default_address.longitude)
            pickup_ok = cook.is_within_pickup_range(default_address.latitude, default_address.longitude)
        else:
            distance  = None
            charge    = None
            pickup_ok = False

        # Max distance filter
        if max_dist and distance is not None:
            try:
                if distance > float(max_dist):
                    continue
            except ValueError:
                pass

        has_menu = cook.has_tomorrow_menu
        same_day = cook.has_today_menu and cook.same_day_enabled

        cook_data.append({
            'cook':         cook,
            'distance':     distance,
            'charge':       charge,
            'pickup_ok':    pickup_ok,
            'has_menu':     has_menu,
            'same_day':     same_day,
            'avg_rating':   round(cook.avg_rating, 1) if cook.avg_rating else None,
            'review_count': cook.review_count,
        })

    # Sort
    if sort_by == 'rating':
        cook_data.sort(key=lambda x: x['avg_rating'] or 0, reverse=True)
    elif sort_by == 'distance' and default_address:
        cook_data.sort(key=lambda x: x['distance'] if x['distance'] else 999)

    context = {
        'cook_data':       cook_data,
        'default_address': default_address,
        'food_type':       food_type,
        'meal_type':       meal_type,
        'search':          search,
        'sort_by':         sort_by,
        'max_dist':        max_dist,
        'today':           today,
        'tomorrow':        tomorrow,
    }
    return render(request, 'customer/cook_list.html', context)


@login_required
def cook_detail(request, pk):
    cook = get_object_or_404(CookProfile, pk=pk, is_approved=True, is_active=True)

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

    repeat_order_payload = None
    repeat_order_id = request.GET.get('repeat_order')
    if repeat_order_id:
        try:
            source_order = Order.objects.prefetch_related('items__menu_item__dish').get(
                pk=repeat_order_id,
                customer=request.user,
                cook=cook,
                status=Order.Status.DELIVERED,
            )
            repeat_order_payload = _build_repeat_order_payload(
                source_order,
                today_menus,
                tomorrow_menus,
            )
            if repeat_order_payload:
                if repeat_order_payload['missing_items']:
                    messages.info(
                        request,
                        'We rebuilt the available dishes from your previous order. '
                        'Some items are not on the live menu right now.'
                    )
                else:
                    messages.success(request, 'Your previous order has been added to the cart.')
            else:
                messages.error(
                    request,
                    'We could not find a live menu that matches your previous order right now.'
                )
        except (ValueError, Order.DoesNotExist):
            messages.error(request, 'That order is not available for repeat ordering.')

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
        'platform_fee_rate': settings.PLATFORM_FEE_RATE,
        'repeat_order_payload_json': json.dumps(repeat_order_payload) if repeat_order_payload else '',
        'tomorrow':       tomorrow,
        'today':          today,
    }
    return render(request, 'customer/cook_detail.html', context)
