import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from cooks.models import CookProfile, DailyMenu, DeliverySlot, Dish
from orders.models import Order, SavedAddress
from reviews.models import Review


class LandingPageTests(TestCase):
    def test_landing_page_uses_real_metrics(self):
        customer = User.objects.create_user(
            email='buyer@example.com',
            phone='9111111111',
            name='Buyer',
            role='CUSTOMER',
            password='testpass123',
        )
        cook_user = User.objects.create_user(
            email='cooklanding@example.com',
            phone='9222222222',
            name='Landing Cook',
            role='COOK',
            password='testpass123',
        )
        cook = CookProfile.objects.create(
            user=cook_user,
            kitchen_name='Landing Kitchen',
            bio='Daily meals',
            phone='9222222222',
            address='22 Lane',
            latitude=Decimal('22.572600'),
            longitude=Decimal('88.363900'),
            cuisine_tags='North Indian',
            daily_capacity=15,
            order_cutoff=datetime.time(21, 0),
            is_approved=True,
            is_active=True,
        )
        slot = DeliverySlot.objects.create(
            cook=cook,
            label='1-2 PM',
            start_time=datetime.time(13, 0),
            end_time=datetime.time(14, 0),
            is_active=True,
        )
        menu = DailyMenu.objects.create(
            cook=cook,
            slot=slot,
            menu_date=datetime.date.today(),
            meal_type=DailyMenu.MealType.LUNCH,
            order_cutoff=datetime.time(10, 0),
            status=DailyMenu.Status.PUBLISHED,
        )
        dish = Dish.objects.create(
            cook=cook,
            name='Paneer Curry',
            base_price=Decimal('180.00'),
            is_active=True,
        )
        address = SavedAddress.objects.create(
            customer=customer,
            label='Home',
            address='11 Some Street',
            latitude=Decimal('22.572700'),
            longitude=Decimal('88.363800'),
            is_default=True,
        )
        order = Order.objects.create(
            customer=customer,
            cook=cook,
            menu=menu,
            slot=slot,
            address=address,
            order_type=Order.OrderType.SAMEDAY,
            status=Order.Status.DELIVERED,
            delivery_type=Order.DeliveryType.DELIVERY,
            payment_method=Order.PaymentMethod.COD,
            payment_status=Order.PaymentStatus.PAID,
            subtotal=Decimal('180.00'),
            total=Decimal('180.00'),
        )
        Review.objects.create(
            order=order,
            customer=customer,
            cook=cook,
            rating=5,
            comment='Excellent',
        )

        response = self.client.get(reverse('landing'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['landing_metrics']['verified_kitchens'], 1)
        self.assertEqual(response.context['landing_metrics']['meals_delivered'], 1)
        self.assertEqual(response.context['landing_metrics']['active_dishes'], 1)
        self.assertEqual(response.context['landing_metrics']['avg_rating'], 5.0)
        self.assertContains(response, 'Verified kitchens')
        self.assertContains(response, dish.name)
