from django.contrib import admin
from .models import Product, PriceRecord


class PriceRecordInline(admin.TabularInline):
    model = PriceRecord
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user',
        'category',
        'unit',
        'selling_price',
        'current_purchase_price',
        'profit_margin_percentage',
        'margin_threshold',
        'is_low_margin',
        'created_at',
    )
    list_filter = ('category', 'margin_threshold', 'created_at')
    search_fields = ('name', 'sku', 'user__username', 'user__business_name')
    inlines = [PriceRecordInline]


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'purchase_price',
        'effective_date',
        'supplier',
        'recorded_by',
        'created_at',
    )
    list_filter = ('effective_date', 'supplier', 'created_at')
    search_fields = ('product__name', 'supplier', 'notes')
