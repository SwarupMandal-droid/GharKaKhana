from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CookProfile, Dish, DailyMenu, MenuItem, DeliverySlot
from .forms import DishForm, DailyMenuForm, CookProfileForm, DeliverySlotForm
from orders.models import Order
from accounts.decorators import role_required


@login_required
def kitchen_setup(request):
    """Guided first-time setup for new cooks"""
    if request.user.role != 'COOK':
        return redirect('/')

    # If already has a profile, go to dashboard
    try:
        cook = request.user.cook_profile
        if cook.kitchen_name:
            return redirect('cook:dashboard')
    except CookProfile.DoesNotExist:
        cook = None

    if request.method == 'POST':
        step = request.POST.get('step')

        if step == '1':
            # Kitchen basics
            kitchen_name = request.POST.get('kitchen_name','').strip()
            bio          = request.POST.get('bio','').strip()
            phone        = request.POST.get('phone','').strip()
            cuisine_tags = request.POST.get('cuisine_tags','').strip()
            address      = request.POST.get('address','').strip()
            latitude     = request.POST.get('latitude','').strip()
            longitude    = request.POST.get('longitude','').strip()

            if not all([kitchen_name, phone, address, latitude, longitude]):
                messages.error(request, 'Please fill all required fields and pin your location.')
                return render(request, 'cook/setup.html', {'step': 1})

            cook, created = CookProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'kitchen_name': kitchen_name,
                    'bio':          bio,
                    'phone':        phone,
                    'cuisine_tags': cuisine_tags,
                    'address':      address,
                    'latitude':     latitude,
                    'longitude':    longitude,
                    'daily_capacity': 20,
                    'order_cutoff': '22:00:00',
                    'same_day_enabled': False,
                    'same_day_limit': 5,
                    'is_approved': False,
                    'is_active':   True,
                }
            )
            if not created:
                cook.kitchen_name = kitchen_name
                cook.bio          = bio
                cook.phone        = phone
                cook.cuisine_tags = cuisine_tags
                cook.address      = address
                cook.latitude     = latitude
                cook.longitude    = longitude
                cook.save()

            return render(request, 'cook/setup.html', {
                'step': 2, 'cook': cook
            })

        elif step == '2':
            # Capacity and cutoff
            cook = request.user.cook_profile
            cook.daily_capacity = int(request.POST.get('daily_capacity', 20))
            cook.order_cutoff   = request.POST.get('order_cutoff', '22:00:00')
            if request.FILES.get('photo'):
                cook.photo = request.FILES['photo']
            cook.save()

            # Create default delivery slots
            slots = request.POST.getlist('slot_label')
            starts = request.POST.getlist('slot_start')
            ends   = request.POST.getlist('slot_end')
            for label, start, end in zip(slots, starts, ends):
                if label and start and end:
                    DeliverySlot.objects.get_or_create(
                        cook=cook, start_time=start, end_time=end,
                        defaults={'label': label, 'is_active': True}
                    )

            return render(request, 'cook/setup.html', {
                'step': 3, 'cook': cook
            })

        elif step == '3':
            # Done — go to pending approval page
            messages.success(
                request,
                'Your kitchen profile is submitted! '
                'We will review and approve it within 24 hours.'
            )
            return render(request, 'cook/setup.html', {
                'step': 'done'
            })

    return render(request, 'cook/setup.html', {'step': 1})


