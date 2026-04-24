from django.db import models
from cooks.models import CookProfile


class CookBankDetail(models.Model):
    cook           = models.OneToOneField(CookProfile, on_delete=models.CASCADE, related_name='bank_detail')
    upi_id         = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    ifsc_code      = models.CharField(max_length=20, blank=True)
    account_name   = models.CharField(max_length=100, blank=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cook_bank_details'

    def __str__(self):
        return f'Bank details — {self.cook.kitchen_name}'


class CommissionInvoice(models.Model):

    class Status(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PAID   = 'PAID',   'Paid'

    cook              = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name='invoices')
    period_start      = models.DateField()
    period_end        = models.DateField()
    gross_earnings    = models.DecimalField(max_digits=12, decimal_places=2)
    commission_rate   = models.DecimalField(max_digits=5,  decimal_places=2, default=5.00)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status            = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    due_date          = models.DateField()
    paid_at           = models.DateTimeField(null=True, blank=True)
    payment_ref       = models.CharField(max_length=100, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'commission_invoices'
        ordering = ['-period_start']

    def __str__(self):
        return f'Invoice — {self.cook.kitchen_name} — {self.period_start} to {self.period_end}'