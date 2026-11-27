from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        RESELLER = 'RESELLER', 'Small Reseller'

    role = models.CharField(
        max_length=20, 
        choices=Role.choices,
        default=Role.RESELLER
    )
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    business_name = models.CharField(max_length=100, blank=True, null=True)

    def clean(self):
        super().clean()
        # Enforce that only one Administrator account can exist in the system
        if self.role == self.Role.ADMIN:
            existing_admin = CustomUser.objects.filter(role=self.Role.ADMIN)
            if self.pk:
                existing_admin = existing_admin.exclude(pk=self.pk)
            if existing_admin.exists():
                raise ValidationError("Only one Administrator account can be registered in the system.")

    def save(self, *args, **kwargs):
        # Automatically connect the Administrator role into the Django admin panel
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
