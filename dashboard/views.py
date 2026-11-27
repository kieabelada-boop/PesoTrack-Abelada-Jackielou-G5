from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.models import CustomUser
from products.models import Product, PriceRecord


@login_required
def dashboard_home(request):
    """Entry point for / that routes users according to their assigned role."""
    if request.user.role == CustomUser.Role.ADMIN:
        return redirect('admin_dashboard')
    return redirect('reseller_dashboard')


@login_required
def reseller_dashboard(request):
    """
    Role-based dashboard for Small Resellers / Sari-sari Store Owners.
    Displays financial metrics, active margin alerts, price shift monitoring, and quick actions.
    """
    if request.user.role != CustomUser.Role.RESELLER and not request.user.is_superuser:
        messages.info(request, "Administrators are directed to the Administrator Dashboard.")
        return redirect('admin_dashboard')

    products = list(Product.objects.filter(user=request.user).prefetch_related('price_records'))
    total_products = len(products)
    low_margin_products = [p for p in products if p.is_low_margin]
    loss_products = [p for p in products if p.is_loss]
    healthy_products = [p for p in products if not p.is_low_margin]

    if total_products > 0:
        avg_margin = sum(p.profit_margin_percentage for p in products) / Decimal(total_products)
    else:
        avg_margin = Decimal('0.00')

    # Sort alerts by margin shortfall descending (most critical first)
    low_margin_alerts = sorted(low_margin_products, key=lambda p: (not p.is_loss, -p.margin_shortfall))

    recent_price_shifts = PriceRecord.objects.filter(
        product__user=request.user
    ).select_related('product', 'recorded_by').order_by('-effective_date', '-created_at')[:8]

    context = {
        'total_products': total_products,
        'low_margin_count': len(low_margin_products),
        'loss_count': len(loss_products),
        'healthy_count': len(healthy_products),
        'avg_margin': round(avg_margin, 2),
        'low_margin_alerts': low_margin_alerts,
        'recent_price_shifts': recent_price_shifts,
    }
    return render(request, 'dashboard/reseller_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """
    Role-based dashboard for Administrators.
    Restricted to ADMIN role. Non-admins cannot open this view by typing its URL.
    Monitors registered small resellers and store owners only.
    """
    if request.user.role != CustomUser.Role.ADMIN and not request.user.is_superuser:
        messages.error(request, "Access denied. Administrator privileges required to access this dashboard.")
        return redirect('reseller_dashboard')

    resellers = CustomUser.objects.filter(
        role=CustomUser.Role.RESELLER
    ).order_by('-date_joined')

    total_resellers = resellers.count()

    context = {
        'resellers': resellers,
        'total_resellers': total_resellers,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)
