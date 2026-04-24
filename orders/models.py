from django.db import models
from accounts.models import User
from cooks.models import CookProfile, DailyMenu, MenuItem, DeliverySlot
import random


class SavedAddress(models.Model):
    customer   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_addresses')
    label      = models.CharField(max_length=50, default='Home', help_text='e.g. Home, Office')
    address    = models.TextField()
    latitude   = models.DecimalField(max_digits=9, decimal_places=6)
    longitude  = models.DecimalField(max_digits=9, decimal_places=6)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_addresses'

    def __str__(self):
        return f'{self.customer.name} — {self.label}'

    def save(self, *args, **kwargs):
        if self.is_default:
            SavedAddress.objects.filter(
                customer=self.customer, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Order(models.Model):

    class OrderType(models.TextChoices):
        PREORDER = 'PREORDER', 'Pre-Order'
        SAMEDAY  = 'SAMEDAY',  'Same Day'

    class Status(models.TextChoices):
        PENDING          = 'PENDING',          'Pending'
        CONFIRMED        = 'CONFIRMED',        'Confirmed'
        PREPARING        = 'PREPARING',        'Preparing'
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out for Delivery'
        DELIVERED        = 'DELIVERED',        'Delivered'
        FAILED           = 'FAILED',           'Failed'
        CANCELLED        = 'CANCELLED',        'Cancelled'

    class DeliveryType(models.TextChoices):
        DELIVERY = 'DELIVERY', 'Delivery'
        PICKUP   = 'PICKUP',   'Self Pickup'

    class PaymentMethod(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        COD    = 'COD',    'Cash on Delivery'

    class PaymentStatus(models.TextChoices):
        PENDING  = 'PENDING',  'Pending'
        PAID     = 'PAID',     'Paid'
        FAILED   = 'FAILED',   'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    customer        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cook            = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name='orders')
    menu            = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='orders')
    slot            = models.ForeignKey(DeliverySlot, on_delete=models.SET_NULL, null=True, related_name='orders')
    address         = models.ForeignKey(SavedAddress, on_delete=models.SET_NULL, null=True, blank=True)

    order_type      = models.CharField(max_length=10, choices=OrderType.choices)
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    delivery_type   = models.CharField(max_length=10, choices=DeliveryType.choices)
    payment_method  = models.CharField(max_length=10, choices=PaymentMethod.choices)
    payment_status  = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_ref     = models.CharField(max_length=100, blank=True)

    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee    = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    pin_code        = models.CharField(max_length=4, blank=True)
    placed_at       = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-placed_at']

    def __str__(self):
        return f'Order #{self.id} — {self.customer.name} from {self.cook.kitchen_name}'

    def generate_pin(self):
        self.pin_code = str(random.randint(1000, 9999))

    def calculate_totals(self):
        self.subtotal     = sum(item.line_total() for item in self.items.all())
        self.platform_fee = round(self.subtotal * 0.002, 2)
        self.total        = self.subtotal + self.platform_fee + self.delivery_charge

    def is_prepaid(self):
        return self.payment_method == self.PaymentMethod.ONLINE

    def can_review(self):
        return self.status == self.Status.DELIVERED


class OrderItem(models.Model):
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item   = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='order_items')
    quantity    = models.PositiveIntegerField(default=1)
    unit_price  = models.DecimalField(max_digits=8, decimal_places=2)
    dish_name   = models.CharField(max_length=150)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f'{self.quantity}x {self.dish_name} (Order #{self.order.id})'

    def line_total(self):
        return self.unit_price * self.quantity


class FailedDelivery(models.Model):

    class Reason(models.TextChoices):
        NOT_HOME      = 'NOT_HOME',      'Customer not home'
        WRONG_ADDRESS = 'WRONG_ADDRESS', 'Wrong address'
        REFUSED       = 'REFUSED',       'Customer refused'
        OTHER         = 'OTHER',         'Other'

    order       = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='failed_delivery')
    reason      = models.CharField(max_length=20, choices=Reason.choices)
    photo       = models.ImageField(upload_to='failed_deliveries/')
    reported_at = models.DateTimeField(auto_now_add=True)
    notes       = models.TextField(blank=True)

    class Meta:
        db_table = 'failed_deliveries'

    def __str__(self):
        return f'Failed delivery for Order #{self.order.id}'