from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Apartment, DealPayment, Project, Block, EstimateCategory, EstimateItem

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_area', 'created_at']
    search_fields = ['name']

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'floors', 'total_area', 'sold_area', 'remaining_area']
    list_filter = ['project']
    search_fields = ['name', 'project__name']

@admin.register(EstimateCategory)
class EstimateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(EstimateItem)
class EstimateItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'block', 'category', 'quantity', 'unit_price', 'planned_amount', 'spent_amount', 'margin']
    list_filter = ['block__project', 'block', 'category']
    search_fields = ['name', 'block__name']
    
@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ['apartment_number', 'block', 'floor', 'rooms', 'area', 'is_sold', 'is_reserved']
    list_filter = ['block', 'floor', 'is_sold', 'is_reserved']
    search_fields = ['apartment_number', 'client_name']
    readonly_fields = ['deal_amount', 'remaining_deal_amount', 'created_at', 'updated_at']

@admin.register(DealPayment)
class DealPaymentAdmin(admin.ModelAdmin):
    list_display = ['apartment', 'amount', 'payment_date']
    list_filter = ['payment_date', 'apartment__block']
    search_fields = ['apartment__apartment_number', 'apartment__client_name']
    readonly_fields = ['created_at']