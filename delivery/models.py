from django.db import models
from accounts.models import User
from cooks.models import CookProfile
from orders.models import Order


class DeliveryPerson(models.Model):
    user    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_profile')
    cook    = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name='delivery_persons')
    phone   = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'delivery_persons'

    def __str__(self):
        return f'{self.user.name} — {self.cook.kitchen_name}'


class Delivery(models.Model):

    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'Pending'
        ASSIGNED  = 'ASSIGNED',  'Assigned'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED    = 'FAILED',    'Failed'

    order           = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_person = models.ForeignKey(DeliveryPerson, on_delete=models.SET_NULL,
                                         null=True, related_name='deliveries')
    status          = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    delivery_address= models.TextField()
    cash_collected  = models.BooleanField(default=False)
    delivered_at    = models.DateTimeField(null=True, blank=True)
    sequence        = models.PositiveIntegerField(default=0, help_text='Order in delivery route')

    class Meta:
        db_table = 'deliveries'
        ordering = ['sequence']

    def __str__(self):
        return f'Delivery for Order #{self.order.id}'