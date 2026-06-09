from django.db import transaction
from django.db.models import Sum, F
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
from django.conf import settings
from .razorpay_utils import create_razorpay_order, verify_payment_signature

@login_required
def order_list(request):
    customer_orders = Order.objects.filter(
        customer=request.user,
        visible_to_customer=True
    ).select_related('cook', 'slot').order_by('-placed_at')
    
    return render(request, 'customer/order_list.html', {
        'customer_orders': customer_orders,
        'user_id_debug': request.user.id
    })


@login_required
def cart(request):
    addresses = SavedAddress.objects.filter(customer=request.user)
    return render(request, 'customer/cart.html', {
        'addresses': addresses,
        'platform_fee_rate': Order.platform_fee_rate_percent(),
    })


def _mark_refund_pending(order, note=''):
    if order.payment_method != Order.PaymentMethod.ONLINE:
        return False
    if order.payment_status not in [Order.PaymentStatus.PAID, Order.PaymentStatus.REFUND_PENDING]:
        return False
    order.payment_status = Order.PaymentStatus.REFUND_PENDING
    if not order.refund_requested_at:
        order.refund_requested_at = timezone.now()
    if note and not order.refund_ref:
        order.refund_ref = note[:100]
    return True


def _notify_order_placed(order):
    from notifications.models import Notification
    if order.order_type == 'PREORDER':
        Notification.objects.create(
            user    = order.customer,
            type    = 'ORDER_CONFIRMED',
            title   = 'Order confirmed!',
            message = f'Your order from {order.cook.kitchen_name} is confirmed for {order.slot.label}.',
        )
        Notification.objects.create(
            user    = order.cook.user,
            type    = 'ORDER_PLACED',
            title   = 'New order received',
            message = f'{order.customer.name} placed an order for {order.slot.label}.',
        )
    else:
        Notification.objects.create(
            user    = order.customer,
            type    = 'ORDER_PLACED',
            title   = 'Order placed!',
            message = f'Waiting for {order.cook.kitchen_name} to confirm your order.',
        )

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
    if address_id:
        address = get_object_or_404(SavedAddress, pk=address_id, customer=request.user)
    elif delivery_type in ['DELIVERY', 'PICKUP']:
        messages.error(request, 'Please select an address to continue.')
        return redirect('orders:cart')

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
    now_dt = timezone.localtime(timezone.now())
    if order_type == 'PREORDER' and now_dt.time() > cook.order_cutoff:
        messages.error(request, f'Orders closed at {cook.order_cutoff}. Try again tomorrow.')
        return redirect(f'/cooks/{cook.pk}/')

    # Check same-day buffer (2 hours before slot)
    if order_type == 'SAMEDAY':
        if not cook.same_day_enabled:
            messages.error(request, 'Same-day orders are not available.')
            return redirect(f'/cooks/{cook.pk}/')
        
        # Use timezone-aware datetime for comparison (handles slots near midnight)
        slot_dt = timezone.make_aware(datetime.datetime.combine(today, slot.start_time))
        if now_dt > slot_dt - datetime.timedelta(hours=2):
            messages.error(request, 'Too late to place a same-day order for this slot (2h buffer required).')
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

    total_qty = sum(item['quantity'] for item in order_items)

    with transaction.atomic():
        # Capacity checks
        # We sum the quantity of items in confirmed/pending/preparing orders
        existing_meals = OrderItem.objects.filter(
            order__cook=cook,
            order__menu__menu_date=menu.menu_date,
            order__status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'PENDING']
        ).aggregate(total=Sum('quantity'))['total'] or 0

        if existing_meals + total_qty > cook.daily_capacity:
            messages.error(request, f"Sorry, {cook.kitchen_name} has reached its daily capacity.")
            return redirect('orders:cart')

        if order_type == 'SAMEDAY':
            sameday_meals = OrderItem.objects.filter(
                order__cook=cook,
                order__menu__menu_date=today,
                order__status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'PENDING']
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            if sameday_meals + total_qty > cook.get_same_day_max():
                messages.error(request, "Same-day order limit reached for this kitchen.")
                return redirect('orders:cart')

        # NEW: Validate pickup range (Business Rule: < 1km)
        if delivery_type == 'PICKUP':
            if not address or not cook.is_within_pickup_range(address.latitude, address.longitude):
                messages.error(request, "Your selected address is beyond the 1km range for self-pickup.")
                return redirect('orders:cart')

        platform_fee = Order.calculate_platform_fee(subtotal)
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
            payment_status  = (
                Order.PaymentStatus.INITIATED
                if payment_method == Order.PaymentMethod.ONLINE
                else Order.PaymentStatus.PENDING
            ),
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

    if payment_method == 'ONLINE':
        return redirect('orders:payment_page', pk=order.pk)
    else:
        _notify_order_placed(order)
        messages.success(request, 'Order placed successfully!')
        return redirect('orders:order_detail', pk=order.pk)


