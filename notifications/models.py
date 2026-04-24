from django.db import models
from accounts.models import User


class Notification(models.Model):

    class Type(models.TextChoices):
        ORDER_PLACED    = 'ORDER_PLACED',    'Order Placed'
        ORDER_CONFIRMED = 'ORDER_CONFIRMED', 'Order Confirmed'
        ORDER_PREPARING = 'ORDER_PREPARING', 'Order Preparing'
        ORDER_OUT       = 'ORDER_OUT',       'Out for Delivery'
        ORDER_DELIVERED  = 'ORDER_DELIVERED', 'Order Delivered'
        ORDER_CANCELLED = 'ORDER_CANCELLED', 'Order Cancelled'
        ORDER_FAILED    = 'ORDER_FAILED',    'Order Failed'
        REVIEW_RECEIVED = 'REVIEW_RECEIVED', 'Review Received'
        INVOICE_CREATED = 'INVOICE_CREATED', 'Invoice Created'

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=20, choices=Type.choices)
    title      = models.CharField(max_length=150)
    message    = models.TextField()
    photo      = models.ImageField(upload_to='notification_photos/', null=True, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.type} → {self.user.name}'