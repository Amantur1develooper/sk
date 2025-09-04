from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Employee, SalaryPayment
from django.conf import settings
from django.contrib import admin

admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [ 'full_name','position', 'hire_date', 'salary']
    search_fields = [ 'full_name', 'position']
    filter_horizontal = ['blocks'] 
    
    
@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payment_type', 'amount', 'date', 'period']
    list_filter = ['payment_type', 'period']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']