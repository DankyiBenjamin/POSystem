from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Item, Restock
from sales.models import Sale, Credit
from django.utils.timezone import now
from .forms import ItemForm, RestockForm


@login_required
def dashboard_view(request):
    # view information at a glance

    today = now().date()

    # 1. Total sales made today
    sales_today = Sale.objects.filter(closed_at__date=today)
    total_sales_today = sum(s.total_sales for s in sales_today)

    # 2. Total outstanding credits (unpaid)
    total_credits = Credit.objects.filter(paid=False).count()

    # 3. Total items in stock
    total_inventory_items = Item.objects.count()

    # low stock items
    low_stock_items = [item for item in Item.objects.all()
                       if item.is_low_stock()]
    low_stock_count = len(low_stock_items)

    # context
    context = {
        'total_sales_today': total_sales_today,
        'total_credits': total_credits,
        'total_inventory_items': total_inventory_items,
        'low_stock_count': low_stock_count,
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required
def item_list(request):
    items = Item.objects.all()
    return render(request, 'inventory/item_list.html', {'items': items})


@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            return redirect('item_list')
    else:
        form = ItemForm()
    return render(request, 'inventory/item_form.html', {'form': form, 'title': 'Add Item'})


@login_required
def update_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('item_list')
    else:
        form = ItemForm(instance=item)
    return render(request, 'inventory/item_form.html', {'form': form, 'title': 'Update Item'})


@login_required
def restock_item(request):
    if request.method == 'POST':
        form = RestockForm(request.POST)
        if form.is_valid():
            restock = form.save(commit=False)
            restock.added_by = request.user
            item = restock.item
            item.quantity += restock.quantity_added
            item.total_stock_added += restock.quantity_added
            item.save()
            restock.save()
            return redirect('item_list')
    else:
        form = RestockForm()
    return render(request, 'inventory/restock_form.html', {'form': form})

# low stock list


@login_required
def low_stock_list(request):
    low_stock_list = [item for item in Item.objects.all()
                      if item.is_low_stock()]
    return render(request, 'inventory/low_stock_list.html', {'low_stock_list': low_stock_list})