@login_required
def payment_page(request, pk):
    order = get_object_or_404(
        Order,
        pk=pk,
        customer=request.user,
        payment_method='ONLINE',
        payment_status__in=[
            Order.PaymentStatus.INITIATED,
            Order.PaymentStatus.PENDING,
            Order.PaymentStatus.FAILED,
        ]
    )
    
    # Reuse existing Razorpay order ID if available to avoid duplicates
    if order.payment_ref and order.payment_ref.startswith('order_'):
        rz_order_id = order.payment_ref
    else:
        rz_order = create_razorpay_order(amount_inr=order.total, receipt_id=f'GK-{order.pk}')
        rz_order_id = rz_order['id']
        order.payment_ref = rz_order_id
        order.save(update_fields=['payment_ref'])
    
    context = {
        'order': order,
        'rz_order_id': rz_order_id,
        'rz_key_id': settings.RAZORPAY_KEY_ID,
        'amount_paise': int(order.total * 100),
        'amount_display': order.total,
        'customer_name': request.user.name,
        'customer_email': request.user.email,
        'customer_phone': request.user.phone,
    }
    return render(request, 'customer/payment.html', context)


@login_required
def payment_callback(request, pk):
    if request.method != 'POST':
        return redirect('orders:order_list')
        
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    
    is_valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    
    with transaction.atomic():
        # Security check: verify that the callback order ID matches our record
        if is_valid and razorpay_order_id == order.payment_ref:
            order.payment_status = 'PAID'
            order.payment_ref = razorpay_payment_id
            order.save(update_fields=['payment_status', 'payment_ref'])
            
            _notify_order_placed(order)
            
            messages.success(request, 'Payment successful! Order placed.')
            return redirect('orders:order_detail', pk=order.pk)
        else:
            order.payment_status = 'FAILED'
            # If payment fails, we also mark the order status as FAILED so cooks don't see it
            order.status = 'FAILED'
            order.save(update_fields=['payment_status', 'status'])
            
            # Restore inventory
            for item in order.items.all():
                menu_item = item.menu_item
                menu_item.quantity_available = F('quantity_available') + item.quantity
                menu_item.save(update_fields=['quantity_available'])
                
            messages.error(request, 'Payment verification failed or was cancelled.')
            return redirect('orders:order_detail', pk=order.pk)


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('cook', 'slot', 'address')
                     .prefetch_related('items'),
        pk=pk,
        customer=request.user
    )
    return render(request, 'customer/order_detail.html', {
        'order': order,
        'platform_fee_rate': Order.platform_fee_rate_percent(),
    })


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)

    if request.method != 'POST':
        return redirect('orders:order_detail', pk=pk)

    # Only allow cancellation within 30 minutes of placing
    time_since = timezone.now() - order.placed_at
    if time_since.total_seconds() > 1800:  # 30 minutes
        messages.error(request, 'Orders can only be cancelled within 30 minutes of placing.')
        return redirect('orders:order_detail', pk=pk)

    # Only allow if still PENDING or CONFIRMED
    if order.status not in ['PENDING', 'CONFIRMED']:
        messages.error(request, f'Cannot cancel an order that is already {order.get_status_display()}.')
        return redirect('orders:order_detail', pk=pk)

    # Restock quantities
    for item in order.items.all():
        item.menu_item.quantity_available += item.quantity
        item.menu_item.save()

    # Update order
    order.status = 'CANCELLED'
    if _mark_refund_pending(order, note='CUSTOMER_CANCELLED'):
        order.save(update_fields=['status', 'payment_status', 'refund_requested_at', 'refund_ref'])
    else:
        order.save(update_fields=['status'])

    # Notify cook
    from notifications.models import Notification
    Notification.objects.create(
        user    = order.cook.user,
        type    = 'ORDER_FAILED',
        title   = 'Order cancelled',
        message = (
            f'{order.customer.name} cancelled order #{order.pk} '
            f'({order.slot.label}). Quantities have been restocked.'
        ),
    )

    # Refund note for online payments
    if order.payment_method == 'ONLINE' and order.payment_status == Order.PaymentStatus.REFUND_PENDING:
        messages.success(
            request,
            'Order cancelled. Your refund has been marked for processing.'
        )
    else:
        messages.success(request, 'Order cancelled successfully.')

    return redirect('orders:order_list')


