from django import forms
from .models import CommonCash, Allocation, CashFlow
from projects.models import EstimateItem

class AllocationForm(forms.ModelForm):
    estimate_item = forms.ModelChoiceField(
        queryset=EstimateItem.objects.all(),
        label="Позиция сметы",
        help_text="Выберите объект, блок и статью сметы"
    )
    
    class Meta:
        model = Allocation
        fields = ['estimate_item', 'amount', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'amount': 'Сумма выделения',
            'description': 'Назначение',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Можно добавить фильтрацию для estimate_item если нужно
        self.fields['estimate_item'].queryset = EstimateItem.objects.select_related(
            'block', 'block__project', 'category'
        )