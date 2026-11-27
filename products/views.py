from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from .forms import (
    ProductCreateForm, ProductUpdateForm,
    PriceRecordForm, StandalonePriceRecordForm,
    QuickAdjustPriceForm
)
from .models import Product, PriceRecord


class ResellerRequiredMixin:
    """Ensures that product operations are restricted to small reseller accounts."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        if request.user.role == 'ADMIN' and not request.user.is_superuser:
            messages.info(request, "Product inventory features are exclusive to small reseller accounts.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)


class ProductListView(LoginRequiredMixin, ResellerRequiredMixin, ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        # Users strictly see only their own products
        qs = Product.objects.filter(user=self.request.user)

        # Search filter
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query) |
                Q(category__icontains=query) |
                Q(description__icontains=query)
            )

        # Category filter
        category = self.request.GET.get('category', '').strip()
        if category:
            qs = qs.filter(category=category)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_user_products = list(self.get_queryset())
        
        # Calculate summary statistics across retrieved products
        total_products = len(all_user_products)
        low_margin_products = [p for p in all_user_products if p.is_low_margin]
        loss_products = [p for p in all_user_products if p.is_loss]
        healthy_products = [p for p in all_user_products if not p.is_low_margin]
        
        if total_products > 0:
            avg_margin = sum(p.profit_margin_percentage for p in all_user_products) / Decimal(total_products)
        else:
            avg_margin = Decimal('0.00')

        # Status filtering for the view
        status_filter = self.request.GET.get('status', 'all')
        if status_filter == 'alerts':
            display_products = low_margin_products
        elif status_filter == 'losses':
            display_products = loss_products
        elif status_filter == 'healthy':
            display_products = healthy_products
        else:
            display_products = all_user_products

        context['products'] = display_products
        context['total_products'] = total_products
        context['low_margin_count'] = len(low_margin_products)
        context['loss_count'] = len(loss_products)
        context['healthy_count'] = len(healthy_products)
        context['avg_margin'] = round(avg_margin, 2)
        context['selected_status'] = status_filter
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['categories'] = Product.Category.choices
        return context


class ProductDetailView(LoginRequiredMixin, ResellerRequiredMixin, DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        # Strict user isolation: 404 raised if accessing another user's product
        return Product.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        # Retrieve all price records ordered chronologically descending
        price_records = list(product.price_records.select_related('recorded_by').all())
        context['price_records'] = price_records
        context['total_records'] = len(price_records)
        context['suggested_price'] = product.suggested_selling_price
        context['supplier_comparison'] = product.supplier_comparison
        context['lowest_supplier'] = product.lowest_supplier
        context['savings_per_unit'] = product.supplier_savings_per_unit
        context['purchase_form'] = PriceRecordForm()
        context['adjust_price_form'] = QuickAdjustPriceForm(instance=product)
        return context


class ProductCreateView(LoginRequiredMixin, ResellerRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    template_name = "products/product_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        product = form.save()

        # Create the initial PriceRecord atomically from form's extra fields
        initial_cost = form.cleaned_data['initial_purchase_price']
        quantity = form.cleaned_data.get('quantity', 1)
        effective_date = form.cleaned_data.get('effective_date')
        supplier = form.cleaned_data.get('supplier', '')
        notes = form.cleaned_data.get('notes', '')

        PriceRecord.objects.create(
            product=product,
            recorded_by=self.request.user,
            purchase_price=initial_cost,
            quantity=quantity,
            effective_date=effective_date,
            supplier=supplier,
            notes=notes or "Initial purchase price recorded at product creation."
        )

        margin = product.profit_margin_percentage
        messages.success(
            self.request,
            f"Product '{product.name}' was successfully added! Initial Cost: ₱{initial_cost:.2f}, "
            f"Retail Selling Price: ₱{product.selling_price:.2f}, Profit Margin: {margin:.2f}%."
        )

        if product.is_loss:
            messages.error(
                self.request,
                f"⚠️ CRITICAL ALERT: '{product.name}' is selling at a loss of ₱{abs(product.unit_profit):.2f}! "
                f"Suggested selling price to achieve {product.margin_threshold:.2f}% margin is ₱{product.suggested_selling_price:.2f}."
            )
        elif product.is_low_margin:
            messages.warning(
                self.request,
                f"⚠️ LOW MARGIN ALERT: Profit margin ({margin:.2f}%) is below your threshold ({product.margin_threshold:.2f}%). "
                f"Suggested selling price: ₱{product.suggested_selling_price:.2f}."
            )

        return redirect(reverse('product_detail', kwargs={'pk': product.pk}))


class ProductUpdateView(LoginRequiredMixin, ResellerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    template_name = "products/product_form.html"

    def get_queryset(self):
        # Strict user isolation: 404 raised if accessing another user's product
        return Product.objects.filter(user=self.request.user)

    @transaction.atomic
    def form_valid(self, form):
        product = form.save()
        margin = product.profit_margin_percentage
        messages.success(
            self.request,
            f"Product '{product.name}' updated successfully! Current Profit Margin: {margin:.2f}%."
        )

        if product.is_loss:
            messages.error(
                self.request,
                f"⚠️ CRITICAL ALERT: Product is selling at a loss! Suggested selling price is ₱{product.suggested_selling_price:.2f}."
            )
        elif product.is_low_margin:
            messages.warning(
                self.request,
                f"⚠️ LOW MARGIN ALERT: Profit margin ({margin:.2f}%) is below your {product.margin_threshold:.2f}% threshold."
            )

        return redirect(reverse('product_detail', kwargs={'pk': product.pk}))


class ProductDeleteView(LoginRequiredMixin, ResellerRequiredMixin, DeleteView):
    model = Product
    template_name = "products/product_confirm_delete.html"
    success_url = reverse_lazy('product_list')

    def get_queryset(self):
        # Strict user isolation: 404 raised if attempting to delete another user's product
        return Product.objects.filter(user=self.request.user)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        product = self.get_object()
        name = product.name
        response = super().post(request, *args, **kwargs)
        messages.success(request, f"Product '{name}' and its price records were successfully deleted.")
        return response


class PriceRecordCreateView(LoginRequiredMixin, ResellerRequiredMixin, View):
    template_name = "products/price_record_form.html"

    def get(self, request, product_id=None):
        if product_id:
            product = get_object_or_404(Product, pk=product_id, user=request.user)
            form = PriceRecordForm()
            return render(request, self.template_name, {'form': form, 'product': product})
        else:
            form = StandalonePriceRecordForm(user=request.user)
            return render(request, self.template_name, {'form': form, 'product': None})

    def post(self, request, product_id=None):
        if product_id:
            product = get_object_or_404(Product, pk=product_id, user=request.user)
            form = PriceRecordForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    record = form.save(commit=False)
                    record.product = product
                    record.recorded_by = request.user
                    return self._process_saved_record(request, product, record)
            return render(request, self.template_name, {'form': form, 'product': product})
        else:
            form = StandalonePriceRecordForm(request.user, request.POST)
            if form.is_valid():
                with transaction.atomic():
                    record = form.save(commit=False)
                    record.recorded_by = request.user
                    product = record.product
                    # Ensure the selected product is actually owned by the current user
                    if product.user != request.user:
                        raise PermissionDenied("You do not have permission to log prices for this product.")
                    return self._process_saved_record(request, product, record)
            return render(request, self.template_name, {'form': form, 'product': None})

    def _process_saved_record(self, request, product, record):
        old_cost = product.current_purchase_price
        record.save()
        new_cost = record.purchase_price
        diff = new_cost - old_cost

        # Calculate percentage difference if old_cost exists
        if old_cost > 0:
            pct_change = (diff / old_cost) * Decimal('100')
        else:
            pct_change = Decimal('0.00')

        margin = product.profit_margin_percentage

        # Feedback messaging based on cost shift
        if old_cost > 0 and diff > 0:
            messages.warning(
                request,
                f"📈 Supplier Price Hike Logged! Purchasing cost increased from ₱{old_cost:.2f} to ₱{new_cost:.2f} "
                f"(+₱{diff:.2f}, +{pct_change:.1f}%). Profit margin narrowed to {margin:.2f}%."
            )
        elif old_cost > 0 and diff < 0:
            messages.success(
                request,
                f"📉 Price Drop Logged! Purchasing cost decreased from ₱{old_cost:.2f} to ₱{new_cost:.2f} "
                f"(-₱{abs(diff):.2f}, {pct_change:.1f}%). Profit margin widened to {margin:.2f}%."
            )
        else:
            messages.success(
                request,
                f"Purchasing price of ₱{new_cost:.2f} recorded for '{product.name}'."
            )

        # Check margin alert status
        if product.is_loss:
            messages.error(
                request,
                f"🚨 CRITICAL ALERT: '{product.name}' is now selling at a loss of ₱{abs(product.unit_profit):.2f}! "
                f"Suggested retail price to maintain {product.margin_threshold:.2f}% margin is ₱{product.suggested_selling_price:.2f}."
            )
        elif product.is_low_margin:
            messages.warning(
                request,
                f"⚠️ LOW MARGIN ALERT: Margin ({margin:.2f}%) fell below your threshold of {product.margin_threshold:.2f}%. "
                f"Suggested retail price: ₱{product.suggested_selling_price:.2f}."
            )

        return redirect(reverse('product_detail', kwargs={'pk': product.pk}))


class PriceRecordUpdateView(LoginRequiredMixin, ResellerRequiredMixin, UpdateView):
    model = PriceRecord
    form_class = PriceRecordForm
    template_name = "products/price_record_form.html"

    def get_queryset(self):
        # Strict user isolation
        return PriceRecord.objects.filter(product__user=self.request.user).select_related('product')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        context['is_edit'] = True
        return context

    @transaction.atomic
    def form_valid(self, form):
        record = form.save()
        messages.success(self.request, f"Price record for '{record.product.name}' updated successfully.")
        return redirect(reverse('product_detail', kwargs={'pk': record.product.pk}))


class PriceRecordDeleteView(LoginRequiredMixin, ResellerRequiredMixin, DeleteView):
    model = PriceRecord
    template_name = "products/price_record_confirm_delete.html"

    def get_queryset(self):
        # Strict user isolation
        return PriceRecord.objects.filter(product__user=self.request.user).select_related('product')

    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.product.pk})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        record = self.get_object()
        product = record.product
        response = super().post(request, *args, **kwargs)
        messages.success(request, f"Price record (₱{record.purchase_price:.2f}) deleted for '{product.name}'.")
        return response


class PriceHistoryListView(LoginRequiredMixin, ResellerRequiredMixin, ListView):
    model = PriceRecord
    template_name = "products/price_history.html"
    context_object_name = "price_records"

    def get_queryset(self):
        qs = PriceRecord.objects.filter(product__user=self.request.user).select_related('product', 'recorded_by')

        product_id = self.request.GET.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)

        supplier = self.request.GET.get('supplier')
        if supplier:
            qs = qs.filter(supplier__icontains=supplier)

        return qs.order_by('-effective_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_products'] = Product.objects.filter(user=self.request.user).order_by('name')
        context['selected_product'] = self.request.GET.get('product', '')
        return context


class ApplySuggestedPriceView(LoginRequiredMixin, ResellerRequiredMixin, View):
    """Allows one-click price adjustment to restore margin threshold."""
    @transaction.atomic
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk, user=request.user)
        suggested = product.suggested_selling_price
        old_selling = product.selling_price
        product.selling_price = suggested
        product.save()

        messages.success(
            request,
            f"✅ Retail selling price for '{product.name}' adjusted from ₱{old_selling:.2f} to ₱{suggested:.2f}. "
            f"Profit margin successfully restored to {product.profit_margin_percentage:.2f}%!"
        )
        return redirect(request.META.get('HTTP_REFERER', reverse('product_detail', kwargs={'pk': product.pk})))


class AdjustSellingPriceView(LoginRequiredMixin, ResellerRequiredMixin, View):
    """Adjust retail selling price directly from Product Overview page."""
    @transaction.atomic
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk, user=request.user)
        form = QuickAdjustPriceForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(
                request,
                f"Retail selling price for '{product.name}' adjusted to ₱{product.selling_price:.2f}. "
                f"Current profit margin: {product.profit_margin_percentage:.2f}%."
            )
        else:
            messages.error(request, "Invalid selling price entered. Please enter a valid amount greater than ₱0.00.")
        return redirect(reverse('product_detail', kwargs={'pk': product.pk}))


class SupplierComparisonView(LoginRequiredMixin, ResellerRequiredMixin, ListView):
    """
    Catalog-wide feature comparing purchasing prices across different suppliers.
    Allows resellers to see where each product is cheapest and find bulk savings.
    """
    model = Product
    template_name = "products/compare_suppliers.html"
    context_object_name = "products"

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user).prefetch_related('price_records')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_prods = list(self.get_queryset())

        compared_products = []
        multi_supplier_count = 0
        total_potential_savings = Decimal('0.00')
        all_suppliers = set()

        for p in all_prods:
            comp = p.supplier_comparison
            if comp:
                for s in comp:
                    all_suppliers.add(s['name'])
                if len(comp) > 1:
                    multi_supplier_count += 1
                    total_potential_savings += p.supplier_savings_per_unit
                compared_products.append({
                    'product': p,
                    'comparison': comp,
                    'lowest': p.lowest_supplier,
                    'savings': p.supplier_savings_per_unit,
                    'has_multiple_suppliers': len(comp) > 1,
                })

        context['compared_products'] = compared_products
        context['all_suppliers'] = sorted(list(all_suppliers))
        context['multi_supplier_count'] = multi_supplier_count
        context['total_potential_savings'] = total_potential_savings
        return context
