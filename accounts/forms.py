from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser


def add_bootstrap_classes(form):
    for field in form.fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = "form-check-input"
        else:
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Required. A valid email address for notifications and recovery."
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "contact_number",
            "business_name",
            "role"
        )
        help_texts = {
            'role': "Select 'Small Reseller' for store owners, or 'Administrator'.",
            'business_name': "e.g. Aling Nena's Sari-Sari Store",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enforce that only one Admin can register: if one already exists, restrict to RESELLER
        if CustomUser.objects.filter(role=CustomUser.Role.ADMIN).exists():
            self.fields['role'].choices = [
                (CustomUser.Role.RESELLER, 'Small Reseller')
            ]
            self.fields['role'].initial = CustomUser.Role.RESELLER
            self.fields['role'].help_text = "Only 'Small Reseller' is available because an Administrator is already registered."
        add_bootstrap_classes(self)

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role == CustomUser.Role.ADMIN:
            existing_admin = CustomUser.objects.filter(role=CustomUser.Role.ADMIN)
            if self.instance and self.instance.pk:
                existing_admin = existing_admin.exclude(pk=self.instance.pk)
            if existing_admin.exists():
                raise forms.ValidationError(
                    "An Administrator account already exists. Only one Administrator is permitted to register."
                )
        return role

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "contact_number",
            "business_name"
        )
        help_texts = {
            'business_name': "Name of your retail store or reseller business.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        qs = CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Another account is already using this email address.")
        return email


class PesoTrackAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)
