from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Employee, SalaryPayment
from django.db.models import Sum, Avg
@login_required
def employees_list(request):
    employees = Employee.objects.all()
    
    # Считаем общую сумму выплат
    from .models import SalaryPayment
    total_salary = SalaryPayment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Считаем среднюю зарплату
    avg_salary = employees.aggregate(Avg('salary'))['salary__avg'] if employees else 0
    
    context = {
        'employees': employees,
        'total_salary': total_salary,
        'avg_salary': avg_salary,
    }
    return render(request, 'employees/employees_list.html', context)
# @login_required
# def employees_list(request):
#     employees = Employee.objects.all()
    
#     context = {
#         'employees': employees,
#     }
#     return render(request, 'employees/employees_list.html', context)

@login_required
def salary_payments_list(request):
    payments = SalaryPayment.objects.all().order_by('-date')
    
    context = {
        'payments': payments,
    }
    return render(request, 'employees/salary_payments_list.html', context)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Employee, SalaryPayment
from django.db.models import Sum

def is_accountant_or_admin(user):
    return user.groups.filter(name__in=['Бухгалтер', 'Администратор']).exists() or user.is_superuser

@login_required
# @user_passes_test(is_accountant_or_admin, login_url='/accounts/login/')
def employee_dashboard(request, employee_id):
    # Получаем сотрудника по ID
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Получаем все выплаты сотрудника
    payments = SalaryPayment.objects.filter(employee=employee).order_by('-date')
    
    # Группируем выплаты по категориям
    payment_categories = {}
    for payment_type, payment_name in SalaryPayment.PAYMENT_TYPES:
        category_payments = payments.filter(payment_type=payment_type)
        if category_payments:
            total = category_payments.aggregate(Sum('amount'))['amount__sum']
            payment_categories[payment_name] = {
                'payments': category_payments,
                'total': total
            }
    
    # Общая сумма всех выплат
    total_earned = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Средняя сумма выплаты
    average_payment = total_earned / len(payments) if payments else 0
    
    context = {
        'employee': employee,
        'payment_categories': payment_categories,
        'total_earned': total_earned,
        'average_payment': average_payment,
        'payment_count': len(payments),
    }
    
    return render(request, 'employees/employee_dashboard.html', context)

@login_required
# @user_passes_test(is_accountant_or_admin, login_url='/accounts/login/')
def employee_list(request):
    # Список всех сотрудников для выбора
    employees = Employee.objects.all().order_by('full_name')
    
    # Добавляем информацию о последней выплате и общем количестве выплат
    for employee in employees:
        last_payment = SalaryPayment.objects.filter(employee=employee).order_by('-date').first()
        employee.last_payment = last_payment
        employee.payment_count = SalaryPayment.objects.filter(employee=employee).count()
    
    return render(request, 'employees/employee_list2.html', {'employees': employees})