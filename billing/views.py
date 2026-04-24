from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CommissionInvoice, CookBankDetail
from cooks.models import CookProfile
from orders.models import Order
import datetime


@login_required
def cook_billing(request):
    """Cook's billing dashboard — sees their own invoices"""
    if request.user.role != 'COOK':
        messages.error(request, 'Access denied.')
        return redirect('/')

    try:
        cook = request.user.cook_profile
    except Exception:
        messages.error(request, 'Cook profile not found. Please complete your setup.')
        return redirect('cook:onboarding')
    invoices = CommissionInvoice.objects.filter(
        cook=cook
    ).order_by('-period_start')

    # Bank details
    try:
        bank_detail = cook.bank_detail
    except CookBankDetail.DoesNotExist:
        bank_detail = None

    # Summary stats
    total_paid   = sum(
        float(i.commission_amount)
        for i in invoices if i.status == 'PAID'
    )
    total_unpaid = sum(
        float(i.commission_amount)
        for i in invoices if i.status == 'UNPAID'
    )

    # Current month earnings (live)
    today        = timezone.localdate()
    month_start  = today.replace(day=1)
    month_earnings = Order.objects.filter(
        cook        = cook,
        status      = 'DELIVERED',
        placed_at__date__gte = month_start,
    ).values_list('subtotal', flat=True)
    current_month_gross      = sum(float(s) for s in month_earnings)
    current_month_commission = round(current_month_gross * 0.05, 2)

    context = {
        'cook':                    cook,
        'invoices':                invoices,
        'bank_detail':             bank_detail,
        'total_paid':              total_paid,
        'total_unpaid':            total_unpaid,
        'current_month_gross':     current_month_gross,
        'current_month_commission':current_month_commission,
        'today':                   today,
    }
    return render(request, 'billing/cook_billing.html', context)


@login_required
def save_bank_details(request):
    if request.user.role != 'COOK':
        return redirect('/')

    try:
        cook = request.user.cook_profile
    except Exception:
        return redirect('cook:onboarding')
    if request.method == 'POST':
        upi_id         = request.POST.get('upi_id', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        ifsc_code      = request.POST.get('ifsc_code', '').strip()
        account_name   = request.POST.get('account_name', '').strip()

        bank_detail, created = CookBankDetail.objects.get_or_create(cook=cook)
        bank_detail.upi_id         = upi_id
        bank_detail.account_number = account_number
        bank_detail.ifsc_code      = ifsc_code
        bank_detail.account_name   = account_name
        bank_detail.save()
        messages.success(request, 'Bank details saved.')

    return redirect('billing:cook_billing')


@login_required
def admin_billing(request):
    """Admin billing panel — sees all invoices across all cooks"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('/')

    status_filter = request.GET.get('status', '')
    invoices      = CommissionInvoice.objects.select_related(
        'cook__user'
    ).order_by('-period_start', 'status')

    if status_filter:
        invoices = invoices.filter(status=status_filter)

    # Platform stats
    total_commission_collected = sum(
        float(i.commission_amount)
        for i in CommissionInvoice.objects.filter(status='PAID')
    )
    total_commission_pending = sum(
        float(i.commission_amount)
        for i in CommissionInvoice.objects.filter(status='UNPAID')
    )
    total_platform_fee = sum(
        float(o.platform_fee)
        for o in Order.objects.filter(status='DELIVERED')
    )

    context = {
        'invoices':                    invoices,
        'status_filter':               status_filter,
        'total_commission_collected':  total_commission_collected,
        'total_commission_pending':    total_commission_pending,
        'total_platform_fee':          total_platform_fee,
    }
    return render(request, 'billing/admin_billing.html', context)


@login_required
def mark_invoice_paid(request, pk):
    """Admin marks a commission invoice as paid"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('/')

    invoice = get_object_or_404(CommissionInvoice, pk=pk)
    if request.method == 'POST':
        payment_ref = request.POST.get('payment_ref', '').strip()
        invoice.status      = 'PAID'
        invoice.paid_at     = timezone.now()
        invoice.payment_ref = payment_ref
        invoice.save()

        from notifications.models import Notification
        Notification.objects.create(
            user    = invoice.cook.user,
            type    = 'INVOICE_CREATED',
            title   = 'Commission invoice marked as paid',
            message = (
                f'Your commission invoice of ₹{invoice.commission_amount} '
                f'for {invoice.period_start.strftime("%B %Y")} '
                f'has been marked as paid. Thank you!'
            ),
        )
        messages.success(request, f'Invoice #{invoice.pk} marked as paid.')

    return redirect('billing:admin_billing')


@login_required
def generate_invoice_manual(request):
    """Admin manually triggers invoice generation"""
    if request.user.role != 'ADMIN':
        return redirect('/')

    if request.method == 'POST':
        from django.core.management import call_command
        month = request.POST.get('month')
        year  = request.POST.get('year')
        try:
            kwargs = {'force': True}
            if month: kwargs['month'] = int(month)
            if year:  kwargs['year']  = int(year)
            call_command('generate_invoices', **kwargs)
            messages.success(request, 'Invoices generated successfully.')
        except Exception as e:
            messages.error(request, f'Error generating invoices: {e}')

    return redirect('billing:admin_billing')
