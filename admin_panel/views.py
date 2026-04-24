from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from accounts.models import User
from cooks.models import CookProfile
from orders.models import Order
from billing.models import CommissionInvoice
from reviews.models import Review
import datetime
from django.utils import timezone


def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            messages.error(request, 'Access denied.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def dashboard(request):
    today      = timezone.localdate()
    this_month = today.replace(day=1)

    # Platform stats
    total_orders    = Order.objects.filter(status='DELIVERED').count()
    total_customers = User.objects.filter(role='CUSTOMER').count()
    total_cooks     = CookProfile.objects.filter(is_approved=True).count()
    pending_cooks   = CookProfile.objects.filter(is_approved=False).count()

    # Revenue
    total_platform_fee = Order.objects.filter(
        status='DELIVERED'
    ).aggregate(total=Sum('platform_fee'))['total'] or 0

    month_orders = Order.objects.filter(
        status='DELIVERED',
        placed_at__date__gte=this_month,
    )
    month_revenue = month_orders.aggregate(
        total=Sum('subtotal')
    )['total'] or 0
    month_fee = month_orders.aggregate(
        total=Sum('platform_fee')
    )['total'] or 0

    # Pending commission
    pending_commission = CommissionInvoice.objects.filter(
        status='UNPAID'
    ).aggregate(total=Sum('commission_amount'))['total'] or 0

    # Recent orders
    recent_orders = Order.objects.select_related(
        'customer', 'cook', 'slot'
    ).order_by('-placed_at')[:10]

    # Pending cook approvals
    pending_approvals = CookProfile.objects.filter(
        is_approved=False
    ).select_related('user').order_by('-created_at')[:5]

    # Unpaid invoices
    unpaid_invoices = CommissionInvoice.objects.filter(
        status='UNPAID'
    ).select_related('cook').order_by('due_date')[:5]

    context = {
        'total_orders':        total_orders,
        'total_customers':     total_customers,
        'total_cooks':         total_cooks,
        'pending_cooks':       pending_cooks,
        'total_platform_fee':  float(total_platform_fee),
        'month_revenue':       float(month_revenue),
        'month_fee':           float(month_fee),
        'pending_commission':  float(pending_commission),
        'recent_orders':       recent_orders,
        'pending_approvals':   pending_approvals,
        'unpaid_invoices':     unpaid_invoices,
        'today':               today,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def cook_approvals(request):
    status   = request.GET.get('status', 'pending')
    if status == 'pending':
        cooks = CookProfile.objects.filter(
            is_approved=False
        ).select_related('user').order_by('-created_at')
    else:
        cooks = CookProfile.objects.filter(
            is_approved=True
        ).select_related('user').order_by('-created_at')

    return render(request, 'admin_panel/cook_approvals.html', {
        'cooks':  cooks,
        'status': status,
    })


@admin_required
def approve_cook(request, pk):
    cook = get_object_or_404(CookProfile, pk=pk)
    if request.method == 'POST':
        cook.is_approved = True
        cook.is_active   = True
        cook.save()

        from notifications.models import Notification
        Notification.objects.create(
            user    = cook.user,
            type    = 'ORDER_CONFIRMED',
            title   = 'Your kitchen is approved!',
            message = (
                f'Congratulations! {cook.kitchen_name} has been approved. '
                f'You can now publish menus and start receiving orders.'
            ),
        )
        messages.success(request, f'{cook.kitchen_name} approved successfully.')
    return redirect('admin_panel:cook_approvals')


@admin_required
def reject_cook(request, pk):
    cook = get_object_or_404(CookProfile, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        from notifications.models import Notification
        Notification.objects.create(
            user    = cook.user,
            type    = 'ORDER_FAILED',
            title   = 'Application not approved',
            message = (
                f'Your application for {cook.kitchen_name} was not approved. '
                f'Reason: {reason}. Please contact support for more details.'
            ),
        )
        cook.delete()
        messages.success(request, 'Cook application rejected.')
    return redirect('admin_panel:cook_approvals')


@admin_required
def all_orders(request):
    status     = request.GET.get('status', '')
    date_str   = request.GET.get('date', '')
    cook_id    = request.GET.get('cook', '')

    orders = Order.objects.select_related(
        'customer', 'cook', 'slot'
    ).order_by('-placed_at')

    if status:
        orders = orders.filter(status=status)
    if date_str:
        try:
            d = datetime.date.fromisoformat(date_str)
            orders = orders.filter(placed_at__date=d)
        except ValueError:
            pass
    if cook_id:
        orders = orders.filter(cook_id=cook_id)

    cooks = CookProfile.objects.filter(is_approved=True)

    return render(request, 'admin_panel/all_orders.html', {
        'orders':     orders[:100],
        'status':     status,
        'date_str':   date_str,
        'cook_id':    cook_id,
        'cooks':      cooks,
        'statuses':   ['PENDING','CONFIRMED','PREPARING','OUT_FOR_DELIVERY','DELIVERED','FAILED','CANCELLED'],
    })


@admin_required
def platform_stats(request):
    today     = timezone.localdate()
    last_30   = today - datetime.timedelta(days=30)

    # Orders by day (last 30 days)
    daily_orders = []
    for i in range(29, -1, -1):
        day   = today - datetime.timedelta(days=i)
        count = Order.objects.filter(
            placed_at__date=day,
            status='DELIVERED'
        ).count()
        revenue = Order.objects.filter(
            placed_at__date=day,
            status='DELIVERED'
        ).aggregate(t=Sum('subtotal'))['t'] or 0
        daily_orders.append({
            'date':    day.strftime('%d %b'),
            'count':   count,
            'revenue': float(revenue),
        })

    # Top cooks by orders
    top_cooks = CookProfile.objects.filter(
        is_approved=True
    ).annotate(
        order_count=Count('orders', filter=Q(orders__status='DELIVERED')),
        avg_rating=Avg('reviews__rating')
    ).order_by('-order_count')[:10]

    return render(request, 'admin_panel/stats.html', {
        'daily_orders': daily_orders,
        'top_cooks':    top_cooks,
        'today':        today,
    })
