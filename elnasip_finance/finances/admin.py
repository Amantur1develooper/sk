from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CommonCash, CashFlow, Allocation, Expense, Sale

@admin.register(CommonCash)
class CommonCashAdmin(admin.ModelAdmin):
    list_display = ['balance']

@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    list_display = ['flow_type', 'amount', 'description', 'date', 'created_by']
    list_filter = ['flow_type', 'date']
    search_fields = ['description']

@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ['estimate_item', 'amount', 'description', 'date']
    list_filter = ['estimate_item__block__project', 'estimate_item__block']
    search_fields = ['description']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['estimate_item', 'amount', 'description', 'date', 'created_by']
    list_filter = ['estimate_item__block__project', 'estimate_item__block']
    search_fields = ['description']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['block', 'area', 'amount', 'date']
    list_filter = ['block__project', 'block']
    search_fields = ['client_info']