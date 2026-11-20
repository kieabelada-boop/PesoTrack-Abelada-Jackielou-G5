from decimal import Decimal, ROUND_UP
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Product(models.Model):
    class Category(models.TextChoices):
        BEVERAGES = 'beverages', 'Beverages & Drinks'
        CANNED_GOODS = 'canned_goods', 'Canned Goods'
        INSTANT_MEALS = 'instant_meals', 'Instant Noodles & Meals'
        SNACKS = 'snacks', 'Snacks & Confectionery'
        CONDIMENTS = 'condiments', 'Condiments & Cooking Essentials'
        TOILETRIES = 'toiletries', 'Toiletries & Personal Care'
        HOUSEHOLD = 'household', 'Household & Cleaning Supplies'
        GENERAL = 'general', 'General Merchandise'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Store Owner"
    )
    name = models.CharField(max_length=150, verbose_name="Product Name")
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.GENERAL,
        verbose_name="Category"
    )
    sku = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="SKU / Barcode"
    )
    unit = models.CharField(
        max_length=30,
        default="piece",
        help_text="e.g. piece, pack, bottle, can, sachet, box, kg",
        verbose_name="Unit of Measure"
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Selling Price (₱)",
        help_text="Current retail price to customers in PHP"
    )
    margin_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        verbose_name="Profit Margin Alert Threshold (%)",
        help_text="Display dashboard alert when profit margin falls below this percentage"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description / Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    @property
    def latest_price_record(self):
        """Returns the most recent price record."""
        return self.price_records.order_by('-effective_date', '-created_at', '-id').first()

    @property
    def current_purchase_price(self):
        """Returns the latest purchase price, or Decimal('0.00') if none recorded."""
        latest = self.latest_price_record
        return latest.purchase_price if latest else Decimal('0.00')

    @property
    def previous_price_record(self):
        """Returns the second most recent price record, or None."""
        records = list(self.price_records.order_by('-effective_date', '-created_at', '-id')[:2])
        if len(records) > 1:
            return records[1]
        return None

    @property
    def previous_purchase_price(self):
        """Returns the previous purchase price, or None if only one or no record exists."""
        prev = self.previous_price_record
        return prev.purchase_price if prev else None

    @property
    def price_change_amount(self):
        """
        Difference between current purchase price and previous purchase price.
        Positive means cost increased (hike); negative means cost decreased.
        """
        if self.previous_purchase_price is not None:
            return self.current_purchase_price - self.previous_purchase_price
        return Decimal('0.00')

    @property
    def price_change_percentage(self):
        """
        Percentage change from previous purchase price to current.
        """
        if self.previous_purchase_price and self.previous_purchase_price > 0:
            change = (self.price_change_amount / self.previous_purchase_price) * Decimal('100')
            return round(change, 2)
        return Decimal('0.00')

    @property
    def unit_profit(self):
        """Unit profit in PHP: Selling Price - Current Purchase Price."""
        return self.selling_price - self.current_purchase_price

    @property
    def profit_margin_percentage(self):
        """
        Profit Margin % = ((Selling Price - Purchase Price) / Selling Price) * 100
        Returns Decimal rounded to 2 places.
        """
        if self.selling_price > 0:
            margin = ((self.selling_price - self.current_purchase_price) / self.selling_price) * Decimal('100')
            return round(margin, 2)
        return Decimal('0.00')

    @property
    def markup_percentage(self):
        """
        Markup % = ((Selling Price - Purchase Price) / Purchase Price) * 100
        """
        if self.current_purchase_price > 0:
            markup = ((self.selling_price - self.current_purchase_price) / self.current_purchase_price) * Decimal('100')
            return round(markup, 2)
        return Decimal('0.00')

    @property
    def is_low_margin(self):
        """Returns True if profit margin is below the user-defined threshold."""
        return self.profit_margin_percentage < self.margin_threshold

    @property
    def is_loss(self):
        """Returns True if selling price is less than purchase price (negative profit)."""
        return self.unit_profit < 0

    @property
    def margin_shortfall(self):
        """Amount by which the margin falls below the threshold."""
        if self.is_low_margin:
            return round(self.margin_threshold - self.profit_margin_percentage, 2)
        return Decimal('0.00')

    @property
    def suggested_selling_price(self):
        """
        Calculates the recommended retail selling price to achieve the desired margin threshold:
        Suggested Price = Current Purchase Price / (1 - (margin_threshold / 100))
        Rounded UP to the nearest cent to guarantee that the restored margin meets or exceeds the threshold.
        """
        if self.margin_threshold < Decimal('100.00') and self.current_purchase_price > 0:
            rate = Decimal('1.00') - (self.margin_threshold / Decimal('100.00'))
            if rate > 0:
                raw_suggested = self.current_purchase_price / rate
                return raw_suggested.quantize(Decimal('0.01'), rounding=ROUND_UP)
        return self.selling_price

    @property
    def price_trend(self):
        """Returns 'up', 'down', 'same', or 'none' indicating cost shift trend."""
        if self.previous_purchase_price is None:
            return 'none'
        if self.price_change_amount > 0:
            return 'up'
        elif self.price_change_amount < 0:
            return 'down'
        return 'same'

    @property
    def total_units_purchased(self):
        """Total quantity of units or packs recorded across all purchase records."""
        total = sum(r.quantity for r in self.price_records.all())
        return total if total > 0 else self.price_records.count()

    @property
    def total_purchase_spend(self):
        """Total cost spent across all purchase records."""
        records = list(self.price_records.all())
        if not records:
            return Decimal('0.00')
        return sum(r.purchase_price * Decimal(r.quantity) for r in records)

    @property
    def average_purchase_price(self):
        """
        Calculates the weighted average purchasing cost:
        Average Cost = Sum(Price * Quantity) / Sum(Quantity).
        """
        records = list(self.price_records.all())
        if not records:
            return self.current_purchase_price or Decimal('0.00')
        total_qty = sum(r.quantity for r in records)
        if total_qty > 0:
            total_spend = sum(r.purchase_price * Decimal(r.quantity) for r in records)
            avg = total_spend / Decimal(total_qty)
            return round(avg, 2)
        return self.current_purchase_price

    @property
    def supplier_comparison(self):
        """
        Compares latest purchasing prices across different suppliers for this product.
        Identifies the supplier with the LOWEST price, calculates cost differences,
        and evaluates profit margins per supplier.
        """
        records = list(self.price_records.order_by('-effective_date', '-created_at', '-id'))
        if not records:
            return []

        supplier_map = {}
        for r in records:
            s_name = (r.supplier or "").strip() or "Standard Wholesaler"
            key = s_name.lower()
            if key not in supplier_map:
                supplier_map[key] = {
                    'name': s_name,
                    'latest_price': r.purchase_price,
                    'latest_date': r.effective_date,
                    'latest_record': r,
                    'records': [r],
                }
            else:
                supplier_map[key]['records'].append(r)

        if not supplier_map:
            return []

        min_price = min(item['latest_price'] for item in supplier_map.values())
        max_price = max(item['latest_price'] for item in supplier_map.values())

        comparison_list = []
        for item in supplier_map.values():
            is_lowest = (item['latest_price'] == min_price)
            diff = item['latest_price'] - min_price
            if self.selling_price > 0:
                margin = ((self.selling_price - item['latest_price']) / self.selling_price) * Decimal('100')
                margin = round(margin, 2)
            else:
                margin = Decimal('0.00')

            comparison_list.append({
                'name': item['name'],
                'latest_price': item['latest_price'],
                'latest_date': item['latest_date'],
                'is_lowest': is_lowest,
                'difference_from_lowest': diff,
                'margin_at_cost': margin,
                'record_count': len(item['records']),
                'total_purchased': sum(rec.quantity for rec in item['records']),
            })

        # Sort so the lowest priced supplier appears first
        comparison_list.sort(key=lambda x: (not x['is_lowest'], x['latest_price']))
        return comparison_list

    @property
    def lowest_supplier(self):
        """Returns the supplier info dict that offers the lowest purchasing price."""
        comp = self.supplier_comparison
        return comp[0] if comp else None

    @property
    def supplier_savings_per_unit(self):
        """Potential savings per unit between most expensive and cheapest supplier."""
        comp = self.supplier_comparison
        if len(comp) > 1:
            prices = [item['latest_price'] for item in comp]
            return max(prices) - min(prices)
        return Decimal('0.00')


