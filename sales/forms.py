from django import forms
from django.db import models
from .models import Credit, Return
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
    

class EditCreditForm(forms.ModelForm):
    # item = forms.CharField(label="Item", max_length=255, required=True)
    class Meta:
        model = Credit
        fields = [
            'item',
            'quantity',
            'customer_name',
            'customer_phone_number',
            'paid',
        ]


class ReturnForm(forms.ModelForm):
    """Form for processing product returns"""
    class Meta:
        model = Return
        fields = ['item', 'quantity_returned', 'reason', 'refund_amount', 'refunded']

    def __init__(self, *args, **kwargs):
        self.sale = kwargs.pop('sale', None)
        super().__init__(*args, **kwargs)
        
        if self.sale:
            # Only show items from this sale
            sale_items = self.sale.saleitem_set.all()
            item_ids = [si.item.id for si in sale_items]
            self.fields['item'].queryset = Item.objects.filter(id__in=item_ids)

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        quantity = cleaned_data.get('quantity_returned')
        
        if item and quantity:
            # Check how many of this item were sold in this sale
            sale_item = self.sale.saleitem_set.filter(item=item).first()
            if sale_item:
                # Check how many have already been returned
                already_returned = self.sale.returns.filter(item=item).aggregate(
                    total=models.Sum('quantity_returned')
                )['total'] or 0
                
                max_returnable = sale_item.quantity_sold - already_returned
                
                if quantity > max_returnable:
                    raise forms.ValidationError(
                        f"You can only return up to {max_returnable} of '{item.name}'. "
                        f"You bought {sale_item.quantity_sold} in this sale, "
                        f"and {already_returned} has already been returned."
                    )
        
        return cleaned_data