from django import forms
from .models import Apartment, DealPayment

class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = [
            'floor', 'apartment_number', 'rooms', 'area', 
            'planned_price_per_m2', 'discount',
            'is_reserved', 'client_name'
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={'placeholder': 'ФИО клиента'}),
        }

class DealPaymentForm(forms.ModelForm):
    class Meta:
        model = DealPayment
        fields = ['amount', 'payment_date', 'comment']
        widgets = {
            'payment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


from django import forms
from .models import Apartment

class ApartmentSaleForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ['deal_Fakt_deal_amount', 'deal_number', 'discount', 'client_name','fact_price_per_m2']
        widgets = {
            'deal_Fakt_deal_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Фактическая сумма сделки'
            }),
            'deal_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Номер сделки'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Скидка в %',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ФИО клиента'
            }),
            'fact_price_per_m2':forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Цена за m²'
            }),
        }
        labels = {
            'deal_Fakt_deal_amount': 'Фактическая сумма сделки',
            'deal_number': 'Номер сделки',
            'fact_price_per_m2':'Цена за m²',
            'discount': 'Скидка (%)',
            'client_name': 'ФИО клиента',
        }
    
    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is not None and (discount < 0 or discount > 100):
            raise forms.ValidationError("Скидка должна быть между 0 и 100%")
        return discount

    def clean_deal_Fakt_deal_amount(self):
        deal_amount = self.cleaned_data.get('deal_Fakt_deal_amount')
        if deal_amount is not None and deal_amount <= 0:
            raise forms.ValidationError("Сумма сделки должна быть положительной")
        return deal_amount
    
    
    
    
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Apartment
from .forms import ApartmentSaleForm

def is_accountant_or_admin(user):
    return user.groups.filter(name__in=['Бухгалтер', 'Администратор']).exists() or user.is_superuser

# @login_required
# # @user_passes_test(is_accountant_or_admin, login_url='/accounts/login/')
# def sell_apartment(request, apartment_id):
#     apartment = get_object_or_404(Apartment, id=apartment_id)
    
#     if apartment.is_sold:
#         messages.warning(request, 'Эта квартира уже продана!')
#         return redirect('apartment_list')
    
#     if request.method == 'POST':
#         form = ApartmentSaleForm(request.POST, instance=apartment)
#         if form.is_valid():
#             # Помечаем квартиру как проданную
#             apartment.is_sold = True
#             apartment = form.save()
            
#             # Если указана скидка, пересчитываем сумму сделки
#             if apartment.discount and apartment.deal_Fakt_deal_amount:
#                 # Вычисляем сумму без скидки
#                 original_amount = apartment.deal_Fakt_deal_amount / (1 - apartment.discount / 100)
#                 apartment.deal_amount = original_amount
#                 apartment.save()
            
#             messages.success(request, f'Квартира {apartment.apartment_number} успешно продана!')
#             return redirect('apartment_list')
#     else:
#         form = ApartmentSaleForm(instance=apartment)
    
#     context = {
#         'form': form,
#         'apartment': apartment,
#         'title': f'Продажа квартиры {apartment.apartment_number}'
#     }
    
#     return render(request, 'projects/sell_apartment.html', context)