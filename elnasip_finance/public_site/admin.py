from django.contrib import admin
from .models import ConsultationRequest


# @admin.register(ConsultationRequest)
# class ConsultationRequestAdmin(admin.ModelAdmin):
#     list_display = ("name", "phone", "created_at", "is_processed")
#     list_filter = ("is_processed", "created_at")
#     search_fields = ("name", "phone", "email")

from django.contrib import admin
from .models import Project, ProjectImage, ProjectPlan


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


class ProjectPlanInline(admin.TabularInline):
    model = ProjectPlan
    extra = 1


# @admin.register(Project)
# class ProjectAdmin(admin.ModelAdmin):
#     list_display = ("get_name", "status", "sort")
#     prepopulated_fields = {"slug": ("name_ru",)}
#     inlines = [ProjectImageInline, ProjectPlanInline]

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    ConsultationRequest,
    Project,
    ProjectImage,
    ProjectPlan,
    Apartment,   # если ещё не добавлял модель Apartment — убери эту строку и блок ниже
)


# ---------------------------
# Helpers (превью картинок)
# ---------------------------
def img_preview(url: str, w: int = 120, h: int = 80):
    if not url:
        return "-"
    return format_html(
        '<img src="{}" style="width:{}px;height:{}px;object-fit:cover;border-radius:10px;border:1px solid #ddd;" />',
        url, w, h
    )


# ---------------------------
# ConsultationRequest
# ---------------------------
@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at", "is_processed")
    list_filter = ("is_processed", "created_at")
    search_fields = ("name", "phone", "email")
    readonly_fields = ("created_at",)
    list_per_page = 25

    actions = ("mark_processed", "mark_unprocessed")

    @admin.action(description=_("Отметить как обработанные"))
    def mark_processed(self, request, queryset):
        queryset.update(is_processed=True)

    @admin.action(description=_("Снять отметку обработки"))
    def mark_unprocessed(self, request, queryset):
        queryset.update(is_processed=False)


# ---------------------------
# Project inlines
# ---------------------------
class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 0
    fields = ("preview", "image", "title_ru", "title_ky", "title_en", "sort")
    readonly_fields = ("preview",)
    ordering = ("sort", "id")

    def preview(self, obj):
        return img_preview(obj.image.url if obj.image else "")
    preview.short_description = _("Превью")


class ProjectPlanInline(admin.TabularInline):
    model = ProjectPlan
    extra = 0
    fields = ("block", "preview", "image", "title_ru", "title_ky", "title_en", "sort")
    readonly_fields = ("preview",)
    ordering = ("block", "sort", "id")

    def preview(self, obj):
        return img_preview(obj.image.url if obj.image else "")
    preview.short_description = _("Превью")


# ---------------------------
# Project
# ---------------------------
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [ProjectImageInline, ProjectPlanInline]

    list_display = (
        "id",
        "preview",
        "name_ru",
        "status",
        "blocks_count",
        "apartments_count",
        "sort",
    )
    list_filter = (
        "status",
        "has_smart_home",
        "has_boiler_house",
        "has_own_park",
        "has_lake",
    )
    search_fields = ("name_ru", "name_ky", "name_en", "slug")
    ordering = ("sort", "id")
    list_editable = ("sort", "status")
    prepopulated_fields = {"slug": ("name_ru",)}

    fieldsets = (
        (_("Основное"), {
            "fields": ("slug", "status", "sort", "hero_image", "pdf")
        }),
        (_("Название и слоган"), {
            "fields": (
                ("name_ru", "name_ky", "name_en"),
                ("tagline_ru", "tagline_ky", "tagline_en"),
            )
        }),
        (_("Описание"), {
            "fields": (
                ("about_ru", "about_ky", "about_en"),
                ("advantages_ru", "advantages_ky", "advantages_en"),
            )
        }),
        (_("Цифры"), {
            "fields": (
                ("blocks_count", "plot_area_m2"),
                ("apartments_count", "underground_parking"),
                ("guest_parking", "building_density_percent"),
            )
        }),
        (_("Фишки"), {
            "fields": (
                ("has_smart_home", "has_boiler_house"),
                ("has_own_park", "has_lake"),
            )
        }),
        (_("Офис продаж / Контакты"), {
            "fields": (
                ("sales_address_ru", "sales_address_ky", "sales_address_en"),
                "phones",
            )
        }),
    )

    def preview(self, obj):
        return img_preview(obj.hero_image.url if obj.hero_image else "", 110, 70)
    preview.short_description = _("Обложка")


# ---------------------------
# Apartment (если есть модель)
# ---------------------------
@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "number",
        "block",
        "rooms",
        "area_m2",
        "floor",
        "delivery_year",
        "status",
        "kind",
        "price_usd",
        "installment_from_usd",
    )
    list_filter = ("project", "status", "kind", "rooms", "delivery_year")
    search_fields = ("number", "block", "project__name_ru", "project__slug")
    ordering = ("sort", "-id")
    # list_editable = ("sort",)
    list_per_page = 25

    fieldsets = (
        (_("Связь"), {
            "fields": ("project", "sort")
        }),
        (_("Параметры"), {
            "fields": (
                ("number", "block"),
                ("rooms", "area_m2", "floor"),
                ("delivery_year", "status", "kind"),
            )
        }),
        (_("Цена / Рассрочка"), {
            "fields": (
                ("price_usd",),
                ("installment_from_usd", "installment_months"),
            )
        }),
        (_("Фото (3 шт.)"), {
            "fields": (
                ("img_plan", "preview_plan"),
                ("img_inside", "preview_inside"),
                ("img_top", "preview_top"),
            )
        }),
    )

    readonly_fields = ("preview_plan", "preview_inside", "preview_top")

    def preview_plan(self, obj):
        return img_preview(obj.img_plan.url if obj.img_plan else "", 140, 100)
    preview_plan.short_description = _("План (превью)")

    def preview_inside(self, obj):
        return img_preview(obj.img_inside.url if obj.img_inside else "", 140, 100)
    preview_inside.short_description = _("Квартира (превью)")

    def preview_top(self, obj):
        return img_preview(obj.img_top.url if obj.img_top else "", 140, 100)
    preview_top.short_description = _("Вид сверху (превью)")