class PriceRecord(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='price_records',
        verbose_name="Product"
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_prices',
        verbose_name="Recorded By"
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Purchasing Price / Cost (₱)",
        help_text="Purchasing price per unit from supplier"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Quantity / Packs Purchased",
        help_text="Number of units/packs purchased at this cost"
    )
    effective_date = models.DateField(
        default=timezone.now,
        verbose_name="Effective Date",
        help_text="Date when this purchasing price became effective"
    )
    supplier = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Supplier / Wholesaler",
        help_text="e.g. Puregold, Ultra Mega, Local Distributor"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Batch info, reason for price shift, or package size"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_date', '-created_at', '-id']
        verbose_name = "Price Record"
        verbose_name_plural = "Price Records"

    def __str__(self):
        return f"{self.product.name} - ₱{self.purchase_price} ({self.effective_date})"

    @property
    def previous_record(self):
        """Finds the price record recorded immediately prior to this one for the same product."""
        return PriceRecord.objects.filter(
            product=self.product
        ).filter(
            models.Q(effective_date__lt=self.effective_date) |
            models.Q(effective_date=self.effective_date, created_at__lt=self.created_at) |
            models.Q(effective_date=self.effective_date, created_at=self.created_at, id__lt=self.id)
        ).order_by('-effective_date', '-created_at', '-id').first()

    @property
    def price_difference(self):
        prev = self.previous_record
        if prev:
            return self.purchase_price - prev.purchase_price
        return Decimal('0.00')

    @property
    def percentage_change(self):
        prev = self.previous_record
        if prev and prev.purchase_price > 0:
            diff = ((self.purchase_price - prev.purchase_price) / prev.purchase_price) * Decimal('100')
            return round(diff, 2)
        return Decimal('0.00')

    @property
    def profit_margin_at_recording(self):
        if self.product.selling_price > 0:
            margin = ((self.product.selling_price - self.purchase_price) / self.product.selling_price) * Decimal('100')
            return round(margin, 2)
        return Decimal('0.00')
