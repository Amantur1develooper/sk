from datetime import timezone
from pyexpat.errors import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from projects.forms import ApartmentForm, DealPaymentForm
from finances.models import Allocation, CashFlow, CommonCash, Sale
from .models import Apartment, DealPayment, Project, Block, EstimateItem, EstimateCategory, RentPayment
from django.db.models import Sum, Avg

@login_required
def projects_list(request):
    projects = Project.objects.all()
    
    context = {
        'projects': projects,
    }
    return render(request, 'projects/projects_list.html', context)
# projects/views.py

from finances.models import Allocation
@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    blocks = project.blocks.prefetch_related('estimate_items', 'estimate_items__allocations')
    
    total_planned = 0
    total_allocated = 0
    total_spent = 0
    
    for block in blocks:
        # Считаем плановую сумму (quantity * unit_price)
        for item in block.estimate_items.all():
            total_planned += item.quantity * item.unit_price
        
        # Считаем выделенные средства
        for item in block.estimate_items.all():
            allocations = item.allocations.aggregate(Sum('amount'))['amount__sum'] or 0
            total_allocated += allocations
    must_buy = total_planned - total_allocated
    context = {
        'project': project,
        'blocks': blocks,
        'total_planned': total_planned,
        'must_buy':must_buy,
        'total_allocated': total_allocated,
        'total_spent': total_spent,
    }
    return render(request, 'projects/project_detail.html', context)
import re
from collections import OrderedDict
from decimal import Decimal

