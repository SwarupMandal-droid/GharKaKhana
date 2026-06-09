import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from cooks.models import CookProfile, DailyMenu, DeliverySlot, Dish, MenuItem
from notifications.models import Notification
from orders.models import Order, OrderItem, SavedAddress
from reviews.models import Review


class OrderFlowTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email='customer@example.com',
            phone='9000000001',
            name='Customer One',
            role='CUSTOMER',
            password='testpass123',
        )
        self.cook_user = User.objects.create_user(
            email='cook@example.com',
            phone='9000000002',
            name='Cook One',
            role='COOK',
            password='testpass123',
        )
        self.cook = CookProfile.objects.create(
            user=self.cook_user,
            kitchen_name='Aunty Kitchen',
            bio='Fresh daily meals',
            phone='9000000002',
            address='12 Main Street',
            latitude=Decimal('22.572600'),
            longitude=Decimal('88.363900'),
            cuisine_tags='Bengali',
            daily_capacity=20,
            order_cutoff=datetime.time(22, 0),
            same_day_enabled=True,
            same_day_limit=5,
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
        self.dish = Dish.objects.create(
            cook=self.cook,
            name='Veg Thali',
            description='Simple dinner',
            base_price=Decimal('150.00'),
            is_active=True,
        )
        self.menu = DailyMenu.objects.create(
            cook=self.cook,
            slot=self.slot,
            menu_date=timezone.localdate() + datetime.timedelta(days=1),
            meal_type=DailyMenu.MealType.DINNER,
            order_cutoff=datetime.time(22, 0),
            status=DailyMenu.Status.PUBLISHED,
        )
        self.menu_item = MenuItem.objects.create(
            menu=self.menu,
            dish=self.dish,
            quantity_available=10,
        )
        self.address = SavedAddress.objects.create(
            customer=self.customer,
            label='Home',
            address='13 Main Street',
            latitude=Decimal('22.572700'),
            longitude=Decimal('88.363800'),
            is_default=True,
        )
        self.client.force_login(self.customer)

    def test_pickup_order_uses_selected_address_without_crashing(self):
        response = self.client.post(reverse('orders:place_order'), {
            'cook_id': self.cook.pk,
            'menu_id': self.menu.pk,
            'slot_id': self.slot.pk,
            'address_id': self.address.pk,
            'delivery_type': 'PICKUP',
            'payment_method': 'COD',
            'items_json': f'{{"{self.menu_item.pk}": {{"qty": 2}}}}',
        })

        order = Order.objects.get(customer=self.customer)
        self.assertRedirects(response, reverse('orders:order_detail', args=[order.pk]))
        self.assertEqual(order.delivery_type, Order.DeliveryType.PICKUP)
        self.assertEqual(order.address, self.address)
        self.assertEqual(order.delivery_charge, 0)

    def test_submit_review_creates_review_and_notification(self):
        order = Order.objects.create(
            customer=self.customer,
            cook=self.cook,
            menu=self.menu,
            slot=self.slot,
            address=self.address,
            order_type=Order.OrderType.PREORDER,
            status=Order.Status.DELIVERED,
            delivery_type=Order.DeliveryType.DELIVERY,
            payment_method=Order.PaymentMethod.COD,
            payment_status=Order.PaymentStatus.PAID,
            subtotal=Decimal('150.00'),
            total=Decimal('150.00'),
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=1,
            unit_price=Decimal('150.00'),
            dish_name='Veg Thali',
        )

        response = self.client.post(reverse('orders:submit_review', args=[order.pk]), {
            'rating': 4,
            'comment': 'Tasty and homely.',
        })

        self.assertRedirects(response, reverse('orders:order_detail', args=[order.pk]))
        review = Review.objects.get(order=order)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Tasty and homely.')
        self.assertTrue(Notification.objects.filter(
            user=self.cook_user,
            type='REVIEW_RECEIVED',
        ).exists())

    def test_repeat_order_prefills_matching_live_menu_items(self):
        delivered_order = Order.objects.create(
            customer=self.customer,
            cook=self.cook,
            menu=self.menu,
            slot=self.slot,
            address=self.address,
            order_type=Order.OrderType.PREORDER,
            status=Order.Status.DELIVERED,
            delivery_type=Order.DeliveryType.DELIVERY,
            payment_method=Order.PaymentMethod.COD,
            payment_status=Order.PaymentStatus.PAID,
            subtotal=Decimal('300.00'),
            total=Decimal('300.60'),
        )
        OrderItem.objects.create(
            order=delivered_order,
            menu_item=self.menu_item,
            quantity=2,
            unit_price=Decimal('150.00'),
            dish_name='Veg Thali',
        )

        response = self.client.get(
            reverse('customer:cook_detail', args=[self.cook.pk]),
            {'repeat_order': delivered_order.pk},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.context['repeat_order_payload_json']
        self.assertIn(f'"{self.menu_item.pk}"', payload)
        self.assertIn('"qty": 2', payload)
