from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CommonCash, CashFlow, Allocation, Expense, Sale
from projects.models import Project, Block, EstimateItem
from employees.models import Employee, SalaryPayment
from django.db.models import Sum
from django.db.models import Sum, Q
from django.db.models import Q
from django.utils.dateparse import parse_date
from projects.models import Block

@login_required
def common_cash_detail(request):
    common_cash = CommonCash.objects.first()
    cash_flows = CashFlow.objects.all().order_by('-date')

    # Получаем список блоков для выпадающего списка
    blocks = Block.objects.all()

    # Фильтры из GET-запроса
    flow_type = request.GET.get("flow_type")   # 'income' или 'expense'
    block_id = request.GET.get("block")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Фильтр по типу операции
    if flow_type in ["income", "expense"]:
        cash_flows = cash_flows.filter(flow_type=flow_type)

    # Фильтр по блоку
    if block_id:
        cash_flows = cash_flows.filter(block_id=block_id)

    # Фильтр по датам
    if start_date:
        cash_flows = cash_flows.filter(date__date__gte=start_date)
    if end_date:
        cash_flows = cash_flows.filter(date__date__lte=end_date)

    # Экспорт в Excel
    if "export" in request.GET:
        return export_cash_flows_to_excel(cash_flows)
    
    total_income = cash_flows.filter(flow_type="income").aggregate(Sum("amount"))["amount__sum"] or 0
    total_expense = cash_flows.filter(flow_type="expense").aggregate(Sum("amount"))["amount__sum"] or 0
    net_balance = total_income - total_expense
    
    context = {
        'common_cash': common_cash,
        'cash_flows': cash_flows,
        'blocks': blocks,
        
        
        
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
    }
    
    
    return render(request, 'finances/common_cash_detail.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from .models import Block, EstimateItem, CommonCash, Allocation
from .forms import AllocationForm

def allocation_create(request):
    common_cash = get_object_or_404(CommonCash, pk=1)
    blocks = Block.objects.all()
    block_id = request.GET.get("block")

    form = None
    if block_id:
        estimate_items = EstimateItem.objects.filter(block_id=block_id)
        if request.method == "POST":
            form = AllocationForm(request.POST)
            form.fields["estimate_item"].queryset = estimate_items
            if form.is_valid():
                allocation = form.save(commit=False)
                allocation.save()
                return redirect("finances:allocations_list")
        else:
            form = AllocationForm()
            form.fields["estimate_item"].queryset = estimate_items

    context = {
        "common_cash": common_cash,
        "blocks": blocks,
        "block_id": int(block_id) if block_id else None,
        "form": form,
    }
    return render(request, "finances/allocation_create.html", context)

# @login_required
# def common_cash_detail(request):
#     common_cash = CommonCash.objects.first()
#     cash_flows = CashFlow.objects.all().order_by('-date')

#     # Фильтры из GET-запроса
#     flow_type = request.GET.get("flow_type")   # 'income' или 'expense'
#     block_id = request.GET.get("block")
#     start_date = request.GET.get("start_date")
#     end_date = request.GET.get("end_date")

#     # Фильтр по типу операции
#     if flow_type in ["income", "expense"]:
#         cash_flows = cash_flows.filter(flow_type=flow_type)

#     # Фильтр по блоку (ищем блок в описании!)
#     if block_id:
#         cash_flows = cash_flows.filter(description__icontains=f"блок {block_id}")

#     # Фильтр по датам
#     if start_date:
#         cash_flows = cash_flows.filter(date__date__gte=parse_date(start_date))
#     if end_date:
#         cash_flows = cash_flows.filter(date__date__lte=parse_date(end_date))

#     # Экспорт в Excel
#     if "export" in request.GET:
#         return export_cash_flows_to_excel(cash_flows)

#     context = {
#         'common_cash': common_cash,
#         'cash_flows': cash_flows,
#     }
#     return render(request, 'finances/common_cash_detail.html', context)


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

#     # 🔹 итоги
#     total_income = cash_flows.filter(flow_type="income").aggregate(sum=Sum("amount"))["sum"] or 0
#     total_expense = cash_flows.filter(flow_type="expense").aggregate(sum=Sum("amount"))["sum"] or 0
#     net_balance = total_income - total_expense

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
#         'total_income': total_income,
#         'total_expense': total_expense,
#         'net_balance': net_balance,
#     }
#     return render(request, 'finances/common_cash_detail.html', context)

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
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from django.http import HttpResponse
from datetime import datetime

def export_cash_flows_to_excel(cash_flows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cash Flows"

    # 🔹 Заголовки
    headers = ["Дата", "Тип", "Сумма", "Описание", "Блок", "Создал"]
    ws.append(headers)

    # 🔹 Стили заголовков
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # 🔹 Данные
    for flow in cash_flows:
        ws.append([
            flow.date.strftime("%d.%m.%Y %H:%M"),
            "Приход" if flow.flow_type == "income" else "Расход",
            float(flow.amount),
            flow.description,
            flow.block.name if flow.block else "—",            # Название блока
            flow.created_by.get_full_name() or flow.created_by.username,  # ФИО или username
        ])

    # 🔹 Автоширина колонок
    for column_cells in ws.columns:
        length = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2

    # 🔹 Итоги
    total_income = sum(f.amount for f in cash_flows if f.flow_type == "income")
    total_expense = sum(f.amount for f in cash_flows if f.flow_type == "expense")
    net_balance = total_income - total_expense

    ws.append([])
    ws.append(["", "ИТОГО:"])
    ws.append(["", "Общий приход", float(total_income)])
    ws.append(["", "Общий расход", float(total_expense)])
    ws.append(["", "Разница", float(net_balance)])

    # 🔹 Запись в память
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # 🔹 Имя файла с датой
    filename = f"cash_flows_{datetime.now().strftime('%d-%m-%Y')}.xlsx"

    # 🔹 HTTP-ответ
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

# def export_cash_flows_to_excel(cash_flows):
#     wb = openpyxl.Workbook()
#     ws = wb.active
#     ws.title = "Cash Flows"

#     # Заголовки
#     ws.append(["Дата", "Тип", "Сумма", "Описание"])

#     # Данные
#     for flow in cash_flows:
#         ws.append([
#             flow.date.strftime("%d.%m.%Y %H:%M"),
#             "Приход" if flow.flow_type == "income" else "Расход",
#             float(flow.amount),
#             flow.description,
#         ])

#     # Запись в память
#     buffer = BytesIO()
#     wb.save(buffer)
#     buffer.seek(0)

#     # HTTP-ответ
#     response = HttpResponse(
#         buffer.getvalue(),
#         content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
#     response['Content-Disposition'] = 'attachment; filename=cash_flows.xlsx'
#     return response

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


# views.py
from projects.models import Block
# finances/views.py (часть)
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AllocationForm
from .models import CommonCash, CashFlow, Allocation
from projects.models import Block, EstimateItem
from django.shortcuts import render, get_object_or_404, redirect
from .models import Block, EstimateItem, CommonCash, Allocation
from .forms import AllocationForm

def allocation_create(request):
    common_cash = CommonCash.objects.first()
    blocks = Block.objects.all()
    block_id = request.GET.get("block")

    form = None
    if block_id:
        estimate_items = EstimateItem.objects.filter(block_id=block_id)
        print(f"Block ID: {block_id}, Found items: {estimate_items.count()}")  # Отладочный вывод
        if request.method == "POST":
            form = AllocationForm(request.POST)
            form.fields["estimate_item"].queryset = estimate_items
            if form.is_valid():
                allocation = form.save(commit=False)
                # allocation = form.save(commit=False)

                # if common_cash.balance < allocation.amount:
                #     messages.error(request, 'Недостаточно средств в Общаге')
                #     return render(request, 'finances/allocation_form.html', {'form': form, 'common_cash': common_cash, 'blocks': blocks, 'block_id': block_id})
                            
                # создаём CashFlow и привязываем block из estimate_item
                cash_flow = CashFlow.objects.create(
                    common_cash=common_cash,
                    flow_type='expense',
                    amount=allocation.amount,
                    block=allocation.estimate_item.block,
                    description=f"Выделение средств: {allocation.description}",
                    created_by=request.user
                )

                allocation.common_cash = common_cash
                allocation.save()

                messages.success(request, f'Средства в размере {allocation.amount} сом успешно выделены!')
    
                return redirect("finances:common_cash_detail")
        else:
            form = AllocationForm()
            form.fields["estimate_item"].queryset = estimate_items

    context = {
        "common_cash": common_cash,
        "blocks": blocks,
        "block_id": int(block_id) if block_id else None,
        "form": form,
    }
    return render(request, "finances/allocation_create.html", context)

# def create_allocation(request):
#     common_cash = CommonCash.objects.first()
#     blocks = Block.objects.all()
#     block_id = request.GET.get('block')  # фильтр по блоку в GET

#     # На GET: инициализируем форму и подрезаем queryset позиций если выбран блок
#     if request.method == 'GET':
#         form = AllocationForm()
#         if block_id:
#             form.fields['estimate_item'].queryset = EstimateItem.objects.filter(block_id=block_id)
#     else:
#         # POST
#         form = AllocationForm(request.POST)
#         # важно: чтобы валидация прошла, убедимся, что в queryset есть выбранный элемент
#         # оставим полный queryset (или можно подрезать как выше)
#         form.fields['estimate_item'].queryset = EstimateItem.objects.select_related('block', 'category').all()

#         if form.is_valid():
#             try:
#                 allocation = form.save(commit=False)

#                 if common_cash.balance < allocation.amount:
#                     messages.error(request, 'Недостаточно средств в Общаге')
#                     return render(request, 'finances/allocation_form.html', {'form': form, 'common_cash': common_cash, 'blocks': blocks, 'block_id': block_id})

#                 # создаём CashFlow и привязываем block из estimate_item
#                 cash_flow = CashFlow.objects.create(
#                     common_cash=common_cash,
#                     flow_type='expense',
#                     amount=allocation.amount,
#                     block=allocation.estimate_item.block,
#                     description=f"Выделение средств: {allocation.description}",
#                     created_by=request.user
#                 )

#                 allocation.common_cash = common_cash
#                 allocation.save()

#                 messages.success(request, f'Средства в размере {allocation.amount} сом успешно выделены!')
                
#                 return redirect('finances:common_cash_detail')
            
#             except Exception as e:
#                 messages.error(request, f'Ошибка при выделении средств: {str(e)}')

#     return render(request, 'finances/allocation_form.html', {
#         'form': form,
#         'common_cash': common_cash,
#         'blocks': blocks,
#         'block_id': int(block_id) if block_id else None
#     })

# def create_allocation(request):
#     common_cash = CommonCash.objects.first()
#     block_id = request.GET.get("block")

#     if request.method == 'POST':
#         form = AllocationForm(request.POST)
#         if form.is_valid():
#             allocation = form.save(commit=False)

#             if common_cash.balance < allocation.amount:
#                 messages.error(request, 'Недостаточно средств в Общаге')
#                 return render(request, 'finances/allocation_form.html', {'form': form, 'common_cash': common_cash})

#             cash_flow = CashFlow.objects.create(
#                 common_cash=common_cash,
#                 flow_type='expense',
#                 amount=allocation.amount,
#                 block=allocation.estimate_item.block,
#                 description=f"Выделение средств: {allocation.description}",
#                 created_by=request.user
#             )
#             allocation.common_cash = common_cash
#             allocation.save()
#             messages.success(request, f'Средства в размере {allocation.amount} сом успешно выделены!')
#             return redirect('finances:common_cash_detail')
#     else:
#         form = AllocationForm()

#     # фильтруем estimate_item если выбран блок
#     if block_id:
#         form.fields['estimate_item'].queryset = form.fields['estimate_item'].queryset.filter(block_id=block_id)

#     blocks = Block.objects.all()
#     return render(request, 'finances/allocation_form.html', {
#         'form': form,
#         'common_cash': common_cash,
#         'blocks': blocks,
#         'block_id': int(block_id) if block_id else None
#     })
from django.http import JsonResponse

# finances/views.py
from django.http import JsonResponse
from django.db.models import Q
from projects.models import EstimateItem
from django.http import JsonResponse
from .models import EstimateItem

def get_estimate_items(request):
    block_id = request.GET.get("block_id")
    items = EstimateItem.objects.filter(block_id=block_id).values("id", "name") if block_id else []
    return JsonResponse(list(items), safe=False)

def get_estimate_items3(request):
    """
    Возвращает JSON список позиций сметы.
    Параметры GET:
      - q: строка поиска (опционально)
      - block_id: id блока (опционально)
    """
    q = request.GET.get('q', '').strip()
    block_id = request.GET.get('block_id')

    qs = EstimateItem.objects.select_related('block', 'category').all()

    if block_id:
        qs = qs.filter(block_id=block_id)

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(block__name__icontains=q) |
            Q(category__name__icontains=q)
        )

    # лимитируем результат
    items = []
    for it in qs[:200]:
        display = f"{it.block.name} — {it.category.name} — {it.name}"
        items.append({'id': it.id, 'text': display})

    return JsonResponse({'results': items})

# def get_estimate_items(request):
#     block_id = request.GET.get("block_id")
#     items = EstimateItem.objects.filter(block_id=block_id).values("id", "name")
#     return JsonResponse(list(items), safe=False)

# @login_required
# @transaction.atomic
# def create_allocation(request):
#     common_cash = CommonCash.objects.first()
    
#     if request.method == 'POST':
#         form = AllocationForm(request.POST)
#         if form.is_valid():
#             try:
#                 # Создаем запись о выделении средств
#                 allocation = form.save(commit=False)
                
#                 # Проверяем достаточно ли средств в Общаге
#                 if common_cash.balance < allocation.amount:
#                     messages.error(request, 'Недостаточно средств в Общаге')
#                     return render(request, 'finances/allocation_form.html', {'form': form})
                
#                 # Создаем запись о движении денег (расход)
#                 cash_flow = CashFlow.objects.create(
#                     common_cash=common_cash,
#                     flow_type='expense',
#                     amount=allocation.amount,
#                     block=allocation.estimate_item.block,  
#                     description=f"Выделение средств: {allocation.description}",
#                     created_by=request.user
#                 )
                
#                 # Сохраняем выделение средств
#                 allocation.common_cash = common_cash
#                 allocation.save()
                
#                 messages.success(request, f'Средства в размере {allocation.amount} сом успешно выделены!')
#                 # return redirect('finances:allocations_list')
#                 return redirect('finances:common_cash_detail')
                
#             except Exception as e:
#                 messages.error(request, f'Ошибка при выделении средств: {str(e)}')
#     else:
#         form = AllocationForm()
    
#     context = {
#         'form': form,
#         'common_cash': common_cash,
#     }
#     return render(request, 'finances/allocation_form.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoanForm, LoanPaymentForm
from .models import Loan, LoanPayment

@login_required
def loans_list(request):
    loans = Loan.objects.all().order_by('-issued_date')
    
    # Фильтрация по типу займа
    loan_type = request.GET.get('type')
    if loan_type in ['given', 'taken']:
        loans = loans.filter(loan_type=loan_type)
    
    # Фильтрация по статусу
    status = request.GET.get('status')
    if status in ['active', 'repaid', 'overdue']:
        loans = loans.filter(status=status)
    
    context = {
        'loans': loans,
        'current_type': loan_type,
        'current_status': status,
    }
    return render(request, 'finances/loans_list.html', context)

@login_required
def loan_detail(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    payments = loan.payments.all().order_by('-payment_date')
    
    context = {
        'loan': loan,
        'payments': payments,
    }
    return render(request, 'finances/loan_detail.html', context)

@login_required
def create_loan(request):
    common_cash = CommonCash.objects.first()
    
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.common_cash = common_cash
            loan.created_by = request.user
            
            # Проверяем достаточно ли средств для выдачи займа
            if loan.loan_type == 'given' and common_cash.balance < loan.amount:
                messages.error(request, 'Недостаточно средств в Общаге для выдачи займа')
                return render(request, 'finances/loan_form.html', {'form': form})
            
            loan.save()
            messages.success(request, 'Займ успешно создан')
            return redirect('finances:loans_list')
    else:
        form = LoanForm()
    
    context = {
        'form': form,
        'common_cash': common_cash,
    }
    return render(request, 'finances/loan_form.html', context)

@login_required
def add_loan_payment(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    common_cash = loan.common_cash
    
    if request.method == 'POST':
        form = LoanPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.loan = loan
            payment.created_by = request.user
            
            # Проверяем достаточно ли средств для возврата полученного займа
            if loan.loan_type == 'taken' and common_cash.balance < payment.amount:
                messages.error(request, 'Недостаточно средств в Общаге для возврата займа')
                return render(request, 'finances/loan_payment_form.html', {'form': form, 'loan': loan})
            
            # Проверяем не превышает ли платеж остаток по займу
            if payment.amount > loan.remaining_amount:
                messages.error(request, f'Сумма платежа не может превышать остаток по займу: {loan.remaining_amount}')
                return render(request, 'finances/loan_payment_form.html', {'form': form, 'loan': loan})
            
            payment.save()
            messages.success(request, 'Платеж по займу успешно добавлен')
            return redirect('finances:loan_detail', loan_id=loan.id)
    else:
        form = LoanPaymentForm()
    
    context = {
        'form': form,
        'loan': loan,
    }
    return render(request, 'finances/loan_payment_form.html', context)