@login_required
def block_detail(request, block_id):
    block = get_object_or_404(Block, id=block_id)
    estimate_items = block.estimate_items.select_related('category').all()
    apartments = block.apartments.all()

    # --- ПРОДАЖИ ---
    fakt_prodaj = apartments.filter(is_sold=True).aggregate(
        Sum('deal_Fakt_deal_amount')
    )['deal_Fakt_deal_amount__sum'] or 0

    # Fallback цена: сначала поле блока, потом средняя по проданным
    block_price = block.planned_price_per_m2 or 0
    if not block_price:
        block_price = apartments.filter(
            is_sold=True, planned_price_per_m2__gt=0
        ).aggregate(avg=Avg('planned_price_per_m2'))['avg'] or 0

    # Для аналитики бронь считается как свободная (не бартер = потенциальная продажа)
    free_apts_data = apartments.filter(
        is_sold=False, is_barter=False
    ).values('area', 'planned_price_per_m2')
    plan_prodaj = sum(
        (a['area'] or 0) * (a['planned_price_per_m2'] if a['planned_price_per_m2'] else block_price)
        for a in free_apts_data
    )

    postupillo = block.received_amount

    # --- ДЛЯ ОСНОВНЫХ РАСЧЁТОВ (без категории 21) ---
    estimate_items_for_calc = estimate_items.exclude(
        category__name="21.Дополнительные расходы не входящие в смету"
    )

    total_planned_raw = sum(item.planned_amount for item in estimate_items)
    total_allocated_raw = sum(item.get_allocated_sum() for item in estimate_items)
    total_spent_raw = sum(item.spent_amount for item in estimate_items)
    total_margin_raw = total_planned_raw - total_spent_raw
    total_planned2 = total_planned_raw - total_allocated_raw

    # --- ОТДЕЛЬНО КАТЕГОРИЯ 21 ---
    extra_items = estimate_items.filter(
        category__name="21.Дополнительные расходы не входящие в смету"
    )

    extra_allocated = sum(item.get_allocated_sum() for item in extra_items)
    extra_planned = sum(item.planned_amount for item in extra_items)
    extra_spent = sum(item.spent_amount for item in extra_items)

    # --- ПЛАН ПО ОСНОВНОЙ СМЕТЕ ---
    total_planned = sum(item.planned_amount for item in estimate_items_for_calc)

    total_planned_positive = sum(
        item.planned_amount
        for item in estimate_items_for_calc
        if item.planned_amount > 0
    )
    total_planned_negative = sum(
        item.planned_amount
        for item in estimate_items_for_calc
        if item.planned_amount < 0
    )

    # --- НОРМАЛЬНЫЕ РАСХОДЫ / ПЕРЕРАСХОД ---
    normal_allocated = 0
    over_allocated = 0

    for item in estimate_items_for_calc:
        planned = item.planned_amount or 0
        allocated = item.get_allocated_sum() or 0

        if allocated <= planned:
            normal_allocated += allocated
        else:
            normal_allocated += planned
            over_allocated += allocated - planned

    total_allocated = normal_allocated
    total_spent = sum(item.spent_amount for item in estimate_items_for_calc)

    # Как у тебя: план по смете с учётом выделенного
    total_planned = total_planned_positive - total_allocated

    # --- МАРЖА (оставляю твою формулу) ---
    marja = (
        ((plan_prodaj + fakt_prodaj) - total_planned - total_allocated)
        - extra_allocated
    ) - over_allocated

    # --- КАТЕГОРИИ ДЛЯ ГРАФИКА ---
    categories = []
    for category in EstimateCategory.objects.all():
        category_total = sum(
            item.spent_amount for item in estimate_items if item.category == category
        )
        if category_total > 0:
            categories.append({
                'name': category.name,
                'total_spent': category_total
            })

    # ------------------------------------------------------------------
    #  ГРУППИРОВКА ПО КАТЕГОРИЯМ СМЕТЫ (EstimateCategory)
    # ------------------------------------------------------------------
    selected_category_id = request.GET.get('category', '').strip()

    # берём только те категории, которые реально есть у этого блока
    used_categories = (
        EstimateCategory.objects
        .filter(estimateitem__block=block)
        .distinct()
        .order_by('id')
    )

    category_groups = []
    for cat in used_categories:
        cat_items = [item for item in estimate_items if item.category_id == cat.id]
        if not cat_items:
            continue

        cat_total_planned = sum(i.planned_amount for i in cat_items)
        cat_total_allocated = sum(i.get_allocated_sum() or 0 for i in cat_items)
        cat_total_margin = sum(i.margin for i in cat_items)

        category_groups.append({
            'category': cat,
            'items': cat_items,
            'total_planned': cat_total_planned,
            'total_allocated': cat_total_allocated,
            'total_margin': cat_total_margin,
        })

    # ИТОГИ ПО ВСЕМ СМЕТАМ (НЕ ЗАВИСЯТ ОТ ФИЛЬТРА)
    table_total_planned = sum(i.planned_amount for i in estimate_items)
    table_total_allocated = sum(i.get_allocated_sum() or 0 for i in estimate_items)
    table_total_margin = sum(i.margin for i in estimate_items)

    from .forms import BlockPriceForm
    price_form = BlockPriceForm(instance=block)

    context = {
        "normal_allocated": normal_allocated,
        "over_allocated": over_allocated,
        'current_block': block,
        'estimate_items': estimate_items,
        'price_form': price_form,

        'total_planned': total_planned,      # для карточки "План по смете"
        'total_allocated': total_allocated,  # для карточки "Факт расходов"
        'total_planned2': total_planned2,
        'fakt_prodaj': fakt_prodaj,
        'plan_prodaj': plan_prodaj,
        'marja': marja,
        'total_planned_positive': total_planned_positive,
        'total_planned_negative': total_planned_negative,
        'extra_allocated': extra_allocated,
        'postupillo': postupillo,
        'total_spent': total_spent,
        'total_margin': total_margin_raw,
        'categories': categories,
        
        
        "extra_planned": extra_planned,
        
        "extra_spent": extra_spent,

        # НОВОЕ:
        'category_groups': category_groups,
        'selected_category_id': selected_category_id,
        'table_total_planned': table_total_planned,
        'table_total_allocated': table_total_allocated,
        'table_total_margin': table_total_margin,
    }
    return render(request, 'projects/block_detail.html', context)

# @login_required
# def block_detail(request, block_id):
#     block = get_object_or_404(Block, id=block_id)
#     estimate_items = block.estimate_items.all()
#     apartments = block.apartments.all()

#     # --- ПРОДАЖИ ---
#     plan_prodaj = apartments.filter(is_sold=False).aggregate(
#         Sum('planned_deal_amount')
#     )['planned_deal_amount__sum'] or 0

#     fakt_prodaj = apartments.filter(is_sold=True).aggregate(
#         Sum('deal_Fakt_deal_amount')
#     )['deal_Fakt_deal_amount__sum'] or 0

#     postupillo = block.received_amount

#     # --- БАЗОВЫЕ СУММЫ ПО ВСЕМ СТРОКАМ СМЕТЫ (без учёта категории 21) ---
#     estimate_items_for_calc = estimate_items.exclude(
#         category__name="21.Дополнительные расходы не входящие в смету"
#     )

