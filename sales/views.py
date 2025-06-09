from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import SaleForm, CreditForm
from .models import Sale, SaleItem, Credit
from inventory.models import Item
from django.db import transaction

# printing reciepts
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.http import FileResponse

# exporting sales and credits to CSV
import csv
from django.http import HttpResponse


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


def is_manager(user):
    return user.is_authenticated and user.role == 'manager'


def is_staff(user):
    return user.is_authenticated and user.role == 'staff'


def is_admin_or_manager(user):
    return user.is_authenticated and user.role in ['admin', 'manager']


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
                return redirect('sales:sale_receipt', sale_id=sale.id)

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
                return redirect('sales:credit_receipt', credit_id=credit.id)
    else:
        form = CreditForm()
    return render(request, 'sales/make_credit.html', {'form': form})


@login_required
def sales_list(request):
    user = request.user

    if user.role == 'admin':
        shop_id = request.session.get('selected_shop_id')
        # get the sales of the specific shop or nothing
        sales = Sale.objects.filter(
            shop_id=shop_id) if shop_id else Sale.objects.none()
    else:
        sales = Sale.objects.filter(shop=user.shop)

    return render(request, 'sales/sales_list.html', {'sales': sales})


@login_required
def credit_list(request):
    user = request.user

    if user.role == 'admin':
        shop_id = request.session.get('selected_shop_id')
        # get the credits of the specific shop or nothing
        credits = Credit.objects.filter(
            shop_id=shop_id) if shop_id else Credit.objects.none()
    else:
        credits = Credit.objects.filter(shop=user.shop)

    return render(request, 'sales/credit_list.html', {'credits': credits})


@user_passes_test(is_admin_or_manager)
@login_required
def export_sales_csv(request):

    user = request.user
    if user.role == 'admin':
        shop_id = request.session.get('selected_shop_id')
        # get the sales of the specific shop or nothing
        sales = Sale.objects.filter(
            shop_id=shop_id) if shop_id else Sale.objects.none()
    else:
        sales = Sale.objects.filter(shop=user.shop)

    response = HttpResponse(content_type='text/csv')
    # set the name to the shop name
    response['Content-Disposition'] = 'attachment; filename="sales.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Date',
        'Customer Name',
        'Phone',
        'Sold By',
        'Item',
        'Quantity',
        'Subtotal',
        'Total Sale',
    ])

    for sale in sales:
        sale_items = sale.saleitem_set.all()
        for item in sale_items:
            writer.writerow([
                sale.closed_at,
                sale.customer_name,
                sale.customer_phone_number,
                sale.closed_by.username,
                item.item.name,
                item.quantity_sold,
                item.subtotal,
                sale.total_sales  # could be repeated for each row or left blank after first
            ])
    return response


@user_passes_test(is_admin_or_manager)
@login_required
def export_credits_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="credits.csv"'
    writer = csv.writer(response)
    writer.writerow(['Customer', 'Phone', 'Item', 'Qty', 'Paid?', 'Date'])

    # getting the user
    user = request.user
    if user.role == 'admin':
        shop_id = request.session.get('selected_shop_id')
        # get the credits of the specific shop or nothing
        credits = Credit.objects.filter(
            shop_id=shop_id) if shop_id else Credit.objects.none()
    else:
        credits = Credit.objects.filter(shop=user.shop)

    for credit in credits:
        writer.writerow([
            credit.customer_name,
            credit.customer_phone_number,
            credit.item.name,
            credit.quantity,
            'Yes' if credit.paid else 'No',
            credit.credited_at
        ])
    return response


@user_passes_test(is_admin_or_manager)
@login_required
def export_inventory_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory.csv"'
    writer = csv.writer(response)
    writer.writerow(['Item Name', 'Quantity', 'Price', 'Low Stock?', 'Shop'])
    user = request.user
    if user.role == 'admin':
        shop_id = request.session.get('selected_shop_id')
        items = Item.objects.filter(
            shop_id=shop_id) if shop_id else Item.objects.none()
    else:
        items = Item.objects.filter(shop=user.shop)

    for item in items:
        writer.writerow([
            item.name,
            item.quantity,
            item.price,
            'Yes' if item.is_low_stock() else 'No',
            item.shop.name if item.shop else ''
        ])
    return response


@login_required
def edit_credit(request, credit_id):
    credit = get_object_or_404(Credit, pk=credit_id)
    if request.method == 'POST':
        form = CreditForm(request.POST, instance=credit)
        if form.is_valid():
            form.save()
            messages.success(request, "Credit updated successfully.")
            return redirect('sales:credit_list')
    else:
        form = CreditForm(instance=credit)
    return render(request, 'sales/edit_credit.html', {'form': form, 'credit': credit})


@login_required
def sale_receipt(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    sale_items = sale.saleitem_set.all()
    return render(request, 'sales/receipt.html', {
        'sale': sale,
        'items': sale_items
    })


@login_required
def sale_receipt_pdf(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    sale_items = sale.saleitem_set.all()
    template = get_template('sales/receipt_pdf.html')
    html = template.render({'sale': sale, 'items': sale_items})
    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"receipt_{sale.id}.pdf")


@login_required
def credit_receipt(request, credit_id):
    credit = get_object_or_404(Credit, pk=credit_id)
    return render(request, 'sales/credit_receipt.html', {'credit': credit})


@login_required
def credit_receipt_pdf(request, credit_id):
    credit = get_object_or_404(Credit, pk=credit_id)
    template = get_template('sales/credit_receipt_pdf.html')
    html = template.render({'credit': credit})
    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"credit_{credit.id}.pdf")
