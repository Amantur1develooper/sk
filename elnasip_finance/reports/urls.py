from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('cash-flow/', views.cash_flow_report, name='cash_flow_report'),
    path('projects/', views.project_report, name='project_report'),
    path('projects/<int:project_id>/', views.project_report, name='project_report_detail'),
    path('blocks/', views.block_report, name='block_report'),
    path('blocks/<int:block_id>/', views.block_report, name='block_report_detail'),
    path('allocations/', views.allocations_report, name='allocations_report'),
    path('salary/', views.salary_report, name='salary_report'),
    path('sales/', views.sales_report, name='sales_report'),
]