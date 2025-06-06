from django.urls import path
from . import views

app_name = 'sales'


urlpatterns = [
    path('', views.sales_list, name='sales_list'),
    path('new/', views.make_sale, name='make_sale'),
    path('credits/', views.credit_list, name='credit_list'),
    path('credits/new/', views.make_credit, name='make_credit'),
]
