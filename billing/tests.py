import datetime
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from cooks.models import CookProfile, DailyMenu, DeliverySlot
from orders.models import Order, SavedAddress


class PaymentLifecycleTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email='refund@example.com',
            phone='9333333333',
            name='Refund Customer',
            role='CUSTOMER',
            password='testpass123',
        )
        self.cook_user = User.objects.create_user(
            email='refundcook@example.com',
            phone='9444444444',
            name='Refund Cook',
            role='COOK',
            password='testpass123',
        )
        self.cook = CookProfile.objects.create(
            user=self.cook_user,
            kitchen_name='Refund Kitchen',
            bio='Refundable meals',
            phone='9444444444',
            address='44 Market Road',
            latitude=Decimal('22.572600'),
            longitude=Decimal('88.363900'),
            cuisine_tags='Bengali',
            daily_capacity=20,
            order_cutoff=datetime.time(22, 0),
            is_approved=True,
            is_active=True,
        )
        self.slot = DeliverySlot.objects.create(
            cook=self.cook,
            label='7-8 PM',
            start_time=datetime.time(19, 0),
            end_time=datetime.time(20, 0),
            is_active=True,
        )
        self.menu = DailyMenu.objects.create(
            cook=self.cook,
            slot=self.slot,
            menu_date=timezone.localdate(),
            meal_type=DailyMenu.MealType.DINNER,
            order_cutoff=datetime.time(22, 0),
            status=DailyMenu.Status.PUBLISHED,
        )
        self.address = SavedAddress.objects.create(
            customer=self.customer,
            label='Home',
            address='55 Some Street',
            latitude=Decimal('22.572700'),
            longitude=Decimal('88.363800'),
            is_default=True,
        )
        self.order = Order.objects.create(
            customer=self.customer,
            cook=self.cook,
            menu=self.menu,
            slot=self.slot,
            address=self.address,
            order_type=Order.OrderType.SAMEDAY,
            status=Order.Status.CONFIRMED,
            delivery_type=Order.DeliveryType.DELIVERY,
            payment_method=Order.PaymentMethod.ONLINE,
            payment_status=Order.PaymentStatus.PAID,
            subtotal=Decimal('200.00'),
            platform_fee=Decimal('0.40'),
            total=Decimal('200.40'),
        )
        self.client.force_login(self.customer)

    def test_cancel_paid_online_order_marks_refund_pending(self):
        response = self.client.post(reverse('orders:cancel_order', args=[self.order.pk]))

        self.order.refresh_from_db()
        self.assertRedirects(response, reverse('orders:order_list'))
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUND_PENDING)
        self.assertIsNotNone(self.order.refund_requested_at)

    @override_settings(PLATFORM_FEE_RATE=Decimal('0.50'))
    def test_platform_fee_uses_configured_rate(self):
        fee = Order.calculate_platform_fee(Decimal('200.00'))
        self.assertEqual(fee, Decimal('1.00'))
