from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Order, OrderItem, SavedAddress
from cooks.models import CookProfile, DailyMenu, MenuItem, DeliverySlot
import datetime
import json
import random
from decimal import Decimal


@login_required
def order_list(request):
    orders = Order.objects.filter(
        customer=request.user
    ).select_related('cook', 'slot').order_by('-placed_at')
    return render(request, 'customer/order_list.html', {'orders': orders})


@login_required
def cart(request):
    addresses = SavedAddress.objects.filter(customer=request.user)
    return render(request, 'customer/cart.html', {'addresses': addresses})


@login_required
def place_order(request):
    if request.method != 'POST':
        return redirect('orders:cart')

    # Read form data
    cook_id        = request.POST.get('cook_id')
    menu_id        = request.POST.get('menu_id')
    slot_id        = request.POST.get('slot_id')
    address_id     = request.POST.get('address_id')
    delivery_type  = request.POST.get('delivery_type', 'DELIVERY')
    payment_method = request.POST.get('payment_method', 'ONLINE')
    items_json     = request.POST.get('items_json', '{}')

    try:
        items_data = json.loads(items_json)
    except Exception:
        messages.error(request, 'Invalid cart data. Please try again.')
        return redirect('orders:cart')

    if not items_data:
        messages.error(request, 'Your cart is empty.')
        return redirect('orders:cart')

    # Get objects
    cook    = get_object_or_404(CookProfile, pk=cook_id, is_approved=True, is_active=True)
    menu    = get_object_or_404(DailyMenu, pk=menu_id, cook=cook, status='PUBLISHED')
    slot    = get_object_or_404(DeliverySlot, pk=slot_id, cook=cook)
    address = None
    if delivery_type == 'DELIVERY':
        address = get_object_or_404(SavedAddress, pk=address_id, customer=request.user)

    # Determine order type
    today    = timezone.localdate()
    tomorrow = today + datetime.timedelta(days=1)
    if menu.menu_date == tomorrow:
        order_type = 'PREORDER'
    elif menu.menu_date == today:
        order_type = 'SAMEDAY'
    else:
        messages.error(request, 'This menu is no longer available.')
        return redirect('customer:cook_list')

    # Check cutoff time
    now = timezone.localtime(timezone.now()).time()
    if order_type == 'PREORDER' and now > cook.order_cutoff:
        messages.error(request, f'Orders closed at {cook.order_cutoff}. Try again tomorrow.')
        return redirect(f'/cooks/{cook.pk}/')

    # Check same-day buffer (2 hours before slot)
    if order_type == 'SAMEDAY':
        if not cook.same_day_enabled:
            messages.error(request, 'Same-day orders are not available.')
            return redirect(f'/cooks/{cook.pk}/')
        buffer_time = (
            datetime.datetime.combine(today, slot.start_time)
            - datetime.timedelta(hours=2)
        ).time()
        if now > buffer_time:
            messages.error(request, 'Too late to place a same-day order for this slot.')
            return redirect(f'/cooks/{cook.pk}/')

    # Check capacity
    existing_orders = Order.objects.filter(
        cook=cook,
        menu__menu_date=menu.menu_date,
        status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'PENDING']
    ).count()

    if existing_orders >= cook.daily_capacity:
        messages.error(request, 'Sorry, this cook is fully booked for the day.')
        return redirect(f'/cooks/{cook.pk}/')

    # Check same-day capacity
    if order_type == 'SAMEDAY':
        sameday_orders = Order.objects.filter(
            cook=cook,
            menu__menu_date=today,
            order_type='SAMEDAY',
            status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'PENDING']
        ).count()
        if sameday_orders >= cook.get_same_day_max():
            messages.error(request, 'Same-day slots are full. Please pre-order for tomorrow.')
            return redirect(f'/cooks/{cook.pk}/')

    # Calculate delivery charge
    delivery_charge = 0
    if delivery_type == 'DELIVERY' and address:
        delivery_charge = cook.delivery_charge(address.latitude, address.longitude)

    # Build order items and calculate subtotal
    subtotal = Decimal('0.00')
    order_items = []
    
    for item_id, item_data in items_data.items():
        try:
            menu_item = MenuItem.objects.select_related('dish').get(pk=item_id, menu=menu)
            qty       = int(item_data.get('qty', 1))
            if qty <= 0: continue
            
            if qty > menu_item.quantity_available:
                messages.error(request, f"Sorry, only {menu_item.quantity_available} left for {menu_item.dish.name}.")
                return redirect('orders:cart')
            
            price     = Decimal(str(menu_item.effective_price()))
            subtotal += price * qty
            
            order_items.append({
                'menu_item':  menu_item,
                'quantity':   qty,
                'unit_price': price,
                'dish_name':  menu_item.dish.name,
            })
        except MenuItem.DoesNotExist:
            continue

    if not order_items:
        messages.error(request, 'No valid items found in your cart for this menu.')
        return redirect('orders:cart')

    # NEW: Validate pickup range (Business Rule: < 1km)
    if delivery_type == 'PICKUP':
        default_address = SavedAddress.objects.filter(customer=request.user, is_default=True).first()
        if not default_address:
            messages.error(request, "Default address required to verify pickup range.")
            return redirect('orders:cart')
        
        if not cook.is_within_pickup_range(default_address.latitude, default_address.longitude):
            messages.error(request, "You are beyond the 1km range for self-pickup.")
            return redirect('orders:cart')

    platform_fee = (subtotal * Decimal('0.002')).quantize(Decimal('0.01'))
    delivery_calc = Decimal(str(delivery_charge))
    total = subtotal + platform_fee + delivery_calc

    # Create order
    order = Order.objects.create(
        customer        = request.user,
        cook            = cook,
        menu            = menu,
        slot            = slot,
        address         = address,
        order_type      = order_type,
        delivery_type   = delivery_type,
        payment_method  = payment_method,
        payment_status  = 'PENDING',
        subtotal        = subtotal,
        platform_fee    = platform_fee,
        delivery_charge = delivery_charge,
        total           = total,
        status          = 'CONFIRMED' if order_type == 'PREORDER' else 'PENDING',
    )

    # Generate PIN for online orders
    if payment_method == 'ONLINE':
        order.pin_code = str(random.randint(1000, 9999))

    order.save()

    # Create order items
    for oi in order_items:
        OrderItem.objects.create(
            order      = order,
            menu_item  = oi['menu_item'],
            quantity   = oi['quantity'],
            unit_price = oi['unit_price'],
            dish_name  = oi['dish_name'],
        )
        # Deduct inventory count
        menu_item = oi['menu_item']
        menu_item.quantity_available -= oi['quantity']
        menu_item.save()

    # Create notification
    from notifications.models import Notification
    if order_type == 'PREORDER':
        Notification.objects.create(
            user    = request.user,
            type    = 'ORDER_CONFIRMED',
            title   = 'Order confirmed!',
            message = f'Your order from {cook.kitchen_name} is confirmed for {slot.label}.',
        )
        Notification.objects.create(
            user    = cook.user,
            type    = 'ORDER_PLACED',
            title   = 'New order received',
            message = f'{request.user.name} placed an order for {slot.label}.',
        )
    else:
        Notification.objects.create(
            user    = request.user,
            type    = 'ORDER_PLACED',
            title   = 'Order placed!',
            message = f'Waiting for {cook.kitchen_name} to confirm your order.',
        )

    messages.success(request, 'Order placed successfully!')
    return redirect('orders:order_detail', pk=order.pk)


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('cook', 'slot', 'address')
                     .prefetch_related('items'),
        pk=pk,
        customer=request.user
    )
    return render(request, 'customer/order_detail.html', {'order': order})


@login_required
def submit_review(request, pk):
    from reviews.models import Review
    order = get_object_or_404(Order, pk=pk, customer=request.user, status='DELIVERED')

    if hasattr(order, 'review'):
        messages.error(request, 'You have already reviewed this order.')
        return redirect('orders:order_detail', pk=pk)

    if request.method == 'POST':
        rating  = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '').strip()
        rating  = max(1, min(5, rating))

        Review.objects.create(
            order    = order,
            customer = request.user,
            cook     = order.cook,
            rating   = rating,
            comment  = comment,
        )
        messages.success(request, 'Thank you for your review!')

    return redirect('orders:order_detail', pk=pk)
