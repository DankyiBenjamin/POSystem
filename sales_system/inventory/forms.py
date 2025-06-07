from django import forms
from .models import Item, Restock


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'price', 'quantity',
                  'description', 'shop', 'low_stock_threshold']


class RestockForm(forms.ModelForm):
    class Meta:
        model = Restock
        fields = ['item', 'quantity_added']
