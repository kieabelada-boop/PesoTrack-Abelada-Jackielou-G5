from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from products.models import Product, PriceRecord

User = get_user_model()


class CoreFeatureModelTests(TestCase):
    def setUp(self):
        self.reseller = User.objects.create_user(
            username='maria_reseller',
            email='maria@example.com',
            password='TestPassword123!',
            role='RESELLER',
            business_name="Maria's Sari-Sari Store"
        )

    def test_predefined_test_case_1_price_hike_triggers_alert(self):
        """
        Test Case 1 (Standard price hike triggering low-margin alert):
        - Product: Instant Noodles
        - Initial Cost: ₱10.00, Selling Price: ₱13.00, Target Threshold: 20.00%
        - Initial Margin: (13 - 10) / 13 * 100 = 23.08% (Healthy >= 20%)
        - Supplier increases cost to: ₱11.50
        - Price Change: +₱1.50 (+15.00%)
        - New Unit Profit: ₱1.50
        - New Margin: (13 - 11.50) / 13 * 100 = 11.54%
        - Alert: Triggered (11.54% < 20.00%)
        - Suggested Selling Price: 11.50 / (1 - 0.20) = ₱14.38
        """
        product = Product.objects.create(
            user=self.reseller,
            name="Instant Noodles",
            category="instant_meals",
            unit="pack",
            selling_price=Decimal('13.00'),
            margin_threshold=Decimal('20.00'),
        )
        # Baseline price record
        rec1 = PriceRecord.objects.create(
            product=product,
            purchase_price=Decimal('10.00'),
            effective_date=timezone.now().date(),
            supplier="Puregold",
            recorded_by=self.reseller
        )

        # Baseline checks
        self.assertEqual(product.current_purchase_price, Decimal('10.00'))
        self.assertIsNone(product.previous_purchase_price)
        self.assertEqual(product.unit_profit, Decimal('3.00'))
        self.assertEqual(product.profit_margin_percentage, Decimal('23.08'))
        self.assertFalse(product.is_low_margin)
        self.assertFalse(product.is_loss)

        # Supplier logs price hike
        rec2 = PriceRecord.objects.create(
            product=product,
            purchase_price=Decimal('11.50'),
            effective_date=timezone.now().date(),
            supplier="Puregold",
            notes="Manufacturer price hike",
            recorded_by=self.reseller
        )

        # Verify price shift calculations
        self.assertEqual(product.current_purchase_price, Decimal('11.50'))
        self.assertEqual(product.previous_purchase_price, Decimal('10.00'))
        self.assertEqual(product.price_change_amount, Decimal('1.50'))
        self.assertEqual(product.price_change_percentage, Decimal('15.00'))
        self.assertEqual(product.price_trend, 'up')

        # Verify profit margin calculations
        self.assertEqual(product.unit_profit, Decimal('1.50'))
        self.assertEqual(product.profit_margin_percentage, Decimal('11.54'))

        # Verify automated dashboard alert status
        self.assertTrue(product.is_low_margin)
        self.assertFalse(product.is_loss)
        self.assertEqual(product.margin_shortfall, Decimal('8.46'))

        # Verify suggested selling price to restore 20% margin: 11.50 / 0.80 = 14.375 -> 14.38
        self.assertEqual(product.suggested_selling_price, Decimal('14.38'))

    def test_predefined_test_case_2_severe_price_hike_critical_loss(self):
        """
        Test Case 2 (Severe cost hike causing negative profit / loss):
        - Product: Canned Sardines
        - Initial Cost: ₱18.00, Selling Price: ₱22.00
        - Margin: 18.18%
        - Supplier increases cost to: ₱23.00 (exceeds selling price!)
        - Price Change: +₱5.00 (+27.78%)
        - New Unit Profit: ₱22.00 - ₱23.00 = -₱1.00 (Loss!)
        - New Margin: -4.55%
        - Alert: Critical loss alert triggered
        """
        product = Product.objects.create(
            user=self.reseller,
            name="Canned Sardines 155g",
            category="canned_goods",
            unit="can",
            selling_price=Decimal('22.00'),
            margin_threshold=Decimal('15.00'),
        )
        PriceRecord.objects.create(
            product=product,
            purchase_price=Decimal('18.00'),
            recorded_by=self.reseller
        )
        PriceRecord.objects.create(
            product=product,
            purchase_price=Decimal('23.00'),
            recorded_by=self.reseller
        )

        self.assertEqual(product.current_purchase_price, Decimal('23.00'))
        self.assertEqual(product.previous_purchase_price, Decimal('18.00'))
        self.assertEqual(product.price_change_amount, Decimal('5.00'))
        self.assertEqual(product.unit_profit, Decimal('-1.00'))
        self.assertEqual(product.profit_margin_percentage, Decimal('-4.55'))
        self.assertTrue(product.is_loss)
        self.assertTrue(product.is_low_margin)
        # Suggested selling price to restore 15% margin: 23.00 / 0.85 = 27.06
        self.assertEqual(product.suggested_selling_price, Decimal('27.06'))

    def test_predefined_test_case_3_cost_decrease_clears_alert(self):
        """
        Test Case 3 (Supplier price decrease / cost drop):
        - Product: Cooking Oil 250ml
        - Initial Cost: ₱25.00, Selling Price: ₱32.00
        - Initial Margin: 21.88%
        - Supplier lowers price to: ₱22.00
        - Price Change: -₱3.00 (-12.00%)
        - New Profit: ₱10.00
        - New Margin: 31.25%
        - Price Trend: 'down'
        - Alert: Healthy (False)
        """
        product = Product.objects.create(
            user=self.reseller,
            name="Cooking Oil 250ml",
            category="condiments",
            unit="bottle",
            selling_price=Decimal('32.00'),
            margin_threshold=Decimal('20.00'),
        )
        PriceRecord.objects.create(
            product=product,
            purchase_price=Decimal('25.00'),
            recorded_by=self.reseller
        )
        PriceRecord.objects.create(
            product=product,
            purchase_price=Decimal('22.00'),
            recorded_by=self.reseller
        )

        self.assertEqual(product.current_purchase_price, Decimal('22.00'))
        self.assertEqual(product.previous_purchase_price, Decimal('25.00'))
        self.assertEqual(product.price_change_amount, Decimal('-3.00'))
        self.assertEqual(product.price_change_percentage, Decimal('-12.00'))
        self.assertEqual(product.price_trend, 'down')
        self.assertEqual(product.unit_profit, Decimal('10.00'))
        self.assertEqual(product.profit_margin_percentage, Decimal('31.25'))
        self.assertFalse(product.is_low_margin)
        self.assertFalse(product.is_loss)


class CoreFeatureViewsAndCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.reseller1 = User.objects.create_user(
            username='reseller_one',
            email='one@example.com',
            password='Password123!',
            role='RESELLER',
            business_name="Store One"
        )
        self.reseller2 = User.objects.create_user(
            username='reseller_two',
            email='two@example.com',
            password='Password123!',
            role='RESELLER',
            business_name="Store Two"
        )
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='Password123!',
            role='ADMIN'
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Pages requiring login redirect unauthenticated users to login."""
        urls = [
            reverse('product_list'),
            reverse('product_create'),
            reverse('price_record_create'),
            reverse('price_history'),
            reverse('reseller_dashboard'),
            reverse('admin_dashboard'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('login'), response.url)

    def test_product_create_read_update_delete_flow(self):
        """Full CRUD flow for Product through UI views with data persistence in DB."""
        self.client.login(username='reseller_one', password='Password123!')

        # 1. CREATE product with initial purchasing cost
        create_url = reverse('product_create')
        post_data = {
            'name': 'Bear Brand Milk Powder 33g',
            'category': 'beverages',
            'unit': 'sachet',
            'selling_price': '15.00',
            'margin_threshold': '18.00',
            'initial_purchase_price': '11.00',
            'effective_date': timezone.now().date().isoformat(),
            'supplier': 'Nestle Distributor',
            'notes': 'Wholesale box of 48',
            'sku': 'BB-33G',
            'description': 'Fortified powdered milk drink'
        }
        response = self.client.post(create_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify DB persistence
        product = Product.objects.get(name='Bear Brand Milk Powder 33g')
        self.assertEqual(product.user, self.reseller1)
        self.assertEqual(product.selling_price, Decimal('15.00'))
        self.assertEqual(product.current_purchase_price, Decimal('11.00'))
        self.assertEqual(product.price_records.count(), 1)
        initial_record = product.price_records.first()
        self.assertEqual(initial_record.purchase_price, Decimal('11.00'))
        self.assertEqual(initial_record.supplier, 'Nestle Distributor')

        # 2. READ: Product List & Product Detail
        list_response = self.client.get(reverse('product_list'))
        self.assertContains(list_response, 'Bear Brand Milk Powder 33g')

        detail_response = self.client.get(reverse('product_detail', kwargs={'pk': product.pk}))
        self.assertContains(detail_response, 'Bear Brand Milk Powder 33g')
        self.assertContains(detail_response, 'Nestle Distributor')

        # 3. UPDATE product details
        update_url = reverse('product_update', kwargs={'pk': product.pk})
        update_data = {
            'name': 'Bear Brand Milk Powder 33g (Promo Pack)',
            'category': 'beverages',
            'unit': 'sachet',
            'selling_price': '16.00',  # Price increase to improve margin
            'margin_threshold': '18.00',
            'sku': 'BB-33G',
            'description': 'Updated promo pack'
        }
        up_response = self.client.post(update_url, update_data, follow=True)
        self.assertEqual(up_response.status_code, 200)

        product.refresh_from_db()
        self.assertEqual(product.name, 'Bear Brand Milk Powder 33g (Promo Pack)')
        self.assertEqual(product.selling_price, Decimal('16.00'))
        # Margin should now be (16 - 11) / 16 * 100 = 31.25%
        self.assertEqual(product.profit_margin_percentage, Decimal('31.25'))

        # 4. RECORD A PRICE SHIFT (Purchasing cost increases to 14.00)
        record_url = reverse('product_price_record_create', kwargs={'product_id': product.pk})
        price_shift_data = {
            'purchase_price': '14.00',
            'effective_date': timezone.now().date().isoformat(),
            'supplier': 'Nestle Distributor',
            'notes': 'Supplier increased SRP and wholesale cost'
        }
        shift_response = self.client.post(record_url, price_shift_data, follow=True)
        self.assertEqual(shift_response.status_code, 200)

        product.refresh_from_db()
        self.assertEqual(product.current_purchase_price, Decimal('14.00'))
        self.assertEqual(product.previous_purchase_price, Decimal('11.00'))
        self.assertEqual(product.price_records.count(), 2)
        # Margin dropped: (16 - 14) / 16 * 100 = 12.50% < 18.00% threshold -> Alert!
        self.assertEqual(product.profit_margin_percentage, Decimal('12.50'))
        self.assertTrue(product.is_low_margin)

        # 5. ONE-CLICK RESTORE MARGIN: Apply suggested selling price
        # Suggested: 14.00 / (1 - 0.18) = 17.073 -> rounded up to 17.08
        apply_url = reverse('apply_suggested_price', kwargs={'pk': product.pk})
        apply_response = self.client.post(apply_url, follow=True)
        self.assertEqual(apply_response.status_code, 200)

        product.refresh_from_db()
        self.assertEqual(product.selling_price, Decimal('17.08'))
        self.assertFalse(product.is_low_margin)

        # 6. DELETE Product
        delete_url = reverse('product_delete', kwargs={'pk': product.pk})
        del_response = self.client.post(delete_url, follow=True)
        self.assertEqual(del_response.status_code, 200)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(PriceRecord.objects.filter(product_id=product.pk).count(), 0)

    def test_user_isolation_cannot_view_or_edit_other_user_product(self):
        """User isolation: Reseller 1 cannot view or modify Reseller 2's products."""
        product_reseller2 = Product.objects.create(
            user=self.reseller2,
            name="Store 2 Private Item",
            category="snacks",
            unit="piece",
            selling_price=Decimal('50.00'),
            margin_threshold=Decimal('15.00')
        )
        PriceRecord.objects.create(
            product=product_reseller2,
            purchase_price=Decimal('35.00'),
            recorded_by=self.reseller2
        )

        # Log in as Reseller 1
        self.client.login(username='reseller_one', password='Password123!')

        # Reseller 1 viewing product list should NOT see Reseller 2's item
        list_resp = self.client.get(reverse('product_list'))
        self.assertNotContains(list_resp, "Store 2 Private Item")

        # Reseller 1 trying to open detail of Reseller 2's item gets 404
        detail_resp = self.client.get(reverse('product_detail', kwargs={'pk': product_reseller2.pk}))
        self.assertEqual(detail_resp.status_code, 404)

        # Reseller 1 trying to edit Reseller 2's item gets 404
        edit_resp = self.client.get(reverse('product_update', kwargs={'pk': product_reseller2.pk}))
        self.assertEqual(edit_resp.status_code, 404)

        # Reseller 1 trying to delete Reseller 2's item gets 404
        del_resp = self.client.post(reverse('product_delete', kwargs={'pk': product_reseller2.pk}))
        self.assertEqual(del_resp.status_code, 404)

    def test_role_based_dashboard_access_control(self):
        """Reseller cannot open Admin Dashboard; redirected with warning."""
        self.client.login(username='reseller_one', password='Password123!')
        response = self.client.get(reverse('admin_dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        # Should be redirected to reseller dashboard
        self.assertContains(response, "Store One's Dashboard")
        self.assertContains(response, "Access denied")

        # Admin login
        self.client.login(username='admin_user', password='Password123!')
        admin_resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(admin_resp.status_code, 200)
        self.assertContains(admin_resp, "Administrator Dashboard")

    def test_supplier_price_comparison_and_average_cost_matching_screenshot(self):
        """
        Verify supplier price comparison feature matching the user-provided design:
        - Product: Nescafé 3-in-1, Selling Price: ₱50.00 / pack
        - Purchase 1: Gaisano at ₱40.00 (12 packs) on Oct 19
        - Purchase 2: Puregold at ₱43.00 (12 packs) on Oct 20
        - Total packs purchased: 24 packs
        - Average cost / pack: (40*12 + 43*12) / 24 = ₱41.50
        - Lowest supplier: Gaisano with LOWEST badge
        - Puregold cost: ₱43.00 (+₱3.00 vs lowest)
        """
        self.client.login(username='reseller_one', password='Password123!')

        product = Product.objects.create(
            user=self.reseller1,
            name="Nescafé 3-in-1",
            category="beverages",
            unit="pack",
            selling_price=Decimal('50.00'),
            margin_threshold=Decimal('15.00')
        )

        # Record purchase from Gaisano (Oct 19)
        PriceRecord.objects.create(
            product=product,
            recorded_by=self.reseller1,
            supplier="Gaisano",
            purchase_price=Decimal('40.00'),
            quantity=12,
            effective_date=timezone.datetime(2026, 10, 19).date()
        )

        # Record purchase from Puregold (Oct 20)
        PriceRecord.objects.create(
            product=product,
            recorded_by=self.reseller1,
            supplier="Puregold",
            purchase_price=Decimal('43.00'),
            quantity=12,
            effective_date=timezone.datetime(2026, 10, 20).date()
        )

        # Verify model calculations
        self.assertEqual(product.total_units_purchased, 24)
        self.assertEqual(product.average_purchase_price, Decimal('41.50'))
        self.assertEqual(product.selling_price, Decimal('50.00'))

        comp = product.supplier_comparison
        self.assertEqual(len(comp), 2)
        # Gaisano should be first and marked as lowest
        self.assertEqual(comp[0]['name'], "Gaisano")
        self.assertTrue(comp[0]['is_lowest'])
        self.assertEqual(comp[0]['latest_price'], Decimal('40.00'))

        # Puregold should have difference of 3.00
        self.assertEqual(comp[1]['name'], "Puregold")
        self.assertFalse(comp[1]['is_lowest'])
        self.assertEqual(comp[1]['latest_price'], Decimal('43.00'))
        self.assertEqual(comp[1]['difference_from_lowest'], Decimal('3.00'))

        # Verify detail page UI renders exact values
        resp = self.client.get(reverse('product_detail', kwargs={'pk': product.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Nescafé 3-in-1")
        self.assertContains(resp, "24 packs purchased")
        self.assertContains(resp, "41.50")  # Average cost
        self.assertContains(resp, "50.00")  # Selling price
        self.assertContains(resp, "Gaisano")
        self.assertContains(resp, "LOWEST")
        self.assertContains(resp, "Puregold")
        self.assertContains(resp, "40.00")
        self.assertContains(resp, "43.00")
        self.assertContains(resp, "Compare stores")
        self.assertContains(resp, "Purchase history")

    def test_adjust_selling_price_action(self):
        """Store owner can adjust selling price directly via Adjust price action."""
        self.client.login(username='reseller_one', password='Password123!')

        product = Product.objects.create(
            user=self.reseller1,
            name="Tang Orange 25g",
            category="beverages",
            unit="sachet",
            selling_price=Decimal('18.00'),
            margin_threshold=Decimal('20.00')
        )
        PriceRecord.objects.create(
            product=product,
            recorded_by=self.reseller1,
            supplier="Puregold",
            purchase_price=Decimal('15.00'),
            quantity=10
        )

        adjust_url = reverse('adjust_selling_price', kwargs={'pk': product.pk})
        resp = self.client.post(adjust_url, {'selling_price': '20.00'}, follow=True)
        self.assertEqual(resp.status_code, 200)

        product.refresh_from_db()
        self.assertEqual(product.selling_price, Decimal('20.00'))
        # Margin: (20 - 15) / 20 * 100 = 25.00% >= 20.00%
        self.assertEqual(product.profit_margin_percentage, Decimal('25.00'))
        self.assertFalse(product.is_low_margin)

    def test_compare_suppliers_catalog_view(self):
        """Reseller can view the catalog-wide supplier comparison page."""
        self.client.login(username='reseller_one', password='Password123!')

        product = Product.objects.create(
            user=self.reseller1,
            name="Lucky Me Beef",
            category="instant_meals",
            unit="pack",
            selling_price=Decimal('15.00'),
            margin_threshold=Decimal('15.00')
        )
        PriceRecord.objects.create(
            product=product,
            recorded_by=self.reseller1,
            supplier="Gaisano",
            purchase_price=Decimal('11.00'),
            quantity=20
        )
        PriceRecord.objects.create(
            product=product,
            recorded_by=self.reseller1,
            supplier="Puregold",
            purchase_price=Decimal('12.50'),
            quantity=20
        )

        resp = self.client.get(reverse('compare_suppliers'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Compare Stores &amp; Wholesalers")
        self.assertContains(resp, "Lucky Me Beef")
        self.assertContains(resp, "Gaisano")
        self.assertContains(resp, "Puregold")
        self.assertContains(resp, "1.50")  # Savings per unit: 12.50 - 11.00 = 1.50
