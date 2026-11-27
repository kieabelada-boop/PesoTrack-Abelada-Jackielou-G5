from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import Product, PriceRecord


def add_bootstrap_classes(form):
    for name, field in form.fields.items():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs['class'] = 'form-check-input'
        else:
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} form-control'.strip()


class ProductCreateForm(forms.ModelForm):
    initial_purchase_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label="Initial Purchasing Price / Cost (₱)",
        help_text="Cost per unit paid to your supplier / wholesaler"
    )
    quantity = forms.IntegerField(
        initial=1,
        min_value=1,
        required=False,
        label="Quantity / Packs Purchased",
        help_text="Number of units or packs purchased in this batch"
    )
    supplier = forms.CharField(
        max_length=150,
        required=False,
        label="Supplier / Wholesaler",
        help_text="e.g. Gaisano, Puregold, Direct Distributor, Public Market"
    )
    effective_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Purchase / Effective Date"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label="Initial Price Notes",
        help_text="Batch details or pricing notes"
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'unit',
            'selling_price',
            'margin_threshold',
            'sku',
            'description',
        ]
        help_texts = {
            'selling_price': "Retail price you sell to your customers in PHP",
            'margin_threshold': "Alert you when profit margin falls below this % (default: 15%)",
            'unit': "e.g. piece, pack, bottle, can, sachet, box, kg",
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user or kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not self.initial.get('effective_date'):
            today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
            self.fields['effective_date'].initial = today
        add_bootstrap_classes(self)

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("Product name must be at least 2 characters long.")
        if self.user and Product.objects.filter(user=self.user, name__iexact=name).exists():
            raise forms.ValidationError(f"You already have a product named '{name}' in your store inventory.")
        return name

    def clean_unit(self):
        unit = self.cleaned_data.get('unit', '').strip()
        if not unit:
            return 'piece'
        return unit

    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        if price is not None and price <= Decimal('0.00'):
            raise forms.ValidationError("Selling price must be greater than ₱0.00.")
        return price

    def clean_margin_threshold(self):
        threshold = self.cleaned_data.get('margin_threshold')
        if threshold is not None and (threshold < Decimal('0.00') or threshold > Decimal('100.00')):
            raise forms.ValidationError("Margin threshold must be between 0% and 100%.")
        return threshold

    def clean_initial_purchase_price(self):
        cost = self.cleaned_data.get('initial_purchase_price')
        if cost is not None and cost <= Decimal('0.00'):
            raise forms.ValidationError("Purchasing price must be greater than ₱0.00.")
        return cost

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if not qty or qty < 1:
            return 1
        return qty

    def clean_effective_date(self):
        dt = self.cleaned_data.get('effective_date')
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
        if dt and dt > today:
            raise forms.ValidationError("Purchase date cannot be in the future.")
        return dt

    def clean_supplier(self):
        return (self.cleaned_data.get('supplier') or '').strip()


class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'unit',
            'selling_price',
            'margin_threshold',
            'sku',
            'description',
        ]
        help_texts = {
            'selling_price': "Retail price you sell to your customers in PHP",
            'margin_threshold': "Alert you when profit margin falls below this %",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("Product name must be at least 2 characters long.")
        if self.instance and self.instance.user:
            qs = Product.objects.filter(user=self.instance.user, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f"Another product named '{name}' already exists in your store inventory.")
        return name

    def clean_unit(self):
        unit = self.cleaned_data.get('unit', '').strip()
        if not unit:
            return 'piece'
        return unit

    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        if price is not None and price <= Decimal('0.00'):
            raise forms.ValidationError("Selling price must be greater than ₱0.00.")
        return price

    def clean_margin_threshold(self):
        threshold = self.cleaned_data.get('margin_threshold')
        if threshold is not None and (threshold < Decimal('0.00') or threshold > Decimal('100.00')):
            raise forms.ValidationError("Margin threshold must be between 0% and 100%.")
        return threshold


class PriceRecordForm(forms.ModelForm):
    class Meta:
        model = PriceRecord
        fields = ['purchase_price', 'quantity', 'effective_date', 'supplier', 'notes']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'purchase_price': "New Purchasing Price / Cost (₱)",
            'quantity': "Quantity / Units Purchased",
            'effective_date': "Purchase Date",
            'supplier': "Supplier / Wholesaler",
            'notes': "Reason for Change / Notes",
        }
        help_texts = {
            'purchase_price': "Latest cost per unit from this supplier",
            'quantity': "Number of packs or items purchased",
            'supplier': "e.g. Gaisano, Puregold, Ultra Mega, Public Market",
            'notes': "e.g., Supplier price increase, Promo ended, Restock batch",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('effective_date'):
            today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
            self.fields['effective_date'].initial = today
        if not self.initial.get('quantity'):
            self.fields['quantity'].initial = 1
        self.fields['quantity'].required = False
        add_bootstrap_classes(self)

    def clean_purchase_price(self):
        price = self.cleaned_data.get('purchase_price')
        if price is not None and price <= Decimal('0.00'):
            raise forms.ValidationError("Purchasing price must be greater than ₱0.00.")
        return price

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if not qty or qty < 1:
            return 1
        return qty

    def clean_effective_date(self):
        dt = self.cleaned_data.get('effective_date')
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
        if dt and dt > today:
            raise forms.ValidationError("Purchase date cannot be in the future.")
        return dt

    def clean_supplier(self):
        return (self.cleaned_data.get('supplier') or '').strip()


class StandalonePriceRecordForm(forms.ModelForm):
    """Used when recording a price record where product must be selected from user's products."""
    class Meta:
        model = PriceRecord
        fields = ['product', 'purchase_price', 'quantity', 'effective_date', 'supplier', 'notes']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'product': "Product",
            'purchase_price': "New Purchasing Price / Cost (₱)",
            'quantity': "Quantity Purchased",
            'effective_date': "Purchase Date",
            'supplier': "Supplier / Wholesaler",
            'notes': "Reason for Change / Notes",
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(user=user).order_by('name')
        if not self.initial.get('effective_date'):
            today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
            self.fields['effective_date'].initial = today
        if not self.initial.get('quantity'):
            self.fields['quantity'].initial = 1
        self.fields['quantity'].required = False
        add_bootstrap_classes(self)

    def clean_purchase_price(self):
        price = self.cleaned_data.get('purchase_price')
        if price is not None and price <= Decimal('0.00'):
            raise forms.ValidationError("Purchasing price must be greater than ₱0.00.")
        return price

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if not qty or qty < 1:
            return 1
        return qty

    def clean_effective_date(self):
        dt = self.cleaned_data.get('effective_date')
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
        if dt and dt > today:
            raise forms.ValidationError("Purchase date cannot be in the future.")
        return dt

    def clean_supplier(self):
        return (self.cleaned_data.get('supplier') or '').strip()


class QuickAdjustPriceForm(forms.ModelForm):
    """Used for the 'Adjust price' action from the Product Overview modal/card."""
    class Meta:
        model = Product
        fields = ['selling_price']
        labels = {
            'selling_price': "New Retail Selling Price (₱)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)

    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        if price is not None and price <= Decimal('0.00'):
            raise forms.ValidationError("Selling price must be greater than ₱0.00.")
        return price
