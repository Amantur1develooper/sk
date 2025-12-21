from django import forms
from .models import ConsultationRequest


class ConsultationRequestForm(forms.ModelForm):
    class Meta:
        model = ConsultationRequest
        fields = ("name", "phone", "email", "message")
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Ваше имя",
                "class": "form-control",
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "Номер телефона / WhatsApp",
                "class": "form-control",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Email (необязательно)",
                "class": "form-control",
            }),
            "message": forms.Textarea(attrs={
                "placeholder": "Кратко опишите вопрос",
                "rows": 4,
                "class": "form-control",
            }),
        }
        labels = {
            "name": "Имя",
            "phone": "Телефон / WhatsApp",
            "email": "Email",
            "message": "Комментарий",
        }
