from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('items/', views.item_list, name='item_list'),
    path('item/add/', views.add_item, name='add_item'),
    path('item/update/<int:pk>/', views.update_item, name='update_item'),
    path('item/restock/', views.restock_item, name='restock_item'),
    path('items/low-stock/', views.low_stock_list, name='low_stock_list'),

]
