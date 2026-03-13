from django.urls import path
from . import views

app_name = 'sales'


urlpatterns = [
    path('', views.sales_list, name='sales_list'),
    path('new/', views.make_sale, name='make_sale'),
    path('credits/', views.credit_list, name='credit_list'),
    path('credits/new/', views.make_credit, name='make_credit'),
    path('credits/edit/<int:credit_id>/',
         views.edit_credit, name='edit_credit'),


    # Export URLs
    path('export/sales/', views.export_sales_csv, name='export_sales_csv'),
    path('export/credits/', views.export_credits_csv, name='export_credits_csv'),
    path('export/inventory/', views.export_inventory_csv,
         name='export_inventory_csv'),

    #     reciept URLs
    path('receipt/<int:sale_id>/', views.sale_receipt, name='sale_receipt'),
    path('receipt/<int:sale_id>/pdf/',
         views.sale_receipt_pdf, name='sale_receipt_pdf'),
    path('credits/receipt/<int:credit_id>/',
         views.credit_receipt, name='credit_receipt'),
    path('credits/receipt/<int:credit_id>/pdf/',
         views.credit_receipt_pdf, name='credit_receipt_pdf'),

     # cancel sales urls
     path('cancel-sale/<int:sale_id>/', views.cancel_sale, name='cancel_sale'),
     # cancel credit urls
     path('cancel-credit/<int:credit_id>/', views.cancel_credit, name='cancel_credit'),

     # return URLs
     path('return/<int:sale_id>/', views.make_return, name='make_return'),
     path('return/receipt/<int:return_id>/', views.return_receipt, name='return_receipt'),
     path('return/receipt/<int:return_id>/pdf/', views.return_receipt_pdf, name='return_receipt_pdf'),
     path('returns/', views.return_list, name='return_list'),
     path('return/refund/<int:return_id>/', views.process_refund, name='process_refund'),

     # Inter-Shop Credit URLs
     path('inter-shop/', views.inter_shop_credit_list, name='inter_shop_credit_list'),
     path('inter-shop/new/', views.make_inter_shop_credit, name='make_inter_shop_credit'),
     path('inter-shop/<int:credit_id>/settle/', views.settle_inter_shop_credit, name='settle_inter_shop_credit'),
     path('inter-shop/settlements/', views.inter_shop_settlement_list, name='inter_shop_settlement_list'),

]
