from django import forms
from django.db import models
from .models import Credit, Return, InterShopCredit, InterShopSettlement
from inventory.models import Item
from accounts.models import Shop
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
            if (user.role or '').lower() == 'admin':
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
            shop = user.shop if (user.role or '').lower() != 'admin' else self.request.session.get('selected_shop_id')
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


class InterShopCreditForm(forms.ModelForm):
    """Form for creating inter-shop credits"""
    class Meta:
        model = InterShopCredit
        fields = ['from_shop', 'to_shop', 'item', 'quantity', 'unit_price', 'notes']
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Get the user's current shop
        user = self.request.user if self.request else None
        current_shop = None
        
        if user:
            # For admin, get selected shop from session
            if (user.role or '').lower() == 'admin':
                selected_shop_id = self.request.session.get('selected_shop_id')
                if selected_shop_id:
                    current_shop = Shop.objects.filter(id=selected_shop_id).first()
            # For other users, get from their user profile
            else:
                current_shop = user.shop
        
        # Set from_shop to current shop and make it read-only
        if current_shop:
            self.fields['from_shop'].queryset = Shop.objects.filter(id=current_shop.id)
            self.fields['from_shop'].initial = current_shop.id
            self.fields['from_shop'].disabled = True
        else:
            self.fields['from_shop'].queryset = Shop.objects.all()
        
        # To shop - exclude current shop to avoid same-shop transfer
        if current_shop:
            self.fields['to_shop'].queryset = Shop.objects.exclude(id=current_shop.id)
        else:
            self.fields['to_shop'].queryset = Shop.objects.all()
        
        # Set empty label for item field - will show when queryset has items
        self.fields['item'].empty_label = "-- Select an item from the 'From Shop' inventory --"
        
        # Filter items based on from_shop selection if already selected (POST data)
        from_shop_id = self.data.get('from_shop') or self.initial.get('from_shop') or (current_shop.id if current_shop else None)
        if from_shop_id:
            self.fields['item'].queryset = Item.objects.filter(shop_id=from_shop_id)
        else:
            # Show all items initially - validation will handle wrong shop in clean()
            self.fields['item'].queryset = Item.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        from_shop = cleaned_data.get('from_shop')
        to_shop = cleaned_data.get('to_shop')
        item = cleaned_data.get('item')
        quantity = cleaned_data.get('quantity')
        
        # Prevent same shop transfer
        if from_shop and to_shop and from_shop == to_shop:
            raise forms.ValidationError("Cannot transfer items to the same shop.")
        
        # Check if item is available in from_shop
        if from_shop and item and quantity:
            if item.shop != from_shop:
                raise forms.ValidationError(f"The item '{item.name}' does not belong to {from_shop.name}.")
            
            if item.quantity < quantity:
                raise forms.ValidationError(
                    f"Not enough stock. {from_shop.name} only has {item.quantity} of '{item.name}'."
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        obj = super().save(commit=False)
        
        if commit:
            from_shop = obj.from_shop
            to_shop = obj.to_shop
            item = obj.item
            quantity = obj.quantity
            
            # Reduce quantity from from_shop
            item.quantity -= quantity
            item.save()
            
            # Add quantity to to_shop - check if item exists
            to_shop_item = Item.objects.filter(name=item.name, shop=to_shop).first()
            if to_shop_item:
                # Item exists in to_shop - add quantity
                to_shop_item.quantity += quantity
                to_shop_item.save()
                # Update the credit to reference the to_shop's item
                obj.item = to_shop_item
            else:
                # Create new item in to_shop
                new_item = Item.objects.create(
                    name=item.name,
                    price=item.price,
                    quantity=quantity,
                    description=item.description,
                    part_number=item.part_number,
                    shop=to_shop
                )
                obj.item = new_item
            
            obj.save()
        
        return obj


class InterShopSettlementForm(forms.ModelForm):
    """Form for settling inter-shop credits"""
    class Meta:
        model = InterShopSettlement
        fields = ['from_shop', 'to_shop', 'amount', 'payment_method', 'notes']
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        self.fields['from_shop'].queryset = Shop.objects.all()
        self.fields['to_shop'].queryset = Shop.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        from_shop = cleaned_data.get('from_shop')
        to_shop = cleaned_data.get('to_shop')
        amount = cleaned_data.get('amount')
        
        if from_shop and to_shop and amount:
            # Calculate total owed by from_shop to to_shop
            total_owed = InterShopCredit.objects.filter(
                from_shop=from_shop,
                to_shop=to_shop
            ).exclude(status='settled').aggregate(
                total=models.Sum('total_amount') - models.Sum('settled_amount')
            )['total'] or 0
            
            if amount > total_owed:
                raise forms.ValidationError(
                    f"Amount cannot exceed total debt. {from_shop.name} owes {to_shop.name} {total_owed}.")
        
        return cleaned_data