#     # Для старых расчётов (если где-то используешь total_planned2 / total_margin)
#     total_planned_raw = sum(item.planned_amount for item in estimate_items)
#     total_allocated_raw = sum(item.get_allocated_sum() for item in estimate_items)
#     total_spent_raw = sum(item.spent_amount for item in estimate_items)
#     total_margin_raw = total_planned_raw - total_spent_raw
#     total_planned2 = total_planned_raw - total_allocated_raw

#     # --- ОТДЕЛЬНО КАТЕГОРИЯ 21 ---
#     extra_items = estimate_items.filter(
#         category__name="21.Дополнительные расходы не входящие в смету"
#     )

#     extra_allocated = sum(item.get_allocated_sum() for item in extra_items)
#     extra_planned = sum(item.planned_amount for item in extra_items)
#     extra_spent = sum(item.spent_amount for item in extra_items)

#     # --- ПЛАН ТОЛЬКО ПО ОСНОВНОЙ СМЕТЕ (без 21 категории) ---
#     total_planned = sum(item.planned_amount for item in estimate_items_for_calc)

#     # Сумма положительных / отрицательных planned_amount
#     total_planned_positive = sum(
#         item.planned_amount
#         for item in estimate_items_for_calc
#         if item.planned_amount > 0
#     )
#     total_planned_negative = sum(
#         item.planned_amount
#         for item in estimate_items_for_calc
#         if item.planned_amount < 0
#     )

#     # --- РАЗБИВКА: нормальные расходы и перерасход ---
#     normal_allocated = 0
#     over_allocated = 0

#     for item in estimate_items_for_calc:
#         planned = item.planned_amount or 0
#         allocated = item.get_allocated_sum() or 0

#         if allocated <= planned:
#             normal_allocated += allocated
#         else:
#             normal_allocated += planned
#             over_allocated += allocated - planned

#     # Для карточек "Факт расходов" используем normal_allocated
#     total_allocated = normal_allocated
#     total_spent = sum(item.spent_amount for item in estimate_items_for_calc)

#     # Пересчёт total_planned для карточки (как у тебя было)
#     total_planned = total_planned_positive - total_allocated

#     # --- МАРЖА (как у тебя, не трогаю формулу) ---
#     marja = (
#         ((plan_prodaj + fakt_prodaj) - total_planned - (total_allocated))
#         - extra_allocated
#     ) - over_allocated

#     # --- КАТЕГОРИИ ДЛЯ ГРАФИКА ---
#     categories = []
#     for category in EstimateCategory.objects.all():
#         category_total = sum(
#             item.spent_amount for item in estimate_items if item.category == category
#         )
#         if category_total > 0:
#             categories.append(
#                 {
#                     'name': category.name,
#                     'total_spent': category_total
#                 }
#             )

#     # ------------------------------------------------------------------
#     #  ГРУППИРОВКА ПО НОМЕРУ В НАЗВАНИИ (1.2, 4, 4,5,7 и т.п.)
#     # ------------------------------------------------------------------

#     # выбранная группа из GET (для фильтра)
#     selected_group = request.GET.get('group', '').strip()

#     # словарь: ключ = "номер" из начала названия, значение = данные группы
#     group_map = {}

#     for item in estimate_items:
#         name = item.name or ''
#         first_token = name.split()[0] if name else ''

#         # если название начинается с цифры — считаем это номером группы
#         if first_token and first_token[0].isdigit():
#             group_key = first_token.rstrip('.')  # "1." -> "1"
#         else:
#             group_key = 'Без номера'

#         if group_key not in group_map:
#             group_map[group_key] = {
#                 'items': [],
#                 'total_planned': Decimal('0'),
#                 'total_allocated': Decimal('0'),
#                 'total_margin': Decimal('0'),
#             }

#         grp = group_map[group_key]
#         grp['items'].append(item)
#         planned = item.planned_amount or 0
#         allocated = item.get_allocated_sum() or 0
#         margin = getattr(item, 'margin', None) or 0

#         grp['total_planned'] += planned
#         grp['total_allocated'] += allocated
#         grp['total_margin'] += margin

#     # функция сортировки групп: сначала числовые, потом текст
#     def group_sort_key(k: str):
#         if k and k[0].isdigit():
#             parts = re.split(r'[^0-9]+', k)
#             nums = [int(p) for p in parts if p]
#             return (0, nums)
#         return (1, k.lower())

#     estimate_groups = OrderedDict()
#     for key in sorted(group_map.keys(), key=group_sort_key):
#         estimate_groups[key] = group_map[key]

