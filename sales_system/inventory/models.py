# inventory/models.py
from django.db import models
from django.conf import settings
from accounts.models import Shop

User = settings.AUTH_USER_MODEL


class Item(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    total_stock_added = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)

    def is_low_stock(self):
        return self.total_stock_added > 0 and self.quantity < 0.2 * self.total_stock_added

    def __str__(self):
        return self.name


class Restock(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='restocks')
    quantity_added = models.IntegerField()
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity_added} added to {self.item.name}"