@role_required(['COOK'])
def dashboard(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    # Stats
    total_dishes = Dish.objects.filter(cook=cook).count()
    active_menus = DailyMenu.objects.filter(cook=cook, status='PUBLISHED').count()
    pending_orders = Order.objects.filter(cook=cook, status='PENDING').count()
    confirmed_orders = Order.objects.filter(cook=cook, status='CONFIRMED').count()
    
    # Revenue (Delivered only)
    from django.db.models import Sum
    total_revenue = Order.objects.filter(cook=cook, status='DELIVERED').aggregate(s=Sum('total'))['s'] or 0
    recent_orders = Order.objects.filter(cook=cook, visible_to_cook=True).order_by('-placed_at')[:5]

    # Earnings last 7 days (Actual vs Projected)
    import json as json_module
    import datetime
    from django.utils import timezone

    today = timezone.localdate()
    earnings_7days = []
    projected_7days = []
    labels_7days   = []
    
    seven_days_ago = today - datetime.timedelta(days=7)
    revenue_7days = Order.objects.filter(
        cook=cook, 
        status='DELIVERED', 
        placed_at__date__gte=seven_days_ago
    ).aggregate(t=Sum('subtotal'))['t'] or 0

    # More KPIs
    total_delivered = Order.objects.filter(cook=cook, status='DELIVERED').count()
    total_cancelled = Order.objects.filter(cook=cook, status='CANCELLED').count()
    completion_rate = 0
    if (total_delivered + total_cancelled) > 0:
        completion_rate = round((total_delivered / (total_delivered + total_cancelled)) * 100)
    
    avg_order_val = 0
    if total_delivered > 0:
        avg_order_val = total_revenue / total_delivered

    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        
        # Actual (Delivered)
        amt = Order.objects.filter(
            cook=cook,
            status='DELIVERED',
            placed_at__date=day,
        ).aggregate(t=Sum('subtotal'))['t'] or 0
        earnings_7days.append(float(amt))
        
        # Projected (Confirmed/Preparing)
        proj = Order.objects.filter(
            cook=cook,
            status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY'],
            placed_at__date=day,
        ).aggregate(t=Sum('subtotal'))['t'] or 0
        projected_7days.append(float(proj))
        
        labels_7days.append(day.strftime('%d %b'))
    
    context = {
        'cook': cook,
        'total_dishes': total_dishes,
        'active_menus': active_menus,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'total_revenue': total_revenue, # All time
        'revenue_7days': revenue_7days, # This week
        'completion_rate': completion_rate,
        'avg_order_val': avg_order_val,
        'recent_orders': recent_orders,
        'earnings_7days': json_module.dumps(earnings_7days),
        'projected_7days': json_module.dumps(projected_7days),
        'labels_7days':   json_module.dumps(labels_7days),
    }
    return render(request, 'cook/dashboard.html', context)

@role_required(['COOK'])
def dish_list(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    dishes = Dish.objects.filter(cook=cook).order_by('-created_at')
    
    context = {
        'cook': cook,
        'dishes': dishes,
    }
    return render(request, 'cook/dish_list.html', context)

@role_required(['COOK'])
def dish_add(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            dish = form.save(commit=False)
            dish.cook = cook
            dish.save()
            messages.success(request, 'Dish added successfully.')
            return redirect('cook:dish_list')
    else:
        form = DishForm()
    return render(request, 'cook/dish_form.html', {'form': form, 'cook': cook})

@role_required(['COOK'])
def dish_edit(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    dish = get_object_or_404(Dish, pk=pk, cook=cook)
    
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dish updated successfully.')
            return redirect('cook:dish_list')
    else:
        form = DishForm(instance=dish)
    
    return render(request, 'cook/dish_form.html', {
        'form': form, 
        'cook': cook,
        'dish': dish,
        'is_edit': True
    })

@role_required(['COOK'])
def menu_list(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    menus = DailyMenu.objects.filter(cook=cook).order_by('-menu_date', 'meal_type')
    
    context = {
        'cook': cook,
        'menus': menus,
    }
    return render(request, 'cook/menu_list.html', context)

@role_required(['COOK'])
def menu_create(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    if request.method == 'POST':
        form = DailyMenuForm(request.POST, cook=cook)
        if form.is_valid():
            # Cook is already on the form via __init__ and used for validation
            menu = form.save(commit=False)
            menu.cook = cook
            menu.save()
            messages.success(request, 'Menu created as Draft. Now add items.')
            return redirect('cook:menu_list')
    else:
        form = DailyMenuForm(cook=cook)
    return render(request, 'cook/menu_form.html', {'form': form, 'cook': cook})

@role_required(['COOK'])
def menu_edit(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    menu = get_object_or_404(DailyMenu, pk=pk, cook=cook)
    
    if request.method == 'POST':
        form = DailyMenuForm(request.POST, instance=menu, cook=cook)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu details updated.')
            return redirect('cook:menu_list')
    else:
        form = DailyMenuForm(instance=menu, cook=cook)
    
    # Manage items
    menu_items = menu.items.all().select_related('dish')
    available_dishes = Dish.objects.filter(cook=cook, is_active=True).exclude(
        id__in=menu_items.values_list('dish_id', flat=True)
    )
    
    context = {
        'cook': cook,
        'menu': menu,
        'form': form,
        'menu_items': menu_items,
        'available_dishes': available_dishes,
    }
    return render(request, 'cook/menu_form.html', context)

@role_required(['COOK'])
def menu_item_add(request, menu_id):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    menu = get_object_or_404(DailyMenu, pk=menu_id, cook=cook)
    
    if request.method == 'POST':
        dish_id = request.POST.get('dish_id')
        qty     = request.POST.get('quantity', 0)
        price   = request.POST.get('price_override')
        
        dish = get_object_or_404(Dish, pk=dish_id, cook=cook)
        
        # Check if dish already exists in menu
        item, created = MenuItem.objects.get_or_create(
            menu=menu,
            dish=dish,
            defaults={
                'quantity_available': qty,
                'price_override': price if price else None
            }
        )
        
        if created:
            messages.success(request, f'{dish.name} added to menu.')
        else:
            # Optionally update quantity if already exists
            item.quantity_available = qty
            if price:
                item.price_override = price
            item.save()
            messages.info(request, f'Updated {dish.name} in menu (was already present).')
    
    return redirect('cook:menu_edit', pk=menu.pk)

@role_required(['COOK'])
def menu_item_remove(request, item_id):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    item = get_object_or_404(MenuItem, pk=item_id, menu__cook=cook)
    menu_id = item.menu_id
    item.delete()
    messages.success(request, 'Item removed from menu.')
    return redirect('cook:menu_edit', pk=menu_id)

@role_required(['COOK'])
def order_list(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    orders = Order.objects.filter(cook=cook, visible_to_cook=True).order_by('-placed_at')
    
    context = {
        'cook': cook,
        'orders': orders,
    }
    return render(request, 'cook/order_list.html', context)


@role_required(['COOK'])
def order_detail(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    order = get_object_or_404(
        Order.objects.select_related('customer', 'slot', 'address')
                     .prefetch_related('items'), 
        pk=pk, 
        cook=cook
    )
    
    context = {
        'cook': cook,
        'order': order,
        'status_choices': Order.Status.choices,
    }
    return render(request, 'cook/order_detail.html', context)


@role_required(['COOK'])
def order_status_update(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    order = get_object_or_404(Order, pk=pk, cook=cook)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.Status.choices):
            old_status = order.status
            order.status = new_status
            update_fields = ['status']
            if (
                order.payment_method == Order.PaymentMethod.ONLINE
                and order.payment_status == Order.PaymentStatus.PAID
                and new_status in ['CANCELLED', 'FAILED']
            ):
                order.payment_status = Order.PaymentStatus.REFUND_PENDING
                order.refund_requested_at = timezone.now()
                order.refund_ref = f'COOK_{new_status}'
                update_fields.extend(['payment_status', 'refund_requested_at', 'refund_ref'])
            order.save(update_fields=update_fields)
            
            # Restock inventory on failure/cancellation
            if old_status not in ['CANCELLED', 'FAILED'] and new_status in ['CANCELLED', 'FAILED']:
                for item in order.items.all():
                    item.menu_item.quantity_available += item.quantity
                    item.menu_item.save()

            # Notify customer about status change
            _notify_status_change(order, old_status, new_status)
                    
            messages.success(request, f'Order status updated to {order.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status.')
            
    return redirect('cook:order_detail', pk=pk)


def _notify_status_change(order, old_status, new_status):
    """Send a notification to the customer when the cook changes order status."""
    from notifications.models import Notification

    STATUS_NOTIFICATIONS = {
        'CONFIRMED': {
            'type':    'ORDER_CONFIRMED',
            'title':   'Order confirmed!',
            'message': 'Your order from {kitchen} has been confirmed and is scheduled for {slot}.',
        },
        'PREPARING': {
            'type':    'ORDER_PREPARING',
            'title':   'Food is being prepared 🍳',
            'message': '{kitchen} has started preparing your order. It will be ready soon!',
        },
        'OUT_FOR_DELIVERY': {
            'type':    'ORDER_OUT',
            'title':   'Out for delivery! 🛵',
            'message': 'Your order from {kitchen} is on its way. Keep your PIN ready.',
        },
        'CANCELLED': {
            'type':    'ORDER_CANCELLED',
            'title':   'Order cancelled',
            'message': 'Your order from {kitchen} has been cancelled by the cook. '
                       'If you were charged, a refund will be processed.',
        },
        'FAILED': {
            'type':    'ORDER_FAILED',
            'title':   'Order could not be fulfilled',
            'message': 'Unfortunately {kitchen} could not fulfil your order. '
                       'Please contact support if you need assistance.',
        },
    }

    if old_status == new_status:
        return

    notif_data = STATUS_NOTIFICATIONS.get(new_status)
    if not notif_data:
        return

    slot_label = order.slot.label if order.slot else 'your selected slot'
    Notification.objects.create(
        user    = order.customer,
        type    = notif_data['type'],
        title   = notif_data['title'],
        message = notif_data['message'].format(
            kitchen=order.cook.kitchen_name,
            slot=slot_label,
        ),
    )


@role_required(['COOK'])
def onboarding(request):
    # Check if already has profile
    if CookProfile.objects.filter(user=request.user).exists():
        return redirect('cook:dashboard')
        
    if request.method == 'POST':
        form = CookProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile completed! Welcome to GharKhana.')
            return redirect('cook:dashboard')
    else:
        form = CookProfileForm(initial={'phone': request.user.phone})
        
    return render(request, 'cook/onboarding.html', {'form': form})

@role_required(['COOK'])
def slot_list(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
        
    slots = DeliverySlot.objects.filter(cook=cook)
    form = DeliverySlotForm()
    return render(request, 'cook/slots.html', {'cook': cook, 'slots': slots, 'form': form})

@role_required(['COOK'])
def slot_add(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
        
    if request.method == 'POST':
        form = DeliverySlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.cook = cook
            slot.save()
            messages.success(request, 'Delivery slot added.')
    return redirect('cook:slot_list')

@role_required(['COOK'])
def slot_delete(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
        
    slot = get_object_or_404(DeliverySlot, pk=pk, cook=cook)
    slot.delete()
    messages.success(request, 'Slot deleted.')
    return redirect('cook:slot_list')

@role_required(['COOK'])
def settings_view(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
        
    if request.method == 'POST':
        form = CookProfileForm(request.POST, request.FILES, instance=cook)
        if form.is_valid():
            if request.POST.get('clear_photo') == 'true':
                cook.photo = None
            form.save()
            messages.success(request, 'Settings updated.')
            return redirect('cook:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CookProfileForm(instance=cook)
        
    context = {
        'cook': cook,
        'form': form,
    }
    return render(request, 'cook/settings.html', context)
