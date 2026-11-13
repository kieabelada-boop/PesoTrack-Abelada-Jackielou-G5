from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from .forms import (CustomUserCreationForm, PesoTrackAuthenticationForm,
                    ProfileForm)
from .models import CustomUser


class PesoTrackLoginView(LoginView):
    authentication_form = PesoTrackAuthenticationForm
    template_name = "registration/login.html"  # Make sure your template path matches your project


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")
    success_message = "Your account has been created. You can now log in."


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileForm
    template_name = "registration/profile.html"
    success_url = reverse_lazy("dashboard")

    def get_object(self, queryset=None):
        return self.request.user