#     # ------------------------------------------------------------------
#     #  ИТОГ ПО ВСЕМ СМЕТАМ ДЛЯ НИЖНЕЙ СТРОКИ ТАБЛИЦЫ
#     #  (НЕ ЗАВИСИТ ОТ ФИЛЬТРА/ГРУПП)
#     # ------------------------------------------------------------------
#     table_total_planned = sum(item.planned_amount or 0 for item in estimate_items)
#     table_total_allocated = sum(item.get_allocated_sum() or 0 for item in estimate_items)
#     table_total_margin = sum(
#         (getattr(item, 'margin', None) or 0) for item in estimate_items
#     )

#     context = {
#         "normal_allocated": normal_allocated,
#         "over_allocated": over_allocated,
#         'current_block': block,
#         'estimate_items': estimate_items,  # если где-то ещё используешь
#         'total_planned': total_planned,
#         'total_allocated': total_allocated,
#         'total_planned2': total_planned2,
#         'fakt_prodaj': fakt_prodaj,
#         'plan_prodaj': plan_prodaj,
#         'marja': marja,
#         'total_planned_positive': total_planned_positive,
#         'total_planned_negative': total_planned_negative,
#         'extra_allocated': extra_allocated,
#         'postupillo': postupillo,
#         'total_spent': total_spent,
#         'total_margin': total_margin_raw,  # старый общий маржин по всем
#         'categories': categories,
#         "extra_planned": extra_planned,
#         "extra_spent": extra_spent,

#         # НОВОЕ:
#         'estimate_groups': estimate_groups,
#         'selected_group': selected_group,
#         'table_total_planned': table_total_planned,
#         'table_total_allocated': table_total_allocated,
#         'table_total_margin': table_total_margin,
#     }
#     return render(request, 'projects/block_detail.html', context)

# @login_required
# def block_detail(request, block_id):
#     block = get_object_or_404(Block, id=block_id)
#     estimate_items = block.estimate_items.all()
#     apartments = block.apartments.all()
    
#     plan_prodaj = apartments.filter( is_sold=False ).aggregate(Sum('planned_deal_amount'))['planned_deal_amount__sum'] or 0 
#     fakt_prodaj = apartments.filter( is_sold=True ).aggregate(Sum('deal_Fakt_deal_amount'))['deal_Fakt_deal_amount__sum'] or 0
#     postupillo = block.received_amount
#     # plan_prodaj = apartments.aggregate(total=Sum('planned_deal_amount'))['total'] or 0
#     # Добавляем расчет общих сумм для контекста
#     total_planned = sum(item.planned_amount for item in estimate_items)
#     total_allocated = sum(item.get_allocated_sum() for item in estimate_items)
#     total_spent = sum(item.spent_amount for item in estimate_items)
#     total_margin = total_planned - total_spent
#     total_planned2 = total_planned - total_allocated #+200
#      # исключаем категорию 21 "Дополнительные расходы не входящие в смету"
#     estimate_items_for_calc = estimate_items.exclude(category__name="21.Дополнительные расходы не входящие в смету")
#     # только категория 21
#     extra_items = estimate_items.filter(category__name="21.Дополнительные расходы не входящие в смету")
#     # extra_allocated = sum(item.get_allocated_sum() for item in extra_items)
#     extra_allocated = sum(item.get_allocated_sum() for item in extra_items)
#     extra_planned = sum(item.planned_amount for item in extra_items)
#     # extra_allocated = sum(item.get_allocated_sum() for item in extra_items)
#     extra_spent = sum(item.spent_amount for item in extra_items)
#     # считаем суммы только по оставшимся позициям
#     total_planned = sum(item.planned_amount for item in estimate_items_for_calc) 
#     # Сумма положительных planned_amount
#     total_planned_positive = sum(
#     item.planned_amount for item in estimate_items_for_calc if item.planned_amount > 0)

# # Сумма отрицательных planned_amount
#     total_planned_negative = sum(
#     item.planned_amount for item in estimate_items_for_calc if item.planned_amount < 0)
#     estimate_items_for_calc = estimate_items.exclude(category__name="21.Дополнительные расходы не входящие в смету")
#     normal_allocated = 0
#     over_allocated = 0

#     for item in estimate_items_for_calc:
#         planned = item.planned_amount or 0
#         allocated = item.get_allocated_sum() or 0

#         if allocated <= planned:
#         # всё ушло в нормальный расход
#             normal_allocated += allocated
#         else:
#         # часть в пределах плана, остальное — перерасход
#             normal_allocated += planned
#             over_allocated += allocated - planned

