from django import template

register = template.Library()
from django.db.models import Sum

@register.filter
def planned_sum(estimate_items):
    return sum(item.planned_amount for item in estimate_items)  # Используем planned_amount вместо amount


@register.filter
def planned_sum2(estimate_items):
    """Сумма плановых затрат (quantity * unit_price)"""
    total = 0
    for item in estimate_items:
        total += item.quantity * item.unit_price
    return total

@register.filter
def spent_sum2(estimate_items):
    """Сумма фактических затрат через модель Allocation"""
    total = 0
    for item in estimate_items:
        # Суммируем все выделенные средства для этой позиции сметы
        allocations = item.allocations.aggregate(Sum('amount'))['amount__sum'] or 0
        total += allocations
    return total


# @register.filter
# def planned_sum2(estimate_items):
#     return estimate_items.aggregate(Sum('planned_amount'))['planned_amount__sum'] or 0

# @register.filter
# def spent_sum2(estimate_items):
#     return estimate_items.aggregate(Sum('spent_amount'))['spent_amount__sum'] or 0
# @register.filter
# def allocated_sum(allocations):
#     return sum(allocation.amount for allocation in allocations)

@register.filter
def spent_sum(estimate_items):
    return sum(item.spent_amount for item in estimate_items)