from django import forms
from .models import SalaryPayment


class SalaryPaymentForEmployeeForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ['payment_type', 'amount', 'period']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'period': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'payment_type': 'Тип выплаты',
            'amount': 'Сумма (сом)',
            'period': 'За период',
        }
