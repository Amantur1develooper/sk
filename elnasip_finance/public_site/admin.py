from django.contrib import admin
from .models import ConsultationRequest


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at", "is_processed")
    list_filter = ("is_processed", "created_at")
    search_fields = ("name", "phone", "email")
