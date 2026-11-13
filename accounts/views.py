from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from .forms import (CustomUserCreationForm, PesoTrackAuthenticationForm,
                    ProfileForm)
from .models import CustomUser


class PesoTrackLoginView(LoginView):
    authentication_form = PesoTrackAuthenticationForm
    template_name = "registration/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'ADMIN':
            return reverse_lazy('admin_dashboard')
        return reverse_lazy('reseller_dashboard')


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


@login_required
def admin_dashboard(request):
    if request.user.role != CustomUser.Role.ADMIN:
        return redirect('reseller_dashboard') 
    return render(request, 'accounts/admin_dashboard.html')

@login_required
def reseller_dashboard(request):
    if request.user.role != CustomUser.Role.RESELLER:
        return redirect('admin_dashboard')  
    return render(request, 'accounts/reseller_dashboard.html')