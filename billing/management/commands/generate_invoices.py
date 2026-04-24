from django.core.management.base import BaseCommand
from django.utils import timezone
from billing.models import CommissionInvoice, CookBankDetail
from cooks.models import CookProfile
from orders.models import Order
import datetime


class Command(BaseCommand):
    help = 'Generate monthly commission invoices for all active cooks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month', type=int,
            help='Month to generate invoices for (1-12). Defaults to last month.'
        )
        parser.add_argument(
            '--year', type=int,
            help='Year to generate invoices for. Defaults to current year.'
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Regenerate even if invoice already exists for this period.'
        )

    def handle(self, *args, **options):
        today = datetime.date.today()

        # Default to last month
        if options['month']:
            month = options['month']
            year  = options['year'] or today.year
        else:
            first_of_this_month = today.replace(day=1)
            last_month          = first_of_this_month - datetime.timedelta(days=1)
            month = last_month.month
            year  = last_month.year

        period_start = datetime.date(year, month, 1)
        # Last day of the month
        if month == 12:
            period_end = datetime.date(year, 12, 31)
        else:
            period_end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        due_date = today.replace(day=1) + datetime.timedelta(days=15)

        self.stdout.write(
            f'Generating invoices for {period_start} to {period_end}...'
        )

        cooks = CookProfile.objects.filter(is_approved=True)
        created_count = 0
        skipped_count = 0

        for cook in cooks:
            # Skip if invoice already exists
            existing = CommissionInvoice.objects.filter(
                cook         = cook,
                period_start = period_start,
                period_end   = period_end,
            ).exists()

            if existing and not options['force']:
                self.stdout.write(f'  Skipping {cook.kitchen_name} — invoice already exists')
                skipped_count += 1
                continue

            # Sum all delivered orders for this period
            gross = Order.objects.filter(
                cook        = cook,
                status      = 'DELIVERED',
                placed_at__date__gte = period_start,
                placed_at__date__lte = period_end,
            ).values_list('subtotal', flat=True)

            gross_earnings = sum(float(s) for s in gross)

            if gross_earnings == 0:
                self.stdout.write(
                    f'  Skipping {cook.kitchen_name} — no earnings this period'
                )
                skipped_count += 1
                continue

            commission_rate   = 5.00
            commission_amount = round(gross_earnings * commission_rate / 100, 2)

            if existing and options['force']:
                CommissionInvoice.objects.filter(
                    cook=cook, period_start=period_start
                ).delete()

            CommissionInvoice.objects.create(
                cook              = cook,
                period_start      = period_start,
                period_end        = period_end,
                gross_earnings    = gross_earnings,
                commission_rate   = commission_rate,
                commission_amount = commission_amount,
                status            = 'UNPAID',
                due_date          = due_date,
            )

            # Notify cook
            from notifications.models import Notification
            Notification.objects.create(
                user    = cook.user,
                type    = 'INVOICE_CREATED',
                title   = 'Monthly commission invoice generated',
                message = (
                    f'Your commission invoice for {period_start.strftime("%B %Y")} '
                    f'is ₹{commission_amount:.2f} (5% of ₹{gross_earnings:.2f}). '
                    f'Due by {due_date.strftime("%d %B %Y")}.'
                ),
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ {cook.kitchen_name} — '
                    f'₹{gross_earnings:.2f} gross → '
                    f'₹{commission_amount:.2f} commission'
                )
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {created_count} invoices created, {skipped_count} skipped.'
            )
        )
