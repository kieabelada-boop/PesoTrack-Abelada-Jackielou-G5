"""
URL configuration for pesotrack project.
"""
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include


def custom_page_not_found(request, exception=None):
    return render(request, "404.html", status=404)


def custom_server_error(request):
    return render(request, "500.html", status=500)


handler404 = custom_page_not_found
handler500 = custom_server_error

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("products/", include("products.urls")),
    path("", include("dashboard.urls")),
]
