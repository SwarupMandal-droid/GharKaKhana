from django.db import models
from accounts.models import User
from cooks.models import CookProfile
from orders.models import Order


class Review(models.Model):
    order      = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    customer   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    cook       = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name='reviews')
    rating     = models.PositiveSmallIntegerField()
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'reviews'
        unique_together = ('order', 'customer')
        ordering        = ['-created_at']

    def __str__(self):
        return f'{self.rating}★ by {self.customer.name} for {self.cook.kitchen_name}'