#     total_allocated = sum(item.get_allocated_sum() for item in estimate_items_for_calc)
#     total_allocated = normal_allocated
#     total_spent = sum(item.spent_amount for item in estimate_items_for_calc)
#     total_planned = total_planned_positive - total_allocated
#     # 2920000 2238980
#     # print((plan_prodaj+fakt_prodaj))
#     # total_allocated = total_allocated - 200
#     # Планируемые продажи plan_prodaj Факт сделок fakt_prodaj 
#     # План по смете total_planned2 Факт расходов total_allocated
#     marja = (((plan_prodaj+fakt_prodaj)-total_planned-(total_allocated)) -extra_allocated)- over_allocated #-200
#     # Группируем расходы по категориям для графика
    
#     categories = []
#     for category in EstimateCategory.objects.all():
#         category_total = sum(item.spent_amount for item in estimate_items if item.category == category)
#         if category_total > 0:
#             categories.append({
#                 'name': category.name,
#                 'total_spent': category_total
#             })
    
#     context = {
#         "normal_allocated": normal_allocated,
#     "over_allocated": over_allocated,
#         'current_block': block,
#         'estimate_items': estimate_items,
#         'total_planned': total_planned,
#         'total_allocated': total_allocated,
#         'total_planned2':total_planned2,
#         'fakt_prodaj':fakt_prodaj,
#         'plan_prodaj':plan_prodaj,
#         'marja':marja,
#         'total_planned_positive':total_planned_positive,
#         'total_planned_negative':total_planned_negative,
#         'extra_allocated':extra_allocated,
#         'postupillo':postupillo,
#         'total_spent': total_spent,
#         'total_margin': total_margin,
#         'categories': categories,
        
#         "extra_planned": extra_planned,
        
#         "extra_spent": extra_spent,
#     }
#     return render(request, 'projects/block_detail.html', context)
# @login_required
# def block_detail(request, block_id):
#     block = get_object_or_404(Block, id=block_id)
#     estimate_items = block.estimate_items.all()
    
#     context = {
#         'block': block,
#         'estimate_items': estimate_items,
#     }
#     return render(request, 'projects/block_detail.html', context)


@login_required
def apartment_list(request, block_id):
    block = Block.objects.get( id=block_id)
    blocks = Block.objects.get( id=block_id)
    apartments = block.apartments.all()
    # @property
    # def unsold_apartments_count(self):
    # @property
    # sold_area = block.apartments.aggregate(Sum('sold_area'))['sold_area__sum']
    # sold_area = block.apartments.aggregate(Sum('sold_area'))['sold_area__sum']
    area = apartments.aggregate(total=Sum('area'))['total'] or 0
    sold_areaM2 = apartments.filter(block=block, is_sold=True).aggregate(total=Sum('area'))['total'] or 0
    sold_area = apartments.filter(block=block,is_reserved=True, is_sold=False).aggregate(total=Sum('area'))['total'] or 0
    col_sum_apartments = apartments.filter(block=block, is_sold=True).count()
    obshie_col_apartments = apartments.filter(block=block).count()
        # return result if result else 0
    # calc_sold_area = block.apartments.aggregate(Sum('sold_area'))['sold_area__sum']
    #     return result if result else 0
    actual_deals_total = apartments.filter(block=block, is_sold=True).aggregate(Sum('deal_Fakt_deal_amount'))['deal_Fakt_deal_amount__sum']
        # return result if result else 0
    free_area = block.total_area - block.sold_area
    reserved_apartments_count = block.apartments.filter(is_reserved=True, is_sold=False).count()

    # Для аналитики бронь = свободная (не бартер = потенциальная продажа)
    free_qs = block.apartments.filter(is_sold=False, is_barter=False)
    unsold_apartments_count = free_qs.aggregate(total=Sum('area'))['total'] or 0
    unsold_apartments_count2 = free_qs.count()

    # Fallback цена: поле блока → средняя по проданным
    block_price = block.planned_price_per_m2 or 0
    if not block_price:
        block_price = apartments.filter(
            is_sold=True, planned_price_per_m2__gt=0
        ).aggregate(avg=Avg('planned_price_per_m2'))['avg'] or 0

    free_apts_data = free_qs.values('area', 'planned_price_per_m2')
    planned_deals_total = sum(
        (a['area'] or 0) * (a['planned_price_per_m2'] if a['planned_price_per_m2'] else block_price)
        for a in free_apts_data
    )
    remaining_deals_total = block.apartments.aggregate(Sum('remaining_deal_amount'))['remaining_deal_amount__sum']
    postipillo =  block.apartments.aggregate(total=Sum("deal_amount"))["total"] or 0
    context = {
        'block': block,
        'blocks':blocks,
        'sold_area':sold_area,
        'free_area':free_area,
        'area':area,
        'postipillo':postipillo,
        'obshie_col_apartments':obshie_col_apartments,
        'col_sum_apartments':col_sum_apartments,
        'sold_areaM2':sold_areaM2,
        'unsold_apartments_count2':unsold_apartments_count2,
        'remaining_deals_total':remaining_deals_total,
        'actual_deals_total':actual_deals_total,
        'planned_deals_total':planned_deals_total,
        'reserved_apartments_count':reserved_apartments_count,
        'unsold_apartments_count': unsold_apartments_count,
        'blockid':block_id,
        'apartments': apartments,
    }
    return render(request, 'projects/apartment_list.html', context)

