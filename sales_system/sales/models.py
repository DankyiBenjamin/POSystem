# sales/models.py
from django.db import models
from django.conf import settings
from inventory.models import Item, Shop

User = settings.AUTH_USER_MODEL


class Purchase(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='purchases')
    quantity = models.IntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    customer_name = models.CharField(max_length=255)
    customer_phone_number = models.CharField(max_length=15)
    purchased_by = models.ForeignKey(User, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.quantity} of {self.item.name}"


class Credit(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='credits')
    quantity = models.IntegerField()
    customer_name = models.CharField(max_length=255)
    customer_phone_number = models.CharField(max_length=15)
    credited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    credited_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.quantity} credited to {self.customer_name}"


class Sale(models.Model):
    items_sold = models.ManyToManyField(
        Item, through='SaleItem', related_name='sales')
    total_sales = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    closed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    closed_at = models.DateTimeField(auto_now_add=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Sale closed by {self.closed_by} on {self.closed_at}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity_sold = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity_sold} of {self.item.name} in Sale {self.sale.id}"


class Log(models.Model):
    # This model is used to log actions performed by users
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action}"
