
from django.shortcuts import render, redirect

from django.contrib import messages

from .forms import ConsultationRequestForm


def home_view(request):
    # пока статические данные-заглушки, потом можно заменить на модели
    objects_preview = [
        {
            "name": "Эко Парк",
            "tag": "Старт продаж",
            "desc": "Современный жилой комплекс рядом с парком. 1–4 комнатные квартиры.",
            "status": "Строится",
        },
        {
            "name": "City Residence",
            "tag": "Скоро",
            "desc": "Дом бизнес-класса в центре города. Подходит для жизни и инвестиций.",
            "status": "Проектирование",
        },
        {
            "name": "Family House",
            "tag": "Рассрочка",
            "desc": "Спокойный семейный квартал с детскими площадками и парковками.",
            "status": "В продаже",
        },
    ]

    advantages = [
        ("🏗️", "Собственная строительная компания", "Контролируем все этапы: от проекта до сдачи дома."),
        ("📍", "Локации в перспективных районах", "Рядом парки, школы, сады и транспорт."),
        ("📑", "Рассрочка и партнёрские банки", "Гибкие условия для покупателей и инвесторов."),
        ("🤝", "Прозрачность и сопровождение", "Помощь с документами и консультации на каждом шаге."),
    ]

    gallery_items = [
        "Первый фасад",
        "Внутренний двор",
        "Холл и подъезд",
        "Детская площадка",
        "Вид с террасы",
        "Ночной вид",
    ]

    context = {
        "objects_preview": objects_preview,
        "advantages": advantages,
        "gallery_items": gallery_items,
    }
    return render(request, "public_site/home.html", context)


def contacts_view(request):
    if request.method == "POST":
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            form.save()
   
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
        
        "office_address": "г. Ош, офис продаж Эл Насип",
   
    }
    return render(request, "public_site/contacts.html", context)
