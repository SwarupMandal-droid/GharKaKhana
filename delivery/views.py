from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import DeliveryPerson, Delivery
from orders.models import Order
from cooks.models import CookProfile
import datetime
import math


def delivery_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'DELIVERY':
            messages.error(request, 'Access denied.')
            return redirect('/')
        try:
            request.user.delivery_profile
        except DeliveryPerson.DoesNotExist:
            messages.error(request, 'Delivery profile not found.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


def haversine(lat1, lon1, lat2, lon2):
    """Returns distance in km between two GPS points"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [
        float(lat1), float(lon1), float(lat2), float(lon2)
    ])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)


def nearest_neighbor_route(cook, deliveries):
    """
    Nearest Neighbor algorithm.
    Start from cook's kitchen, always go to nearest unvisited delivery.
    Returns ordered list of deliveries with per-leg distance.
    """
    if not deliveries:
        return []

    try:
        current_lat = float(cook.latitude)
        current_lng = float(cook.longitude)
    except (TypeError, ValueError):
        return []

    unvisited  = list(deliveries)
    route      = []

    while unvisited:
        nearest      = None
        nearest_dist = float('inf')

        for delivery in unvisited:
            if not delivery.order.address:
                continue
            dist = haversine(
                current_lat, current_lng,
                delivery.order.address.latitude,
                delivery.order.address.longitude,
            )
            if dist < nearest_dist:
                nearest_dist = dist
                nearest      = delivery

        if nearest is None:
            break

        route.append({
            'delivery':  nearest,
            'distance':  nearest_dist,
        })
        current_lat = float(nearest.order.address.latitude)
        current_lng = float(nearest.order.address.longitude)
        unvisited.remove(nearest)

    return route


def build_maps_url(cook, route):
    """Build Google Maps multi-stop URL"""
    if not route:
        return None
    waypoints = [f"{cook.latitude},{cook.longitude}"]
    for stop in route:
        addr = stop['delivery'].order.address
        if addr:
            waypoints.append(f"{addr.latitude},{addr.longitude}")
    if len(waypoints) < 2:
        return None
    return "https://www.google.com/maps/dir/" + "/".join(waypoints)


def estimate_time(route):
    """Estimate total delivery time in minutes"""
    avg_speed_kmh   = 20
    handoff_minutes = 5
    total_km = sum(stop['distance'] for stop in route)
    travel   = (total_km / avg_speed_kmh) * 60
    handoffs = len(route) * handoff_minutes
    return round(travel + handoffs)


@delivery_required
def dashboard(request):
    delivery_person = request.user.delivery_profile
    cook            = delivery_person.cook
    today           = datetime.date.today()

    # Get today's slot batches
    from cooks.models import DeliverySlot
    slots = cook.delivery_slots.filter(is_active=True).order_by('start_time')

    slot_batches = []
    for slot in slots:
        # All orders for this slot today that need delivery
        slot_orders = Order.objects.filter(
            cook         = cook,
            slot         = slot,
            menu__menu_date = today,
            status__in   = ['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED'],
            delivery_type = 'DELIVERY',
        ).select_related(
            'customer', 'address'
        ).prefetch_related('items')

        if not slot_orders.exists():
            continue

        # Get or create Delivery records for these orders
        deliveries = []
        for order in slot_orders:
            delivery, created = Delivery.objects.get_or_create(
                order           = order,
                defaults={
                    'delivery_person': delivery_person,
                    'delivery_address': order.address.address if order.address else '',
                    'status': 'ASSIGNED',
                }
            )
            if not delivery.delivery_person:
                delivery.delivery_person = delivery_person
                delivery.save()
            deliveries.append(delivery)

        # Run route optimization
        pending_deliveries = [
            d for d in deliveries if d.status == 'ASSIGNED'
        ]
        completed_deliveries = [
            d for d in deliveries if d.status == 'COMPLETED'
        ]

        # Check if cutoff has passed (route ready)
        now          = timezone.localtime(timezone.now()).time()
        cutoff_passed = now >= cook.order_cutoff

        if pending_deliveries:
            route    = nearest_neighbor_route(cook, pending_deliveries)
            # Save sequence numbers
            for idx, stop in enumerate(route):
                stop['delivery'].sequence = idx + 1
                stop['delivery'].save()
            maps_url = build_maps_url(cook, route)
            est_time = estimate_time(route)
            total_km = round(sum(s['distance'] for s in route), 2)
        else:
            route    = []
            maps_url = None
            est_time = 0
            total_km = 0

        slot_batches.append({
            'slot':       slot,
            'route':      route,
            'completed':  completed_deliveries,
            'maps_url':   maps_url,
            'est_time':   est_time,
            'total_km':   total_km,
            'cutoff_passed': cutoff_passed,
            'total':      len(deliveries),
            'done':       len(completed_deliveries),
        })

    context = {
        'delivery_person': delivery_person,
        'cook':            cook,
        'slot_batches':    slot_batches,
        'today':           today,
    }
    return render(request, 'delivery/dashboard.html', context)


@delivery_required
def confirm_delivery(request, order_id):
    delivery_person = request.user.delivery_profile
    order   = get_object_or_404(Order, pk=order_id, cook=delivery_person.cook)
    delivery= get_object_or_404(Delivery, order=order, delivery_person=delivery_person)

    if request.method != 'POST':
        return redirect('delivery:dashboard')

    # COD flow
    if order.payment_method == 'COD':
        delivery.cash_collected = True
        delivery.status         = 'COMPLETED'
        delivery.delivered_at   = timezone.now()
        delivery.save()
        order.status            = 'DELIVERED'
        order.payment_status    = 'PAID'
        order.save()
        _notify_delivered(order)
        messages.success(request, f'Cash collected. Order #{order.pk} marked delivered.')
        return redirect('delivery:dashboard')

    # Online PIN flow
    entered_pin = request.POST.get('pin', '').strip()
    if not entered_pin:
        p1 = request.POST.get('p1','')
        p2 = request.POST.get('p2','')
        p3 = request.POST.get('p3','')
        p4 = request.POST.get('p4','')
        entered_pin = p1 + p2 + p3 + p4

    if entered_pin == order.pin_code:
        delivery.status      = 'COMPLETED'
        delivery.delivered_at= timezone.now()
        delivery.save()
        order.status         = 'DELIVERED'
        order.save()
        _notify_delivered(order)
        messages.success(request, f'PIN confirmed. Order #{order.pk} delivered!')
    else:
        messages.error(request, 'Incorrect PIN. Please try again.')

    return redirect('delivery:dashboard')


@delivery_required
def report_failed(request, order_id):
    delivery_person = request.user.delivery_profile
    order    = get_object_or_404(Order, pk=order_id, cook=delivery_person.cook)
    delivery = get_object_or_404(Delivery, order=order, delivery_person=delivery_person)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'OTHER')
        photo  = request.FILES.get('photo')

        from orders.models import FailedDelivery
        FailedDelivery.objects.create(
            order  = order,
            reason = reason,
            photo  = photo,
            notes  = request.POST.get('notes', ''),
        )

        delivery.status = 'FAILED'
        delivery.save()
        order.status    = 'FAILED'
        order.save()

        # Notify customer if prepaid
        if order.payment_method == 'ONLINE' and photo:
            from notifications.models import Notification
            Notification.objects.create(
                user    = order.customer,
                type    = 'ORDER_FAILED',
                title   = 'Delivery could not be completed',
                message = (
                    f'We could not deliver your order from {order.cook.kitchen_name}. '
                    f'Reason: {reason}. Your food has been donated to someone in need. '
                    f'Please contact us for a refund.'
                ),
                photo   = photo,
            )

        messages.success(request, 'Delivery reported. Thank you for your honesty.')
        return redirect('delivery:dashboard')

    return render(request, 'delivery/failed.html', {
        'order':    order,
        'delivery': delivery,
    })


def _notify_delivered(order):
    from notifications.models import Notification
    Notification.objects.create(
        user    = order.customer,
        type    = 'ORDER_DELIVERED',
        title   = 'Order delivered!',
        message = f'Your order from {order.cook.kitchen_name} has been delivered. Enjoy your meal!',
    )
