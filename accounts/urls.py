from django.urls import path
from .views import PesoTrackLoginView, SignUpView, ProfileUpdateView, admin_dashboard, reseller_dashboard

urlpatterns = [
    path('login/', PesoTrackLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/', ProfileUpdateView.as_view(), name='profile'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('reseller-dashboard/', reseller_dashboard, name='reseller_dashboard'),
]