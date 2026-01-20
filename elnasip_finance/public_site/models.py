from django.db import models

# Create your models here.
from django.db import models


class ConsultationRequest(models.Model):
    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон / WhatsApp", max_length=30)
    email = models.EmailField("Email", blank=True, null=True)
    message = models.TextField("Комментарий", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    is_processed = models.BooleanField("Обработана", default=False)

    class Meta:
        verbose_name = "Заявка на консультацию"
        verbose_name_plural = "Заявки на консультацию"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} ({self.phone})"



from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


class Project(models.Model):
    class Status(models.TextChoices):
        SALES = "sales", _("В продаже")
        BUILDING = "building", _("Строится")
        DESIGN = "design", _("Проект")
        DONE = "done", _("Сдан")

    slug = models.SlugField(unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BUILDING)

    name_ru = models.CharField(max_length=120)
    name_ky = models.CharField(max_length=120, blank=True)
    name_en = models.CharField(max_length=120, blank=True)

    tagline_ru = models.CharField(max_length=220, blank=True)
    tagline_ky = models.CharField(max_length=220, blank=True)
    tagline_en = models.CharField(max_length=220, blank=True)

    about_ru = models.TextField(blank=True)
    about_ky = models.TextField(blank=True)
    about_en = models.TextField(blank=True)

    # каждый пункт с новой строки (мы превратим в список)
    advantages_ru = models.TextField(blank=True)
    advantages_ky = models.TextField(blank=True)
    advantages_en = models.TextField(blank=True)

    hero_image = models.ImageField(upload_to="public_site/projects/hero/", blank=True)
    pdf = models.FileField(upload_to="public_site/projects/pdfs/", blank=True)

    # цифры
    blocks_count = models.PositiveIntegerField(null=True, blank=True)
    plot_area_m2 = models.PositiveIntegerField(null=True, blank=True)
    apartments_count = models.PositiveIntegerField(null=True, blank=True)
    underground_parking = models.PositiveIntegerField(null=True, blank=True)
    guest_parking = models.PositiveIntegerField(null=True, blank=True)
    building_density_percent = models.PositiveIntegerField(null=True, blank=True)

    # флаги
    has_smart_home = models.BooleanField(default=False)
    has_boiler_house = models.BooleanField(default=False)
    has_own_park = models.BooleanField(default=False)
    has_lake = models.BooleanField(default=False)

    # контакты для проекта/офиса продаж (если нужно)
    sales_address_ru = models.CharField(max_length=220, blank=True)
    sales_address_ky = models.CharField(max_length=220, blank=True)
    sales_address_en = models.CharField(max_length=220, blank=True)
    phones = models.CharField(max_length=200, blank=True, help_text="через запятую")

    sort = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort", "id"]

    def __str__(self):
        return self.get_name()

    def _t(self, base: str) -> str:
        lang = (get_language() or "ru")[:2]
        val = getattr(self, f"{base}_{lang}", "") or getattr(self, f"{base}_ru", "")
        return val or ""

    def get_name(self): return self._t("name")
    def get_tagline(self): return self._t("tagline")
    def get_about(self): return self._t("about")
    def get_sales_address(self): return self._t("sales_address")

    def get_advantages_list(self):
        text = self._t("advantages")
        return [line.strip() for line in text.splitlines() if line.strip()]


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="public_site/projects/gallery/")
    title_ru = models.CharField(max_length=120, blank=True)
    title_ky = models.CharField(max_length=120, blank=True)
    title_en = models.CharField(max_length=120, blank=True)
    sort = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort", "id"]

    def _t(self, base: str) -> str:
        lang = (get_language() or "ru")[:2]
        return getattr(self, f"{base}_{lang}", "") or getattr(self, f"{base}_ru", "")

    def get_title(self): return self._t("title")


class ProjectPlan(models.Model):
    class Block(models.TextChoices):
        AB = "ab", "A/Б"
        V = "v", "В"
        G = "g", "Г"
        OTHER = "other", _("Другое")

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="plans")
    block = models.CharField(max_length=20, choices=Block.choices, default=Block.OTHER)
    image = models.ImageField(upload_to="public_site/projects/plans/")
    title_ru = models.CharField(max_length=160, blank=True)
    title_ky = models.CharField(max_length=160, blank=True)
    title_en = models.CharField(max_length=160, blank=True)
    sort = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["block", "sort", "id"]

    def _t(self, base: str) -> str:
        lang = (get_language() or "ru")[:2]
        return getattr(self, f"{base}_{lang}", "") or getattr(self, f"{base}_ru", "")

    def get_title(self): return self._t("title")
