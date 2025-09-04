from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employees_list, name='employees_list'),
     path('employees/', views.employee_list, name='employee_list'),
    path('employee/<int:employee_id>/', views.employee_dashboard, name='employee_dashboard'),
    path('salary-payments/', views.salary_payments_list, name='salary_payments_list'),
]