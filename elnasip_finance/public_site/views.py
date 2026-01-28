
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .forms import ConsultationRequestForm
from django.shortcuts import render, redirect
from .forms import ConsultationRequestForm


def home_view(request):
    # 3 проекта (третьему пока поставь заглушку — потом переименуешь)
    projects = [
        {
            "slug": "eco-park",
            "name": _("Эко Парк"),
            "badge": _("4 блока"),
            "status": _("Строится"),
            "image": "public_site/img/projects/eco-park/cover.png",
            "short": "Закрытый двор, зелёные зоны, семейная инфраструктура.",
        },
        {
            "slug": "nasip-k",
            "name": "Насип",
            "badge": "К блок",
            "status": "В продаже",
            "image": "public_site/img/projects/nasip-k/cover.png",
            "short": "Удобные планировки, современный фасад, развитый район.",
        },
        {
            "slug": "elnasip-3",
            "name": "Эл Насип 3",
            "badge": "Скоро",
            "status": "Анонс",
            "image": "public_site/img/projects/elnasip-3/cover.png",
            "short": "Новый проект. Подробности уточняйте у менеджера.",
        },
    ]

    # Слайды карусели: 1 общий + 3 по проектам (можно менять тексты)
    hero_slides = [
        {
            "badge": "Эл Насип · строительная компания",
            "title": "Жилые комплексы нового уровня в Оше",
            "sub": "Рассрочка до 36 месяцев. Помощь в ипотеке. Сопровождение сделки.",
            "image": "public_site/img/hero/hero1.png",
            "primary": {"text": "Смотреть проекты", "href": "#objects"},
            "secondary": {"text": "Консультация", "href": "/contacts/"},
        },
        {
            "badge": "Эко Парк · 4 блока",
            "title": "Просторные дворы и зелёные зоны",
            "sub": "Комфорт для семьи и выгодно для инвестиций.",
            "image": "public_site/img/hero/hero2.png",
            "primary": {"text": "Эко Парк", "href": "/contacts/?project=eco-park"},
            "secondary": {"text": "Галерея", "href": "#gallery"},
        },
        {
            "badge": "Насип · К блок",
            "title": "Современная архитектура и удобные планировки",
            "sub": "Подберём этаж, площадь и вариант оплаты.",
            "image": "public_site/img/hero/hero3.png",
            "primary": {"text": "Насип (К блок)", "href": "/contacts/?project=nasip-k"},
            "secondary": {"text": "Условия оплаты", "href": "#installment"},
        },
        {
            "badge": "Эл Насип 3 · скоро",
            "title": "Новый проект — старт анонса",
            "sub": "Оставьте заявку — сообщим первым о старте продаж.",
            "image": "public_site/img/hero/hero4.png",
            "primary": {"text": "Оставить заявку", "href": "/contacts/?project=elnasip-3"},
            "secondary": {"text": "Контакты", "href": "/contacts/"},
        },
    ]

    # Галерея (пока можно 6-8 картинок)
    gallery_images = [
        "public_site/img/gallery/1.png",
        "public_site/img/gallery/2.png",
        "public_site/img/gallery/3.png",
        "public_site/img/gallery/4.png",
        "public_site/img/gallery/5.png",
        "public_site/img/gallery/6.png",
    ]

    context = {
        "projects": projects,
        "hero_slides": hero_slides,
        "gallery_images": gallery_images,
    }
    return render(request, "public_site/home.html", context)


def contacts_view(request):
    # Автоподстановка текста по проекту
    project = request.GET.get("project")
    initial = {}
    if project:
        initial["message"] = f"Здравствуйте! Хочу консультацию по проекту: {project}"

    if request.method == "POST":
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Спасибо! Заявка отправлена. Мы свяжемся с вами в ближайшее время.")
            return redirect("public_site:contacts")
    else:
        form = ConsultationRequestForm(initial=initial)

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
from django.shortcuts import render, get_object_or_404
from .models import Project


def objects_list_view(request):
    projects = Project.objects.all()
    status = request.GET.get("status")
    qs = Project.objects.all()
    if status:
        qs = qs.filter(status=status)
    return render(request, "public_site/objects_list.html", {"projects": qs})


def project_detail_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    images = project.images.all()
    plans = project.plans.all()
    return render(
        request,
        "public_site/project_detail.html",
        {"project": project, "images": images, "plans": plans},
    )


from django.views.generic import ListView, DetailView
from .models import Apartment, Project
from django.views.generic import ListView
from .models import Apartment

class ApartmentsListView(ListView):
    model = Apartment
    template_name = "public_site/apartments_list.html"
    context_object_name = "apartments"
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().select_related("project")

        rooms = self.request.GET.getlist("rooms")  # ['1','2']
        if rooms:
            qs = qs.filter(rooms__in=rooms)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ВАЖНО: тут готовый список для шаблона
        ctx["selected_rooms"] = self.request.GET.getlist("rooms")

        return ctx


class ApartmentDetailView(DetailView):
    model = Apartment
    template_name = "public_site/apartment_detail.html"
    context_object_name = "a"
apartments_list = ApartmentsListView.as_view()
apartment_detail = ApartmentDetailView.as_view()
