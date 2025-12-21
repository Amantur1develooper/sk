from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import ConsultationRequestForm


def contacts_view(request):
    if request.method == "POST":
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            form.save()
            # тут потом добавим отправку в Telegram / email
            messages.success(
                request,
                "Спасибо! Ваша заявка на консультацию отправлена. Мы свяжемся с вами в ближайшее время."
            )
            return redirect("public_site:contacts")
    else:
        form = ConsultationRequestForm()

    context = {
        "form": form,
        "phone_display": "+996 558 333 200",
        "phone_raw": "+996558333200",
        "whatsapp_link": "http://wa.me/996558333200",
        "telegram_link": "https://t.me/elnasip",
        "instagram_link": "https://www.instagram.com/elnasip_stroy?igsh=ZTIybXV1bHVxd3Yy",
        "threads_link": "https://www.threads.com/@elnasip_stroy?igshid=NTc4MTIwNjQ2YQ==",
        # пример адреса — поменяешь на свой
        "office_address": "г. Ош, офис продаж Эл Насип",
        # сюда потом можно вставить точные координаты для карты
    }
    return render(request, "public_site/contacts.html", context)
