from django.contrib.auth.models import AbstractUser
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

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"