from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Item, Restock, Shop
from sales.models import Sale, Credit
from django.db.models import Q
from django.utils.timezone import now
from .forms import ItemForm, RestockForm
from inventory.utils import get_user_shop_queryset


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


def is_manager(user):
    return user.is_authenticated and user.role == 'manager'


def is_staff(user):
    return user.is_authenticated and user.role == 'staff'


def is_admin_or_manager(user):
    return user.is_authenticated and user.role in ['admin', 'manager']


@login_required

def dashboard_view(request):
    today = now().date()
    user = request.user

    # Determine selected shop
    if user.role == 'admin':
        shop_id = request.GET.get('shop')
        if shop_id:
            request.session['selected_shop_id'] = shop_id
        selected_shop_id = request.session.get('selected_shop_id')
        selected_shop = get_object_or_404(Shop, id=selected_shop_id) if selected_shop_id else None
    else:
        selected_shop = user.shop
        request.session['selected_shop_id'] = selected_shop.id

    # Filter objects by selected shop
    sales_today = Sale.objects.filter(closed_at__date=today, shop=selected_shop)
    credits = Credit.objects.filter(shop=selected_shop)
    paid_credits_today = credits.filter(paid=True, paid_at__date=today)
    inventory_items = Item.objects.filter(shop=selected_shop)

    # Identify low stock items
    low_stock_items = [item for item in inventory_items if item.is_low_stock()]

    # Compute totals
    direct_sales_total = sum(s.total_sales for s in sales_today)
    paid_credit_total = sum(c.item.price * c.quantity for c in paid_credits_today)
    total_sales_today = direct_sales_total + paid_credit_total

    context = {
        'selected_shop': selected_shop,
        'available_shops': Shop.objects.all() if user.role == 'admin' else [],
        'total_sales_today': total_sales_today,
        'total_credits': credits.filter(paid=False).count(),
        'total_inventory_items': inventory_items.count(),
        'low_stock_count': len(low_stock_items),
    }

    return render(request, 'inventory/dashboard.html', context)


# list of items in the inventory
@login_required
def item_list(request):
    user = request.user
    # Get search query from request
    search_query = request.GET.get('q', '')

    # Determine shop
    if user.role == 'admin':
        shop_id = request.session.get('selected_shop_id')
        # Get all items for the selected shop or none if no shop is selected
        base_qs = Item.objects.filter(shop_id=shop_id) if shop_id else Item.objects.none()
    else:
        base_qs = Item.objects.filter(shop=user.shop)

    # Apply search filter
    if search_query:
        items = base_qs.filter(
            Q(name__icontains=search_query) | Q(part_number__icontains=search_query)
        )
    else:
        items = base_qs

    return render(request, 'inventory/item_list.html', {
        'items': items,
        'search_query': search_query
    })



@user_passes_test(is_admin_or_manager)
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


@user_passes_test(is_admin_or_manager)
@login_required
def restock_item(request):
    if request.method == 'POST':
        form = RestockForm(request.POST, request=request)
        if form.is_valid():
            restock = form.save(commit=False)
            restock.added_by = request.user

            item = restock.item
            item.quantity += restock.quantity_added
            item.total_stock_added += restock.quantity_added
            item.save()

            restock.shop = item.shop
            restock.save()

            return redirect('item_list')
    else:
        form = RestockForm(request=request)

    return render(request, 'inventory/restock_form.html', {'form': form})

# low stock list


@login_required
def low_stock_list(request):
    user = request.user

    if user.role == 'admin':
        shop_id = request.session.get('selected_shop_id')
        # Get all items for the selected shop or none if no shop is selected
        items = Item.objects.filter(
            shop_id=shop_id) if shop_id else Item.objects.none()
    else:
        # For non-admin users, filter items by their shop
        items = Item.objects.filter(shop=user.shop)

    low_stock_list = [item for item in items
                      if item.is_low_stock()]
    return render(request, 'inventory/low_stock_list.html', {'low_stock_list': low_stock_list})


@login_required
@user_passes_test(is_admin)
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, f"✅ '{item.name}' has been deleted from inventory.")
    messages.error(request, f"❌ Failed to delete '{item.name}'.")
    return redirect('item_list')
# def low_stock_list(request):
#     # Get shop-filtered items


#     # Filter only those that are low stock
#     low_stock_items = [item for item in items if item.is_low_stock()]

#     return render(request, 'inventory/low_stock_list.html', {'items': low_stock_items})


# the low stock shop list is not showing
# the sales list and credit list are not filtering by shop
