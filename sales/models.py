# sales/models.py
from django.db import models
from django.conf import settings
from inventory.models import Item, Shop
from django.utils import timezone
from django.db import transaction

User = settings.AUTH_USER_MODEL


# what the shop purchases as supplies
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


# # This model is used to track the sequence of receipts for sales and credits
# It ensures that each sale and credit has a unique receipt code.
class ReceiptSequence(models.Model):
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE)
    last_sale_number = models.PositiveIntegerField(default=0)
    last_credit_number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"ReceiptSeqence for {self.shop.name}"

class Credit(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='credits')
    quantity = models.IntegerField()
    customer_name = models.CharField(max_length=255)
    customer_phone_number = models.CharField(max_length=15)
    credited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    credited_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)  # 👈 Add this
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)
    receipt_code = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Auto-generate receipt code
        if not self.receipt_code and self.shop:
            with transaction.atomic():
                sequence, _ = ReceiptSequence.objects.select_for_update().get_or_create(shop=self.shop)
                sequence.last_credit_number += 1
                sequence.save()

                year = timezone.now().year
                self.receipt_code = f"CR-SHOP{self.shop.id}-{year}-{sequence.last_credit_number:04d}"


        # Auto-set paid_at when marking as paid
        if self.paid and self.paid_at is None:
            self.paid_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} credited to {self.customer_name}"



class Sale(models.Model):
    items_sold = models.ManyToManyField(
        Item, through='SaleItem', related_name='sales')
    total_sales = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    closed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    closed_at = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)

    customer_phone_number = models.CharField(
        max_length=20, null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)
    receipt_code = models.CharField(
        max_length=100, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_code and self.shop:
            with transaction.atomic():
                sequence, _ = ReceiptSequence.objects.select_for_update().get_or_create(shop=self.shop)
                sequence.last_sale_number += 1
                sequence.save()

                year = timezone.now().year
                self.receipt_code = f"SL-SHOP{self.shop.id}-{year}-{sequence.last_sale_number:04d}"
        super().save(*args, **kwargs)


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


# before pushing to production, make sure to run migrations to the production database
# change the database settings in settings.py to point to the production database