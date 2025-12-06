# projects/views.py
from django.shortcuts import render
from django.db.models import Q, Sum, Count
from .models import Apartment, Block, Project
from projects.apartments.forms import ApartmentFilterForm
# projects/views.py
import csv
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Q, Sum, Count

from .models import Apartment, Block, Project
def export_apartments_csv(qs):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="apartments.csv"'

    writer = csv.writer(response, delimiter=';')

    # Заголовки
    writer.writerow([
        'ЖК',
        'Блок',
        'Этаж',
        'Номер',
        'Комнат',
        'Площадь, m²',
        'План. цена m²',
        'Факт. цена m²',
        'Сделка, сом',
        'Статус',
        'Клиент / арендатор',
    ])

    for a in qs:
        if a.is_sold:
            status = 'Продана'
        elif a.is_reserved:
            status = 'Бронь'
        elif a.is_rented:
            status = 'Аренда'
        else:
            status = 'Свободна'

        client_or_tenant = a.client_name or a.tenant_name or ''

        writer.writerow([
            a.block.project.name if a.block and a.block.project else '',
            a.block.name if a.block else '',
            a.floor,
            a.apartment_number,
            a.rooms,
            a.area,
            a.planned_price_per_m2,
            a.fact_price_per_m2,
            a.deal_amount,
            status,
            client_or_tenant,
        ])

    return response

def apartment_list(request):
    qs = Apartment.objects.select_related(
        'block',
        'block__project',
    ).all()

    form = ApartmentFilterForm(request.GET or None)

    # Динамический queryset для блоков
    project_id = request.GET.get('project')
    if project_id:
        form.fields['block'].queryset = Block.objects.filter(project_id=project_id)
    else:
        form.fields['block'].queryset = Block.objects.all()

    if form.is_valid():
        cd = form.cleaned_data

        # ЖК
        if cd.get('project'):
            qs = qs.filter(block__project=cd['project'])

        # Блок
        if cd.get('block'):
            qs = qs.filter(block=cd['block'])

        # Статус
        status = cd.get('status')
        if status == 'free':
            qs = qs.filter(is_sold=False, is_reserved=False, is_rented=False)
        elif status == 'sold':
            qs = qs.filter(is_sold=True)
        elif status == 'reserved':
            qs = qs.filter(is_reserved=True, is_sold=False)
        elif status == 'rented':
            qs = qs.filter(is_rented=True)

        # Комнаты
        if cd.get('rooms_min') is not None:
            qs = qs.filter(rooms__gte=cd['rooms_min'])
        if cd.get('rooms_max') is not None:
            qs = qs.filter(rooms__lte=cd['rooms_max'])

        # Площадь
        if cd.get('area_min') is not None:
            qs = qs.filter(area__gte=cd['area_min'])
        if cd.get('area_max') is not None:
            qs = qs.filter(area__lte=cd['area_max'])

        # Планируемая цена m²
        if cd.get('price_min') is not None:
            qs = qs.filter(planned_price_per_m2__gte=cd['price_min'])
        if cd.get('price_max') is not None:
            qs = qs.filter(planned_price_per_m2__lte=cd['price_max'])

        # Этаж
        if cd.get('floor_min') is not None:
            qs = qs.filter(floor__gte=cd['floor_min'])
        if cd.get('floor_max') is not None:
            qs = qs.filter(floor__lte=cd['floor_max'])

        # Поиск по клиенту / арендатору / договору
        search = cd.get('client_search')
        if search:
            qs = qs.filter(
                Q(client_name__icontains=search) |
                Q(tenant_name__icontains=search) |
                Q(tenant_phone__icontains=search) |
                Q(deal_number__icontains=search) |
                Q(tenant_contract__icontains=search)
            )

        # Сортировка
        order = cd.get('order')
        if order:
            if order == '':
                qs = qs.order_by(
                    'block__project__name',
                    'block__name',
                    'floor',
                    'apartment_number',
                )
            else:
                qs = qs.order_by(order)
        else:
            qs = qs.order_by(
                'block__project__name',
                'block__name',
                'floor',
                'apartment_number',
            )
    else:
        qs = qs.order_by(
            'block__project__name',
            'block__name',
            'floor',
            'apartment_number',
        )

    # 👉 Если нажали "Экспорт в Excel" — сразу отдаем файл
    if request.GET.get('export') == 'csv':
        return export_apartments_csv(qs)

    # Статистика для шапки
    stats = qs.aggregate(
        total=Count('id'),
        sold=Count('id', filter=Q(is_sold=True)),
        free=Count('id', filter=Q(is_sold=False, is_reserved=False, is_rented=False)),
        total_area=Sum('area'),
        sold_area=Sum('sold_area'),
    )

    context = {
        'form': form,
        'apartments': qs,
        'stats': stats,
    }
    return render(request, 'projects/apartments_list.html', context)

