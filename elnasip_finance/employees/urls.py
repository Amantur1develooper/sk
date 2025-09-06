from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employees_list, name='employees_list'),
     path('employees/', views.employee_list, name='employee_list'),
    path('employee/<int:employee_id>/', views.employee_dashboard, name='employee_dashboard'),
    path('salary-payments/', views.salary_payments_list, name='salary_payments_list'),
     path('employee/<int:employee_id>/payments/new/', views.salary_payment_create_for_employee, name='salary_payment_create_for_employee'),
    path('employee/<int:employee_id>/payments/', views.salary_payment_list_for_employee, name='salary_payment_list_for_employee'),

    #  path('payments/', views.salary_payment_list, name='salary_payment_list'),
    # path('payments/new/', views.salary_payment_create, name='salary_payment_create'),
]