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