# def apartment_list(request):
#     qs = Apartment.objects.select_related(
#         'block',
#         'block__project',
#     ).all()

#     # форма фильтров
#     form = ApartmentFilterForm(request.GET or None)

#     # динамический queryset для блоков
#     project_id = request.GET.get('project')
#     if project_id:
#         form.fields['block'].queryset = Block.objects.filter(project_id=project_id)
#     else:
#         form.fields['block'].queryset = Block.objects.all()

#     if form.is_valid():
#         cd = form.cleaned_data

#         # ЖК
#         if cd.get('project'):
#             qs = qs.filter(block__project=cd['project'])

#         # Блок
#         if cd.get('block'):
#             qs = qs.filter(block=cd['block'])

#         # Статус
#         status = cd.get('status')
#         if status == 'free':
#             qs = qs.filter(is_sold=False, is_reserved=False, is_rented=False)
#         elif status == 'sold':
#             qs = qs.filter(is_sold=True)
#         elif status == 'reserved':
#             qs = qs.filter(is_reserved=True, is_sold=False)
#         elif status == 'rented':
#             qs = qs.filter(is_rented=True)

#         # Комнаты
#         if cd.get('rooms_min') is not None:
#             qs = qs.filter(rooms__gte=cd['rooms_min'])
#         if cd.get('rooms_max') is not None:
#             qs = qs.filter(rooms__lte=cd['rooms_max'])

#         # Площадь
#         if cd.get('area_min') is not None:
#             qs = qs.filter(area__gte=cd['area_min'])
#         if cd.get('area_max') is not None:
#             qs = qs.filter(area__lte=cd['area_max'])

#         # Планируемая цена m²
#         if cd.get('price_min') is not None:
#             qs = qs.filter(planned_price_per_m2__gte=cd['price_min'])
#         if cd.get('price_max') is not None:
#             qs = qs.filter(planned_price_per_m2__lte=cd['price_max'])

#         # Этаж
#         if cd.get('floor_min') is not None:
#             qs = qs.filter(floor__gte=cd['floor_min'])
#         if cd.get('floor_max') is not None:
#             qs = qs.filter(floor__lte=cd['floor_max'])

#         # Поиск по клиенту / арендатору / договору
#         search = cd.get('client_search')
#         if search:
#             qs = qs.filter(
#                 Q(client_name__icontains=search) |
#                 Q(tenant_name__icontains=search) |
#                 Q(tenant_phone__icontains=search) |
#                 Q(deal_number__icontains=search) |
#                 Q(tenant_contract__icontains=search)
#             )

#         # Сортировка
#         order = cd.get('order')
#         if order:
#             # Особый вариант: сортировка по нескольким полям
#             if order == '':
#                 qs = qs.order_by(
#                     'block__project__name',
#                     'block__name',
#                     'floor',
#                     'apartment_number',
#                 )
#             else:
#                 qs = qs.order_by(order)
#         else:
#             qs = qs.order_by(
#                 'block__project__name',
#                 'block__name',
#                 'floor',
#                 'apartment_number',
#             )
#     else:
#         qs = qs.order_by(
#             'block__project__name',
#             'block__name',
#             'floor',
#             'apartment_number',
#         )

#     # Немного статистики для шапки
#     stats = qs.aggregate(
#         total=Count('id'),
#         sold=Count('id', filter=Q(is_sold=True)),
#         free=Count('id', filter=Q(is_sold=False, is_reserved=False, is_rented=False)),
#         total_area=Sum('area'),
#         sold_area=Sum('sold_area'),
#     )

#     context = {
#         'form': form,
#         'apartments': qs,
#         'stats': stats,
#     }
#     return render(request, 'projects/apartments_list.html', context)
