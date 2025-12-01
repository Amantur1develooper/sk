from datetime import timezone
from pyexpat.errors import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from projects.forms import ApartmentForm, DealPaymentForm
from finances.models import Allocation, CashFlow, CommonCash, Sale
from .models import Apartment, DealPayment, Project, Block, EstimateItem, EstimateCategory, RentPayment
from django.db.models import Sum

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


@login_required
def block_detail(request, block_id):
    block = get_object_or_404(Block, id=block_id)
    estimate_items = block.estimate_items.all()
    apartments = block.apartments.all()
    
    plan_prodaj = apartments.filter( is_sold=False ).aggregate(Sum('planned_deal_amount'))['planned_deal_amount__sum'] or 0 
    fakt_prodaj = apartments.filter( is_sold=True ).aggregate(Sum('deal_Fakt_deal_amount'))['deal_Fakt_deal_amount__sum'] or 0
    postupillo = block.received_amount
    # plan_prodaj = apartments.aggregate(total=Sum('planned_deal_amount'))['total'] or 0
    # Добавляем расчет общих сумм для контекста
    total_planned = sum(item.planned_amount for item in estimate_items)
    total_allocated = sum(item.get_allocated_sum() for item in estimate_items)
    total_spent = sum(item.spent_amount for item in estimate_items)
    total_margin = total_planned - total_spent
    total_planned2 = total_planned - total_allocated #+200
     # исключаем категорию 21 "Дополнительные расходы не входящие в смету"
    estimate_items_for_calc = estimate_items.exclude(category__name="21.Дополнительные расходы не входящие в смету")
    # только категория 21
    extra_items = estimate_items.filter(category__name="21.Дополнительные расходы не входящие в смету")
    # extra_allocated = sum(item.get_allocated_sum() for item in extra_items)
    extra_allocated = sum(item.get_allocated_sum() for item in extra_items)
    extra_planned = sum(item.planned_amount for item in extra_items)
    # extra_allocated = sum(item.get_allocated_sum() for item in extra_items)
    extra_spent = sum(item.spent_amount for item in extra_items)
    # считаем суммы только по оставшимся позициям
    total_planned = sum(item.planned_amount for item in estimate_items_for_calc) 
    # Сумма положительных planned_amount
    total_planned_positive = sum(
    item.planned_amount for item in estimate_items_for_calc if item.planned_amount > 0
)

# Сумма отрицательных planned_amount
    total_planned_negative = sum(
    item.planned_amount for item in estimate_items_for_calc if item.planned_amount < 0
)
    estimate_items_for_calc = estimate_items.exclude(category__name="21.Дополнительные расходы не входящие в смету")
    normal_allocated = 0
    over_allocated = 0

    for item in estimate_items_for_calc:
        planned = item.planned_amount or 0
        allocated = item.get_allocated_sum() or 0

        if allocated <= planned:
        # всё ушло в нормальный расход
            normal_allocated += allocated
        else:
        # часть в пределах плана, остальное — перерасход
            normal_allocated += planned
            over_allocated += allocated - planned

    total_allocated = sum(item.get_allocated_sum() for item in estimate_items_for_calc)
    total_allocated = normal_allocated
    total_spent = sum(item.spent_amount for item in estimate_items_for_calc)
    total_planned = total_planned_positive - total_allocated
    # 2920000 2238980
    # print((plan_prodaj+fakt_prodaj))
    # total_allocated = total_allocated - 200
    # Планируемые продажи plan_prodaj Факт сделок fakt_prodaj 
    # План по смете total_planned2 Факт расходов total_allocated
    marja = (((plan_prodaj+fakt_prodaj)-total_planned-(total_allocated)) -extra_allocated)- over_allocated #-200
    # Группируем расходы по категориям для графика
    
    categories = []
    for category in EstimateCategory.objects.all():
        category_total = sum(item.spent_amount for item in estimate_items if item.category == category)
        if category_total > 0:
            categories.append({
                'name': category.name,
                'total_spent': category_total
            })
    
    context = {
        "normal_allocated": normal_allocated,
    "over_allocated": over_allocated,
        'current_block': block,
        'estimate_items': estimate_items,
        'total_planned': total_planned,
        'total_allocated': total_allocated,
        'total_planned2':total_planned2,
        'fakt_prodaj':fakt_prodaj,
        'plan_prodaj':plan_prodaj,
        'marja':marja,
        'total_planned_positive':total_planned_positive,
        'total_planned_negative':total_planned_negative,
        'extra_allocated':extra_allocated,
        'postupillo':postupillo,
        'total_spent': total_spent,
        'total_margin': total_margin,
        'categories': categories,
        
        "extra_planned": extra_planned,
        
        "extra_spent": extra_spent,
    }
    return render(request, 'projects/block_detail.html', context)
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
    unsold_apartments_count = block.apartments.filter(is_sold=False, is_reserved=False).aggregate(total=Sum('area'))['total'] or 0
    unsold_apartments_count2 = block.apartments.filter(is_sold=False, is_reserved=False).count() or 0
    planned_deals_total = apartments.filter(block=block, is_reserved=False, is_sold=False).aggregate(Sum('planned_deal_amount'))['planned_deal_amount__sum'] or 0
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
    apartment = Apartment.objects.get( id=apartment_id)
    # apartment.planned_deal_amount = 0
    apartment.save()
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