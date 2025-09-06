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



from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Если суперпользователь → кидаем в админку или спец. страницу
            if user.is_superuser:
                return redirect("admin:index")   # можно заменить на свою страницу
            else:
                return redirect("projects:projects_list")  # страница для простых пользователей
        else:
            messages.error(request, "Неверное имя пользователя или пароль")

    return render(request, "auth/login.html")

from django.contrib.auth.decorators import login_required

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")  # возвращаем на страницу входа

from django.shortcuts import render, redirect
from django.contrib import messages
# from .forms import SalaryPaymentForm
# employees/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Employee, SalaryPayment
from .forms import SalaryPaymentForEmployeeForm

@login_required
def salary_payment_create_for_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        form = SalaryPaymentForEmployeeForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.employee = employee
            payment.save()  # здесь сработает твой SalaryPayment.save() — создаст CashFlow/Expense/Allocation
            messages.success(request, f'Выплата {payment.get_payment_type_display()} ({payment.amount}) для {employee.full_name} создана.')
            # редирект куда угодно — например на страницу сотрудника или список выплат сотрудника
            return redirect('employees:employee_dashboard', employee_id=employee.id)
    else:
        # можно задать начальные значения (например, period = today)
        form = SalaryPaymentForEmployeeForm(initial={'period': None})

    return render(request, 'employees/salary_payment_form_for_employee.html', {
        'form': form,
        'employee': employee,
    })

# def salary_payment_create(request):
#     if request.method == 'POST':
#         form = SalaryPaymentForm(request.POST)
#         if form.is_valid():
#             payment = form.save()
#             messages.success(request, f'✅ {payment.get_payment_type_display()} в размере {payment.amount} сом выплачена сотруднику {payment.employee.full_name}')
#             return redirect('salary_payment_list')  # сделаем список выплат
#     else:
#         form = SalaryPaymentForm()

#     return render(request, 'employees/salary_payment_form.html', {'form': form})


from .models import SalaryPayment
def salary_payment_list_for_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    payments = employee.payments.select_related('employee').order_by('-date')
    return render(request, 'employees/salary_payment_list_for_employee.html', {
        'employee': employee,
        'payments': payments,
    })

def salary_payment_list(request):
    payments = SalaryPayment.objects.select_related('employee').order_by('-date')
    return render(request, 'employees/salary_payment_list.html', {'payments': payments})