@login_required
def update_location(request):
    if request.method != 'POST':
        return redirect('customer:cook_list')
        
    try:
        data = json.loads(request.body)
        lat  = data.get('lat')
        lng  = data.get('lng')
        addr = data.get('address', 'Current Location')
        
        if not lat or not lng:
            return redirect('customer:cook_list')
            
        # Update or create default address
        address, created = SavedAddress.objects.get_or_create(
            customer=request.user,
            label='Current Location',
            defaults={
                'address': addr,
                'latitude': lat,
                'longitude': lng,
                'is_default': True
            }
        )
        
        if not created:
            address.address = addr
            address.latitude = lat
            address.longitude = lng
            address.is_default = True
            address.save()
            
        return redirect('customer:cook_list')
    except Exception:
        return redirect('customer:cook_list')


@login_required
def submit_review(request, pk):
    from reviews.models import Review
    from notifications.models import Notification
    order = get_object_or_404(Order, pk=pk, customer=request.user, status='DELIVERED')

    if hasattr(order, 'review'):
        messages.error(request, 'You have already reviewed this order.')
        return redirect('orders:order_detail', pk=pk)

    if request.method == 'POST':
        rating  = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '').strip()
        rating  = max(1, min(5, rating))
        Review.objects.create(
            order=order,
            customer=request.user,
            cook=order.cook,
            rating=rating,
            comment=comment,
        )
        Notification.objects.create(
            user=order.cook.user,
            type='REVIEW_RECEIVED',
            title='New customer review',
            message=(
                f'{request.user.name} left a {rating}-star review '
                f'for order #{order.pk}.'
            ),
        )

        messages.success(request, 'Thank you for your review!')
    return redirect('orders:order_detail', pk=pk)

@login_required
@transaction.atomic
def archive_order(request, pk):
    """
    Manually hide an order from the list (customer or cook side).
    This doesn't cancel the order, just hides it from view.
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Permission check
    if request.user == order.customer:
        role = 'customer'
    elif hasattr(request.user, 'cook_profile') and request.user.cook_profile == order.cook:
        role = 'cook'
    else:
        return json_response({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        action = request.POST.get('action', 'delete') # delete or undo
        
        if role == 'customer':
            order.visible_to_customer = (action == 'undo')
        else:
            order.visible_to_cook = (action == 'undo')
            
        order.save()
        return json_response({'status': 'success', 'action': action})
        
    return json_response({'error': 'Method not allowed'}, status=405)

# Helper for JSON responses
def json_response(data, status=200):
    from django.http import JsonResponse
    return JsonResponse(data, status=status)
