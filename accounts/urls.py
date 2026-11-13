from django.urls import path
from .views import PesoTrackLoginView, ProfileUpdateView, SignUpView

urlpatterns = [
    path("login/", PesoTrackLoginView.as_view(), name="login"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
]