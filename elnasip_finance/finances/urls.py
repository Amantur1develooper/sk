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

    path("cars/", views.car_list, name="car_list"),
    path("cars/purchase/", views.car_purchase, name="car_purchase"),
    path("cars/<int:pk>/sale/", views.car_sale, name="car_sale"),
    
    path('loans/', views.loans_list, name='loans_list'),
    path('loans/create/', views.create_loan, name='create_loan'),
    path('loans/<int:loan_id>/', views.loan_detail, name='loan_detail'),
    path('loans/<int:loan_id>/payment/', views.add_loan_payment, name='add_loan_payment'),

]