from .forms import ApartmentCommentForm, DealPaymentEditForm, RentApartmentForm, RentPaymentEditForm, RentPaymentForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Apartment
@login_required
def apartment_detail(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    payments = apartment.payments.all().order_by('-payment_date')
    total_paid = payments.aggregate(total=Sum("amount"))["total"] or 0
    comments = apartment.comments.order_by("-created_at")  # последние сверху
    if request.method == "POST":
        form = ApartmentCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.apartment = apartment
            comment.save()
            messages.success(request, "Комментарий добавлен!")
            return redirect("projects:apartment_detail", apartment_id=apartment.id)
    else:
        form = ApartmentCommentForm()
    context = {
        'apartment': apartment,
        'payments': payments,
        'total_paid':total_paid,
        "form": form,
        "comments": comments,
    }
    return render(request, 'projects/apartment_detail.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Apartment
from .forms import ApartmentReservationForm

def reserve_apartment(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)

    if apartment.is_reserved:
        messages.warning(request, "Эта квартира уже забронирована!")
        return redirect("projects:apartment_detail", apartment_id=apartment.id)

    if request.method == "POST":
        form = ApartmentReservationForm(request.POST, instance=apartment)
        if form.is_valid():
            apt = form.save(commit=False)
            apt.is_reserved = True  # ставим галочку
            apt.save()
            messages.success(request, f"Квартира {apt.apartment_number} успешно забронирована на {apt.client_name}!")
            return redirect("projects:apartment_detail", apartment_id=apartment.id)
    else:
        form = ApartmentReservationForm(instance=apartment)

    return render(request, "projects/reserve_apartment.html", {
        "apartment": apartment,
        "form": form
    })


@login_required
def add_apartment(request, block_id):
    block = get_object_or_404(Block, id=block_id)
    
    if request.method == 'POST':
        form = ApartmentForm(request.POST)
        if form.is_valid():
            apartment = form.save(commit=False)
            apartment.block = block
            apartment.save()
            messages.success(request, 'Квартира успешно добавлена')
            return redirect('apartment_list', block_id=block.id)
    else:
        form = ApartmentForm()
    
    context = {
        'block': block,
        'form': form,
    }
    return render(request, 'projects/add_apartment.html', context)
from django.contrib import messages

@login_required
def add_payment(request, apartment_id):
    apartment = Apartment.objects.get(id=apartment_id)
    if request.method == 'POST':
        form = DealPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.apartment = apartment
            payment.created_by = request.user  # Сохраняем кто создал платеж
            messages.success(request, 'Платеж успешно добавлен')
            payment = form.save(commit=False)
            Sale.objects.create(
                 block = apartment.block,
                 area = 0,
                 apartment = apartment,
                 amount = payment.amount,
                 
                 client_info = f'{apartment.client_name}',
                 created_by = request.user
            )
            
            payment.apartment = apartment
            payment.save()
            messages.success(request, 'Платеж успешно добавлен')
            # return redirect('projects:apartment_detail', apartment_id=apartment.id)
            return redirect('projects:apartment_detail', apartment_id=apartment.id)
    else:
        form = DealPaymentForm(initial={'payment_date': timezone.now()})
    
    context = {
        'apartment': apartment,
        'form': form,
    }
    return render(request, 'projects/add_payment.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Apartment
from .forms import ApartmentSaleForm

def is_accountant_or_admin(user):
    return user.groups.filter(name__in=['Бухгалтер', 'Администратор']).exists() or user.is_superuser

@login_required
# @user_passes_test(is_accountant_or_admin, login_url='/accounts/login/')
def sell_apartment(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    
    if apartment.is_sold:
        messages.warning(request, 'Эта квартира уже продана!')
        return redirect('projects:apartment_list', apartment.block.id)
    
    if request.method == 'POST':
        form = ApartmentSaleForm(request.POST, instance=apartment)
        if form.is_valid():
            # Помечаем квартиру как проданную
            apartment = form.save(commit=False)  # берём объект, но пока не сохраняем
        
            apartment.is_sold = True
            fact_price = form.cleaned_data['fact_price_per_m2']
            apartment.fact_price_per_m2 = fact_price
            # apartment.fact_price_per_m2 = fact_price
            apartment.deal_Fakt_deal_amount = (apartment.area * fact_price) - (form.cleaned_data.get('discount') or 0)
            # apartment.deal_Fakt_deal_amount = full_price - 
        
            # apartment.save()  # 
            # apartment.is_sold = True
            
            
             
            apartment.remaining_deal_amount = apartment.deal_Fakt_deal_amount
            apartment.save()
            # Создаём запись в Sale
            # Sale.objects.create(
            #     block=apartment.block,
            #     area=apartment.area,
            #     amount=apartment.deal_Fakt_deal_amount,
            #     client_info=apartment.client_name,
            #     created_by=request.user,   # <<< кто создал сделку
            # )
#             sale = Sale(
#     block=apartment.block,
#     area=apartment.area,
#     amount=apartment.deal_Fakt_deal_amount,
#     client_info=form.cleaned_data['client_name'],
#     created_by=request.user  # 👈 сохраняем кто продал
# )
            # sale.save(user=request.user)  # 👈 передаём пользователя дальше

            messages.success(request, f'Квартира {apartment.apartment_number} успешно продана!')
            return redirect('projects:apartment_list', apartment.block.id)
    else:
        form = ApartmentSaleForm(instance=apartment)
    
    context = {
        'form': form,
        'apartment': apartment,
        'title': f'Продажа квартиры {apartment.apartment_number}'
    }
    
    return render(request, 'projects/sell_apartment.html', context)


# projects/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Block
from .forms import ApartmentCreateForm

@login_required
def apartment_add(request, block_id):
    block = get_object_or_404(Block, id=block_id)
    blocks = Block.objects.get(id=block_id)

    if request.method == "POST":
        form = ApartmentCreateForm(request.POST)
        if form.is_valid():
            apt = form.save(commit=False)
            apt.block = block            # <- автоматически привязываем блок
            # остальные поля уже имеют default/null в вашей модели
            apt.save()
            messages.success(request, f"Квартира {apt.apartment_number} добавлена в {block}.")
            return redirect("projects:apartment_list", block_id=block.id)
    else:
        form = ApartmentCreateForm()

    return render(request, "projects/apartment_add.html", {"form": form,
                                                           "block": block,
                                                           'blocks':blocks})


@login_required
def set_block_price(request, block_id):
    from .forms import BlockPriceForm
    block = get_object_or_404(Block, id=block_id)

    if request.method == "POST":
        form = BlockPriceForm(request.POST, instance=block)
        if form.is_valid():
            from django.db.models import F, ExpressionWrapper
            from django.db.models import DecimalField as DecF
            price = form.cleaned_data['planned_price_per_m2']
            form.save()
            # Обновляем цену для свободных + забронированных (бронь = потенц. продажа)
            updated = block.apartments.filter(
                is_sold=False, is_barter=False
            ).update(
                planned_price_per_m2=price,
                fact_price_per_m2=price,
                planned_deal_amount=ExpressionWrapper(
                    F('area') * price,
                    output_field=DecF(max_digits=15, decimal_places=2)
                ),
            )
            messages.success(
                request,
                f"Цена {price:,.0f} сом/м² сохранена. "
                f"Обновлено {updated} свободных квартир."
            )
        else:
            messages.error(request, "Ошибка при сохранении цены.")

    return redirect("projects:block_detail", block_id=block.id)


@login_required
def delete_block_apartments(request, block_id):
    block = get_object_or_404(Block, id=block_id)

    if request.method == "POST":
        confirm = request.POST.get("confirm")
        if confirm == "yes":
            deleted_count, _ = block.apartments.all().delete()
            messages.success(request, f"Удалено {deleted_count} квартир (и все связанные данные) из блока «{block.name}».")
        else:
            messages.warning(request, "Удаление отменено.")
        return redirect("projects:block_detail", block_id=block.id)

    return render(request, "projects/block_apartments_delete_confirm.html", {"apt_block": block})


from django.shortcuts import render, redirect, get_object_or_404
from .models import Block, EstimateItem
from .forms import EstimateItemForm

def add_estimate_item(request, block_id):
    block = get_object_or_404(Block, id=block_id)

    if request.method == "POST":
        form = EstimateItemForm(request.POST)
        if form.is_valid():
            estimate_item = form.save(commit=False)
            estimate_item.block = block   # автоматически присваиваем
            estimate_item.save()
            return redirect("projects:block_detail", block_id=block.id)  # например на страницу блока
    else:
        form = EstimateItemForm()

    return render(request, "projects/add_estimate_item.html", {
        "form": form,
        "block": block,
    })


from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden

def superuser_required(view_func):
    """Декоратор для проверки, что пользователь - суперпользователь"""
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='/admin/login/'
    )(view_func)
    return decorated_view_func

@login_required
@superuser_required
def edit_payment(request, payment_id):
    payment = get_object_or_404(DealPayment, id=payment_id)
    
    if request.method == 'POST':
        form = DealPaymentEditForm(request.POST, instance=payment)
        if form.is_valid():
            # Сохраняем, кто изменил платеж
            payment = form.save(commit=False)
            payment.updated_by = request.user
            payment.save()
            
            messages.success(request, 'Платеж успешно обновлен')
            return redirect('projects:apartment_detail', apartment_id=payment.apartment.id)
    else:
        form = DealPaymentEditForm(instance=payment)
    
    context = {
        'form': form,
        'payment': payment,
        'apartment': payment.apartment,
    }
    return render(request, 'projects/edit_payment.html', context)

@login_required
@superuser_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(DealPayment, id=payment_id)
    apartment_id = payment.apartment.id
    
    if request.method == 'POST':
        # Создаем запись в истории перед удалением
        from finances.models import CashFlow, CommonCash
        common_cash = CommonCash.objects.first()
        
        if common_cash:
            CashFlow.objects.create(
                common_cash=common_cash,
                flow_type='expense',  # Обратная операция - возврат средств
                amount=payment.amount,
                description=f"УДАЛЕНИЕ: Платеж за кв. {payment.apartment.apartment_number} ({payment.payment_date.strftime('%d.%m.%Y')})",
                block=payment.apartment.block,
                created_by=request.user
            )
        
        payment.delete()
        messages.success(request, 'Платеж успешно удален')
        return redirect('projects:apartment_detail', apartment_id=apartment_id)
    
    context = {
        'payment': payment,
    }
    return render(request, 'projects/delete_payment_confirm.html', context)


@login_required
def rent_apartment(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    
    if request.method == 'POST':
        form = RentApartmentForm(request.POST, instance=apartment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Информация об аренде обновлена')
            return redirect('projects:apartment_detail', apartment_id=apartment.id)
    else:
        form = RentApartmentForm(instance=apartment)
    
    context = {
        'apartment': apartment,
        'form': form,
    }
    return render(request, 'projects/rent_apartment.html', context)

@login_required
def add_rent_payment(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    
    if request.method == 'POST':
        form = RentPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.apartment = apartment
            payment.created_by = request.user
            payment.save()
            messages.success(request, 'Арендный платеж успешно добавлен')
            return redirect('projects:apartment_detail', apartment_id=apartment.id)
    else:
        form = RentPaymentForm()
    
    context = {
        'apartment': apartment,
        'form': form,
    }
    return render(request, 'projects/add_rent_payment.html', context)

@login_required
@superuser_required
def edit_rent_payment(request, payment_id):
    payment = get_object_or_404(RentPayment, id=payment_id)
    
    if request.method == 'POST':
        form = RentPaymentEditForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.updated_by = request.user
            payment.save()
            messages.success(request, 'Арендный платеж успешно обновлен')
            return redirect('projects:apartment_detail', apartment_id=payment.apartment.id)
    else:
        form = RentPaymentEditForm(instance=payment)
    
    context = {
        'form': form,
        'payment': payment,
        'apartment': payment.apartment,
    }
    return render(request, 'projects/edit_rent_payment.html', context)

@login_required
@superuser_required
def delete_rent_payment(request, payment_id):
    payment = get_object_or_404(RentPayment, id=payment_id)
    apartment_id = payment.apartment.id
    
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Арендный платеж успешно удален')
        return redirect('projects:apartment_detail', apartment_id=apartment_id)
    
    context = {
        'payment': payment,
    }
    return render(request, 'projects/delete_rent_payment_confirm.html', context)

