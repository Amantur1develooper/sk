# from django import forms
# from .models import CommonCash, Allocation, CashFlow
# from projects.models import EstimateItem
# forms.py
from django import forms
from django_select2.forms import ModelSelect2Widget
from .models import Allocation
from projects.models import EstimateItem, Block
# forms.py
from django_select2.forms import ModelSelect2Widget
class AllocationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        block_id = kwargs.pop('block_id', None)
        super().__init__(*args, **kwargs)
        
        if block_id:
            self.fields['estimate_item'].queryset = EstimateItem.objects.filter(block_id=block_id)
        else:
            self.fields['estimate_item'].queryset = EstimateItem.objects.none()

    class Meta:
        model = Allocation
        fields = ['estimate_item', 'amount', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
# class AllocationForm(forms.ModelForm):
#     estimate_item = forms.ModelChoiceField(
#         queryset=EstimateItem.objects.select_related('block', 'block__project', 'category'),
#         label="Позиция сметы",
#         widget=ModelSelect2Widget(
#             model=EstimateItem,
#             search_fields=[
#                 "name__icontains",
#                 "block__name__icontains",
#                 "category__name__icontains"
#             ],
#             attrs={"data-placeholder": "Начните вводить позицию сметы..."}
#         ),
#         help_text="Можно искать по названию, блоку и категории"
#     )

#     class Meta:
#         model = Allocation
#         fields = ['estimate_item', 'amount', 'description']
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 3}),
#         }


# class AllocationForm(forms.ModelForm):
#     estimate_item = forms.ModelChoiceField(
#         queryset=EstimateItem.objects.all(),
#         label="Позиция сметы",
#         help_text="Выберите объект, блок и статью сметы"
#     )
    
#     class Meta:
#         model = Allocation
#         fields = ['estimate_item', 'amount', 'description']
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 3}),
#         }
#         labels = {
#             'amount': 'Сумма выделения',
#             'description': 'Назначение',
#         }
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Можно добавить фильтрацию для estimate_item если нужно
#         self.fields['estimate_item'].queryset = EstimateItem.objects.select_related(
#             'block', 'block__project', 'category'
#         )