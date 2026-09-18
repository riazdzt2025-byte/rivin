from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Category, Product, Customer, Order, OrderItem, Coupon, SiteSetting

class TrilingualTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(code='stationery', name_bn='স্টেশনারি', name_en='Stationery', name_ar='قرطاسية')

    def test_display_name_fallback(self):
        p = Product.objects.create(sku='rivin-0001', category=self.cat, name_bn='খাতা', name_en='', name_ar='', price=Decimal('50.00'), stock=10)
        self.assertEqual(p.display_name('en'), 'খাতা')  # fallback to bn
        self.assertEqual(p.display_name('ar'), 'খাতা')
        self.assertEqual(p.display_name('bn'), 'খাতা')
        p.name_en = 'Notebook'
        p.save()
        self.assertEqual(p.display_name('en'), 'Notebook')

    def test_money_and_stock_validation(self):
        p = Product(sku='rivin-0002', category=self.cat, name_bn='কলম', price=Decimal('-5.00'), stock=-1)
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_order_no_generated(self):
        cust = Customer.objects.create(name='Test', mobile='01710091015', address='Dhaka')
        o = Order.objects.create(customer=cust, subtotal=Decimal('400.00'), delivery_fee=Decimal('60.00'))
        self.assertTrue(o.order_no.startswith('ORD-'))
        self.assertEqual(o.total, Decimal('460.00'))

    def test_state_machine_valid(self):
        cust = Customer.objects.create(name='A', mobile='01700000001')
        o = Order.objects.create(customer=cust, subtotal=Decimal('300'), delivery_fee=Decimal('60'))
        o.transition_to(Order.CONFIRMED)
        self.assertEqual(o.status, Order.CONFIRMED)
        o.transition_to(Order.PACKED)
        o.transition_to(Order.OUT_FOR_DELIVERY)
        o.transition_to(Order.DELIVERED)
        self.assertIsNotNone(o.delivered_at)
        # cannot go back
        from .models import InvalidOrderTransition
        with self.assertRaises(InvalidOrderTransition):
            o.transition_to(Order.PLACED)

    def test_state_machine_invalid(self):
        cust = Customer.objects.create(name='B', mobile='01700000002')
        o = Order.objects.create(customer=cust, subtotal=Decimal('300'), delivery_fee=Decimal('60'))
        from .models import InvalidOrderTransition
        with self.assertRaises(InvalidOrderTransition):
            o.transition_to(Order.DELIVERED)  # must go through steps

    def test_coupon_percent(self):
        c = Coupon.objects.create(code='EID10', type='percent', value=Decimal('10.00'), is_active=True)
        self.assertTrue(c.is_valid_for(Decimal('500')))
        self.assertEqual(c.discount_for(Decimal('500')), Decimal('50.00'))

    def test_coupon_min_subtotal(self):
        c = Coupon.objects.create(code='BIG', type='fixed', value=Decimal('100'), min_subtotal=Decimal('1000'), is_active=True)
        self.assertFalse(c.is_valid_for(Decimal('500')))
        self.assertEqual(c.discount_for(Decimal('500')), Decimal('0.00'))

    def test_audit_snapshot(self):
        cust = Customer.objects.create(name='C', mobile='01700000003')
        o = Order.objects.create(customer=cust, subtotal=Decimal('350'), delivery_fee=Decimal('60'))
        p = Product.objects.create(sku='rivin-0003', category=self.cat, name_bn='ব্যাগ', name_en='Bag', name_ar='حقيبة', price=Decimal('350'), stock=5)
        item = OrderItem.objects.create(order=o, product=p, unit_price_snapshot=p.price, qty=1)
        self.assertEqual(item.product_name_snapshot['ar'], 'حقيبة')
        # change product name later -> snapshot stays
        p.name_ar = 'شنطة'
        p.save()
        item.refresh_from_db()
        self.assertEqual(item.product_name_snapshot['ar'], 'حقيبة')

class ApiLanguageTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(code='cat1', name_bn='ক্যাট১', name_en='Cat1', name_ar='فئة1')
        Product.objects.create(sku='rivin-t1', category=self.cat, name_bn='পণ্য১', name_en='Product1', name_ar='منتج1', price=Decimal('100'), stock=10)

    def test_products_lang_ar_returns_rtl(self):
        resp = self.client.get('/api/v1/products/?lang=ar')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['dir'], 'rtl')
        self.assertEqual(data['products'][0]['name'], 'منتج1')

    def test_products_lang_bn(self):
        resp = self.client.get('/api/v1/products/?lang=bn')
        data = resp.json()
        self.assertEqual(data['dir'], 'ltr')
        self.assertEqual(data['products'][0]['name'], 'পণ্য১')
