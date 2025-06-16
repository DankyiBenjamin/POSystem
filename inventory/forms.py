from django import forms
from .models import Item, Restock


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'price', 'quantity','part_number',
                  'description', 'shop', 'low_stock_threshold']


class RestockForm(forms.ModelForm):
    class Meta:
        model = Restock
        fields = ['item', 'quantity_added']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if request:
            user = request.user
            shop = user.shop if user.role != 'admin' else request.session.get('selected_shop_id')
            if shop:
                self.fields['item'].queryset = Item.objects.filter(shop_id=shop)
            else:
                self.fields['item'].queryset = Item.objects.none()