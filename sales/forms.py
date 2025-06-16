from django import forms
from .models import Credit
from inventory.models import Item
from django.contrib.auth import get_user_model


# user
User = get_user_model()

# only showing items based on user role and selected shop
class SaleForm(forms.Form):
    item_name = forms.CharField(label="Item", max_length=255)
    quantity = forms.IntegerField(min_value=1)
    customer_name = forms.CharField(max_length=255)
    customer_phone_number = forms.CharField(max_length=15)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.items_qs = Item.objects.none()
        if request:
            user = request.user
            if user.role == 'admin':
                selected_shop_id = request.session.get('selected_shop_id')
                if selected_shop_id:
                    self.items_qs = Item.objects.filter(shop_id=selected_shop_id)
            else:
                self.items_qs = Item.objects.filter(shop=user.shop)

        self.fields['item_name'].widget.attrs.update({
            'list': 'item-list',
            'autocomplete': 'off'
        })

    def clean_item_name(self):
        name = self.cleaned_data['item_name']
        try:
            return self.items_qs.get(name__iexact=name)
        except Item.DoesNotExist:
            raise forms.ValidationError("Item not found in this shop.")


class CreditForm(forms.ModelForm):
    item_name = forms.CharField(label="Item", max_length=255, required=True)

    class Meta:
        model = Credit
        fields = ['item_name', 'quantity', 'customer_name', 'customer_phone_number']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            user = self.request.user
            shop = user.shop if user.role != 'admin' else self.request.session.get('selected_shop_id')
            if shop:
                self.items_qs = Item.objects.filter(shop_id=shop)
                # prepare datalist options
                self.fields['item_name'].widget.attrs.update({
                    'list': 'item-list',
                    'autocomplete': 'off'
                })

    def clean_item_name(self):
        name = self.cleaned_data['item_name']
        try:
            return self.items_qs.get(name__iexact=name)
        except Item.DoesNotExist:
            raise forms.ValidationError("Item not found in this shop.")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.item = self.cleaned_data['item_name']
        if commit:
            obj.save()
        return obj