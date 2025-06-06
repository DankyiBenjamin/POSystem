from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SaleForm, CreditForm
from .models import Sale, SaleItem, Credit
from inventory.models import Item
from django.db import transaction


@login_required
@transaction.atomic
def make_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['item']
            qty = form.cleaned_data['quantity']
            name = form.cleaned_data['customer_name']
            phone = form.cleaned_data['customer_phone_number']

            if item.quantity < qty:
                messages.error(request, "Not enough stock.")
                print(
                    f"Not enough stock for {item.name}. Requested: {qty}, Available: {item.quantity}")
            else:
                subtotal = item.price * qty
                sale = Sale.objects.create(
                    closed_by=request.user, total_sales=subtotal, shop=item.shop, customer_name=name, customer_phone_number=phone)
                SaleItem.objects.create(
                    sale=sale, item=item, quantity_sold=qty, subtotal=subtotal)

                item.quantity -= qty
                item.save()

                messages.success(
                    request, f"Sold {qty} {item.name} for {subtotal}")
                return redirect('sales:make_sale')
    else:
        form = SaleForm()
    return render(request, 'sales/make_sale.html', {'form': form})


@login_required
def make_credit(request):
    if request.method == 'POST':
        form = CreditForm(request.POST)
        if form.is_valid():
            credit = form.save(commit=False)
            item = credit.item
            if item.quantity < credit.quantity:
                messages.error(request, "Not enough stock for credit.")
            else:
                credit.credited_by = request.user
                credit.shop = item.shop
                item.quantity -= credit.quantity
                item.save()
                credit.save()
                messages.success(
                    request, f"{credit.quantity} {item.name} credited to {credit.customer_name}")
                return redirect('sales:make_credit')
    else:
        form = CreditForm()
    return render(request, 'sales/make_credit.html', {'form': form})


@login_required
def sales_list(request):
    sales = Sale.objects.all().order_by('-closed_at')
    return render(request, 'sales/sales_list.html', {'sales': sales})


@login_required
def credit_list(request):
    credits = Credit.objects.all().order_by('-credited_at')
    return render(request, 'sales/credit_list.html', {'credits': credits})
