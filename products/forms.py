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
    supplier = forms.CharField(
        max_length=150,
        required=False,
        label="Supplier / Wholesaler",
        help_text="e.g. Puregold, Direct Distributor, Local Public Market"
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['effective_date'].initial = timezone.now().date()
        add_bootstrap_classes(self)

    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Selling price must be greater than ₱0.00.")
        return price

    def clean_margin_threshold(self):
        threshold = self.cleaned_data.get('margin_threshold')
        if threshold is not None and (threshold < 0 or threshold > 100):
            raise forms.ValidationError("Margin threshold must be between 0% and 100%.")
        return threshold

    def clean_initial_purchase_price(self):
        cost = self.cleaned_data.get('initial_purchase_price')
        if cost is not None and cost <= 0:
            raise forms.ValidationError("Purchasing price must be greater than ₱0.00.")
        return cost


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

    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Selling price must be greater than ₱0.00.")
        return price

    def clean_margin_threshold(self):
        threshold = self.cleaned_data.get('margin_threshold')
        if threshold is not None and (threshold < 0 or threshold > 100):
            raise forms.ValidationError("Margin threshold must be between 0% and 100%.")
        return threshold


class PriceRecordForm(forms.ModelForm):
    class Meta:
        model = PriceRecord
        fields = ['purchase_price', 'effective_date', 'supplier', 'notes']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'purchase_price': "New Purchasing Price / Cost (₱)",
            'effective_date': "Effective Date",
            'supplier': "Supplier / Wholesaler",
            'notes': "Reason for Change / Notes",
        }
        help_texts = {
            'purchase_price': "Latest cost per unit from your supplier",
            'notes': "e.g., Supplier price increase, Delivery fee adjustment, Promo ended",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('effective_date'):
            self.fields['effective_date'].initial = timezone.now().date()
        add_bootstrap_classes(self)

    def clean_purchase_price(self):
        price = self.cleaned_data.get('purchase_price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Purchasing price must be greater than ₱0.00.")
        return price


class StandalonePriceRecordForm(forms.ModelForm):
    """Used when recording a price record where product must be selected from user's products."""
    class Meta:
        model = PriceRecord
        fields = ['product', 'purchase_price', 'effective_date', 'supplier', 'notes']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'product': "Product",
            'purchase_price': "New Purchasing Price / Cost (₱)",
            'effective_date': "Effective Date",
            'supplier': "Supplier / Wholesaler",
            'notes': "Reason for Change / Notes",
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(user=user).order_by('name')
        if not self.initial.get('effective_date'):
            self.fields['effective_date'].initial = timezone.now().date()
        add_bootstrap_classes(self)

    def clean_purchase_price(self):
        price = self.cleaned_data.get('purchase_price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Purchasing price must be greater than ₱0.00.")
        return price
