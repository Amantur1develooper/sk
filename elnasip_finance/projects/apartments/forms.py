# projects/forms.py
from django import forms
from projects.models import Project, Block


class ApartmentFilterForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        label="ЖК"
    )
    block = forms.ModelChoiceField(
        queryset=Block.objects.none(),
        required=False,
        label="Блок"
    )

    status = forms.ChoiceField(
        required=False,
        label="Статус",
        choices=(
            ('', 'Все'),
            ('free', 'Свободные'),
            ('sold', 'Проданные'),
            ('reserved', 'В броне'),
            ('rented', 'Сданные в аренду'),
        )
    )

    rooms_min = forms.IntegerField(required=False, label="Комнат от")
    rooms_max = forms.IntegerField(required=False, label="Комнат до")

    area_min = forms.DecimalField(
        required=False, label="Площадь от",
        max_digits=10, decimal_places=2
    )
    area_max = forms.DecimalField(
        required=False, label="Площадь до",
        max_digits=10, decimal_places=2
    )

    price_min = forms.DecimalField(
        required=False, label="Цена m² от (план)",
        max_digits=10, decimal_places=2
    )
    price_max = forms.DecimalField(
        required=False, label="Цена m² до (план)",
        max_digits=10, decimal_places=2
    )

    floor_min = forms.IntegerField(required=False, label="Этаж от")
    floor_max = forms.IntegerField(required=False, label="Этаж до")

    client_search = forms.CharField(
        required=False,
        label="Клиент / телефон / договор"
    )

    order = forms.ChoiceField(
        required=False,
        label="Сортировка",
        choices=(
            ('', 'По проекту / блоку / номеру'),
            ('area', 'Площадь ↑'),
            ('-area', 'Площадь ↓'),
            ('planned_price_per_m2', 'План. цена m² ↑'),
            ('-planned_price_per_m2', 'План. цена m² ↓'),
            ('fact_price_per_m2', 'Факт. цена m² ↑'),
            ('-fact_price_per_m2', 'Факт. цена m² ↓'),
        )
    )
