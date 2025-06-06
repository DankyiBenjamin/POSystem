from django import forms
from .models import Credit
from inventory.models import Item
from django.contrib.auth import get_user_model


# user
User = get_user_model()


class SaleForm(forms.Form):
    # Form for creating a sale
    item = forms.ModelChoiceField(queryset=Item.objects.all())
    quantity = forms.IntegerField(min_value=1)
    customer_name = forms.CharField(required=False)
    customer_phone_number = forms.CharField(required=False)


class CreditForm(forms.ModelForm):
    # Form for creating a credit
    class Meta:
        model = Credit
        fields = ['item', 'quantity', 'customer_name', 'customer_phone_number']
