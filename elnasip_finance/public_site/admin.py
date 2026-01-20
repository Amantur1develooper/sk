from django.contrib import admin
from .models import ConsultationRequest


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at", "is_processed")
    list_filter = ("is_processed", "created_at")
    search_fields = ("name", "phone", "email")

from django.contrib import admin
from .models import Project, ProjectImage, ProjectPlan


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


class ProjectPlanInline(admin.TabularInline):
    model = ProjectPlan
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("get_name", "status", "sort")
    prepopulated_fields = {"slug": ("name_ru",)}
    inlines = [ProjectImageInline, ProjectPlanInline]
