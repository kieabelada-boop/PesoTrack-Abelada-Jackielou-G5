from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from .forms import (
    CustomUserCreationForm,
    PesoTrackAuthenticationForm,
    ProfileForm,
)
from .models import CustomUser


class PesoTrackLoginView(LoginView):
    authentication_form = PesoTrackAuthenticationForm
    template_name = "registration/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and user.role == CustomUser.Role.ADMIN:
            return reverse_lazy('admin_dashboard')
        return reverse_lazy('reseller_dashboard')


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")
    success_message = "Your account has been created successfully! You can now log in."


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CustomUser
    form_class = ProfileForm
    template_name = "registration/profile.html"
    success_url = reverse_lazy("profile")
    success_message = "Your profile information has been updated successfully."

    def get_object(self, queryset=None):
        return self.request.user
