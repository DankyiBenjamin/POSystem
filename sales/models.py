# sales/models.py
from django.db import models
from django.conf import settings
from inventory.models import Item, Shop
from django.utils import timezone

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
            year = timezone.now().year
            count = Credit.objects.filter(shop=self.shop).count() + 1
            self.receipt_code = f"CR-SHOP{self.shop.id}-{year}-{count:04d}"

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
            year = timezone.now().year
            shop_id = self.shop.id
            count = Sale.objects.filter(shop=self.shop).count() + 1
            self.receipt_code = f"SL-SHOP{shop_id}-{year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def total_returns(self):
        """Calculate total refund amount for this sale"""
        return sum(r.refund_amount for r in self.returns.filter(refunded=True))

    @property
    def net_sales(self):
        """Calculate net sales after returns"""
        return self.total_sales - self.total_returns

    @property
    def has_returns(self):
        """Check if this sale has any returns"""
        return self.returns.exists()


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


class Return(models.Model):
    """Model for tracking product returns"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='returns')
    quantity_returned = models.IntegerField()
    reason = models.TextField(blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refunded = models.BooleanField(default=False)
    refunded_at = models.DateTimeField(null=True, blank=True)
    returned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    returned_at = models.DateTimeField(auto_now_add=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)
    receipt_code = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Auto-generate return receipt code
        if not self.receipt_code and self.shop:
            year = timezone.now().year
            count = Return.objects.filter(shop=self.shop).count() + 1
            self.receipt_code = f"RT-SHOP{self.shop.id}-{year}-{count:04d}"
        
        # Auto-set refunded_at when marking as refunded
        if self.refunded and self.refunded_at is None:
            self.refunded_at = timezone.now()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity_returned} of {self.item.name} returned from Sale {self.sale.receipt_code}"


class InterShopCredit(models.Model):
    """Model for tracking credits between shops"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('settled', 'Settled'),
        ('partial', 'Partial'),
    )
    
    from_shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name='credits_given')
    to_shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name='credits_received')
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='inter_shop_credits')
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    settled_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    receipt_code = models.CharField(
        max_length=100, unique=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = self.quantity * self.unit_price
        
        # Auto-generate receipt code
        if not self.receipt_code:
            year = timezone.now().year
            count = InterShopCredit.objects.count() + 1
            self.receipt_code = f"ISC-{year}-{count:04d}"
        
        # Auto-set settled_at when fully settled
        if self.status == 'settled' and self.settled_at is None:
            self.settled_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to be settled"""
        return self.total_amount - self.settled_amount
    
    @property
    def is_settled(self):
        """Check if fully settled"""
        return self.status == 'settled' or self.remaining_amount <= 0
    
    def __str__(self):
        return f"{self.quantity} {self.item.name} from {self.from_shop} to {self.to_shop}"


class InterShopSettlement(models.Model):
    """Model for tracking settlements between shops"""
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('transfer', 'Transfer'),
        ('item', 'Item'),
    )
    
    from_shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name='settlements_made')
    to_shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name='settlements_received')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    settled_credits = models.ManyToManyField(
        InterShopCredit, related_name='settlements', blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.amount} from {self.from_shop} to {self.to_shop}"
