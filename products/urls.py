from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    PriceRecordCreateView,
    PriceRecordUpdateView,
    PriceRecordDeleteView,
    PriceHistoryListView,
    ApplySuggestedPriceView,
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('add/', ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('<int:pk>/apply-suggested/', ApplySuggestedPriceView.as_view(), name='apply_suggested_price'),
    path('<int:product_id>/record-price/', PriceRecordCreateView.as_view(), name='product_price_record_create'),
    path('record-price/', PriceRecordCreateView.as_view(), name='price_record_create'),
    path('price-records/<int:pk>/edit/', PriceRecordUpdateView.as_view(), name='price_record_update'),
    path('price-records/<int:pk>/delete/', PriceRecordDeleteView.as_view(), name='price_record_delete'),
    path('price-history/', PriceHistoryListView.as_view(), name='price_history'),
]
