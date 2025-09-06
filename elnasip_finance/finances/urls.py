from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('common-cash/', views.common_cash_detail, name='common_cash_detail'),
    path('allocations/create/', views.allocation_create, name='create_allocation'),
    path('allocations/', views.allocations_list, name='allocations_list'),
    path('expenses/', views.expenses_list, name='expenses_list'),
    path('sales/', views.sales_list, name='sales_list'),
    path("get-estimate-items/", views.get_estimate_items, name="get_estimate_items"),
    path('ajax/get-estimate-items/', views.get_estimate_items, name='get_estimate_items'),

]