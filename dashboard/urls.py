from django.urls import path
from .views import dashboard_home, reseller_dashboard, admin_dashboard

urlpatterns = [
    path("", dashboard_home, name="dashboard"),
    path("reseller-dashboard/", reseller_dashboard, name="reseller_dashboard"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin-panel/", admin_dashboard, name="admin_panel"),
]
