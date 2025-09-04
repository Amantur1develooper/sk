from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class ReportTemplate(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название отчета")
    description = models.TextField(verbose_name="Описание")
    model_name = models.CharField(max_length=100, verbose_name="Модель данных")
    fields = models.TextField(verbose_name="Поля для отображения")
    filters = models.TextField(blank=True, verbose_name="Фильтры")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Шаблон отчета"
        verbose_name_plural = "Шаблоны отчетов"

class SavedReport(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название отчета")
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name="Шаблон")
    parameters = models.TextField(verbose_name="Параметры отчета")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='reports/', blank=True, null=True, verbose_name="Файл отчета")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Сохраненный отчет"
        verbose_name_plural = "Сохраненные отчеты"