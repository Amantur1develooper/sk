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
from django import forms
from .models import EstimateItem

class EstimateItemForm(forms.ModelForm):
    class Meta:
        model = EstimateItem
        exclude = ["block"]  # блок задаём во views

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
        fields = [ 'deal_number', 'discount', 'client_name','fact_price_per_m2']
        widgets = {
            
            'deal_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Номер сделки'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Скидка в сомах',
                'step': '0.01',
                'min': '0',
               
            }),
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ФИО клиента'
            }),
            'fact_price_per_m2': forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Цена за m²',
                'step': '0.01',   # шаг (например, можно вводить дробные значения)
            'min': '0'
                }),

            # 'fact_price_per_m2':forms.TextInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': 'Цена за m²'
            # }),
        }
        labels = {
            
            'deal_number': 'Номер сделки',
            'fact_price_per_m2':'Цена за m²',
            'discount': 'Скидка (сом)',
            'client_name': 'ФИО клиента',
        }
    


   
    
    
    
    
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


# projects/forms.py


class ApartmentCreateForm(forms.ModelForm):
    class Meta:
        model = Apartment
        # показываем только обязательные поля
        fields = ["apartment_number", "rooms", "area", "planned_price_per_m2",'floor']
        widgets = {
            "apartment_number": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Напр. 45А"
            }),
            "rooms": forms.NumberInput(attrs={
                "class": "form-control", "min": 0
            }),
            "area": forms.NumberInput(attrs={
                "class": "form-control", "step": "0.01", "min": 0
            }),
            "planned_price_per_m2": forms.NumberInput(attrs={
                "class": "form-control", "step": "0.01", "min": 0
            }),
            "floor": forms.NumberInput(attrs={"class": "form-control", "min": 1}),  # этаж
   
        }

    def clean(self):
        data = super().clean()
        # простые проверки > 0
        if data.get("rooms", 0) < 0:
            self.add_error("rooms", "Количество комнат не может быть отрицательным")
        if data.get("area", 0) <= 0:
            self.add_error("area", "Площадь должна быть больше 0")
        if data.get("planned_price_per_m2", 0) <= 0:
            self.add_error("planned_price_per_m2", "Планируемая цена м² должна быть больше 0")
        return data
