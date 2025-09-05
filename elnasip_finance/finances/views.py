from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CommonCash, CashFlow, Allocation, Expense, Sale
from projects.models import Project, Block, EstimateItem
from employees.models import Employee, SalaryPayment
from django.db.models import Sum
from django.db.models import Sum, Q

@login_required
def common_cash_detail(request):
    common_cash = CommonCash.objects.first()
    cash_flows = CashFlow.objects.all().order_by('-date')

    # 🔹 фильтры
    block_id = request.GET.get('block')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if block_id:
        cash_flows = cash_flows.filter(description__icontains=Block.objects.get(id=block_id).name)

    if start_date:
        cash_flows = cash_flows.filter(date__date__gte=parse_date(start_date))
    if end_date:
        cash_flows = cash_flows.filter(date__date__lte=parse_date(end_date))

    # 🔹 итоги
    total_income = cash_flows.filter(flow_type="income").aggregate(sum=Sum("amount"))["sum"] or 0
    total_expense = cash_flows.filter(flow_type="expense").aggregate(sum=Sum("amount"))["sum"] or 0
    net_balance = total_income - total_expense

    # 🔹 экспорт в Excel
    if 'export' in request.GET:
        return export_cash_flows_to_excel(cash_flows)

    blocks = Block.objects.all()

    context = {
        'common_cash': common_cash,
        'cash_flows': cash_flows,
        'blocks': blocks,
        'selected_block': block_id,
        'start_date': start_date,
        'end_date': end_date,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
    }
    return render(request, 'finances/common_cash_detail.html', context)

@login_required
def dashboard(request):
    # Получаем данные для дашборда
    common_cash = CommonCash.objects.first()
    projects = Project.objects.all()
    total_projects = projects.count()
    total_blocks = Block.objects.count()
    
    # Считаем общие показатели
    total_income = CashFlow.objects.filter(flow_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = CashFlow.objects.filter(flow_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    margin = total_income - total_expense
    
    # Получаем последние операции
    recent_operations = CashFlow.objects.all().order_by('-date')[:10]
    
    context = {
        'common_cash': common_cash,
        'projects': projects,
        'total_projects': total_projects,
        'total_blocks': total_blocks,
        'total_income': total_income,
        'total_expense': total_expense,
        'margin': margin,
        'recent_operations': recent_operations,
    }
    return render(request, 'finances/dashboard.html', context)
import datetime
from django.utils.dateparse import parse_date
from django.http import HttpResponse
import openpyxl
from openpyxl.utils import get_column_letter
from django.db.models import Q
from projects.models import Block
from .models import CommonCash, CashFlow

# @login_required
# def common_cash_detail(request):
#     common_cash = CommonCash.objects.first()
#     cash_flows = CashFlow.objects.all().order_by('-date')

#     # 🔹 фильтры
#     block_id = request.GET.get('block')
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')

#     if block_id:
#         cash_flows = cash_flows.filter(description__icontains=Block.objects.get(id=block_id).name)

#     if start_date:
#         cash_flows = cash_flows.filter(date__date__gte=parse_date(start_date))
#     if end_date:
#         cash_flows = cash_flows.filter(date__date__lte=parse_date(end_date))

#     # 🔹 экспорт в Excel
#     if 'export' in request.GET:
#         return export_cash_flows_to_excel(cash_flows)

#     blocks = Block.objects.all()

#     context = {
#         'common_cash': common_cash,
#         'cash_flows': cash_flows,
#         'blocks': blocks,
#         'selected_block': block_id,
#         'start_date': start_date,
#         'end_date': end_date,
#     }
#     return render(request, 'finances/common_cash_detail.html', context)

import openpyxl
from io import BytesIO
from django.http import HttpResponse

def export_cash_flows_to_excel(cash_flows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cash Flows"

    # Заголовки
    ws.append(["Дата", "Тип", "Сумма", "Описание"])

    # Данные
    for flow in cash_flows:
        ws.append([
            flow.date.strftime("%d.%m.%Y %H:%M"),
            "Приход" if flow.flow_type == "income" else "Расход",
            float(flow.amount),
            flow.description,
        ])

    # Запись в память
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # HTTP-ответ
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename=cash_flows.xlsx'
    return response

# def export_cash_flows_to_excel(cash_flows):
#     wb = openpyxl.Workbook()
#     ws = wb.active
#     ws.title = "Движение средств"

#     headers = ["Дата", "Тип", "Сумма", "Описание"]
#     ws.append(headers)

#     for flow in cash_flows:
#         ws.append([
#             flow.date.strftime("%d.%m.%Y %H:%M"),
#             "Приход" if flow.flow_type == "income" else "Расход",
#             float(flow.amount),
#             flow.description
#         ])

#     # ширина колонок
#     for col_num, _ in enumerate(headers, 1):
#         ws.column_dimensions[get_column_letter(col_num)].width = 20

#     response = HttpResponse(
#         content=openpyxl.writer.excel.save_virtual_workbook(wb),
#         content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#     )
#     response['Content-Disposition'] = 'attachment; filename="cash_flows.xlsx"'
#     return response

# @login_required
# def common_cash_detail(request):
#     common_cash = CommonCash.objects.first()
#     cash_flows = CashFlow.objects.all().order_by('-date')
    
#     context = {
#         'common_cash': common_cash,
#         'cash_flows': cash_flows,
#     }
#     return render(request, 'finances/common_cash_detail.html', context)

@login_required
def allocations_list(request):
    allocations = Allocation.objects.all().order_by('-date')
    
    context = {
        'allocations': allocations,
    }
    return render(request, 'finances/allocations_list.html', context)

@login_required
def expenses_list(request):
    expenses = Expense.objects.all().order_by('-date')
    
    context = {
        'expenses': expenses,
    }
    return render(request, 'finances/expenses_list.html', context)

@login_required
def sales_list(request):
    sales = Sale.objects.all().order_by('-date')
    
    context = {
        'sales': sales,
    }
    return render(request, 'finances/sales_list.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import AllocationForm
from .models import CommonCash, CashFlow, Allocation
from projects.models import EstimateItem

@login_required
@transaction.atomic
def create_allocation(request):
    common_cash = CommonCash.objects.first()
    
    if request.method == 'POST':
        form = AllocationForm(request.POST)
        if form.is_valid():
            try:
                # Создаем запись о выделении средств
                allocation = form.save(commit=False)
                
                # Проверяем достаточно ли средств в Общаге
                if common_cash.balance < allocation.amount:
                    messages.error(request, 'Недостаточно средств в Общаге')
                    return render(request, 'finances/allocation_form.html', {'form': form})
                
                # Создаем запись о движении денег (расход)
                cash_flow = CashFlow.objects.create(
                    common_cash=common_cash,
                    flow_type='expense',
                    amount=allocation.amount,
                    description=f"Выделение средств: {allocation.description}",
                    created_by=request.user
                )
                
                # Сохраняем выделение средств
                allocation.common_cash = common_cash
                allocation.save()
                
                messages.success(request, f'Средства в размере {allocation.amount} сом успешно выделены!')
                # return redirect('finances:allocations_list')
                return redirect('finances:common_cash_detail')
                
            except Exception as e:
                messages.error(request, f'Ошибка при выделении средств: {str(e)}')
    else:
        form = AllocationForm()
    
    context = {
        'form': form,
        'common_cash': common_cash,
    }
    return render(request, 'finances/allocation_form.html', context)