from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class Shop(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    Role_CHOICES = (
        ('admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Staff', 'Staff'),
    )

    role = models.CharField(
        max_length=20, choices=Role_CHOICES, default='staff')
    shop = models.ForeignKey(
        Shop, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
