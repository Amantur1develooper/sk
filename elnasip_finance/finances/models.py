from django.db import models
from projects.models import Project, Block, EstimateItem
from django.contrib.auth.models import User

class CommonCash(models.Model):
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Баланс")
    
    def __str__(self):
        return f"Общаг: {self.balance}"
    
    class Meta:
        verbose_name = "Общаг (Главная касса)"
        verbose_name_plural = "Общаг (Главная касса)"

class CashFlow(models.Model):
    FLOW_TYPES = (
        ('income', 'Приход'),
        ('expense', 'Расход'),
    )
    
    common_cash = models.ForeignKey(CommonCash, on_delete=models.CASCADE, related_name='cash_flows')
    flow_type = models.CharField(max_length=10, choices=FLOW_TYPES, verbose_name="Тип операции")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма")
    description = models.TextField(verbose_name="Описание")
    block = models.ForeignKey(Block, on_delete=models.SET_NULL, null=True, blank=True, related_name="cash_flows")
    date = models.DateTimeField(auto_now_add=True)
    # is_zp = 
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        # Обновляем баланс при сохранении операции
        if not self.pk:  # Если это новая запись
            if self.flow_type == 'income':
                self.common_cash.balance += self.amount
            elif 'Премия' in self.description:
                 self.common_cash.balance -= self.amount
            elif "Бонус" in self.description or "Аванс " in self.description or "Зарплата " in self.description:
                pass
            else:
                self.common_cash.balance -= self.amount
            self.common_cash.save()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_flow_type_display()}: {self.amount} - {self.description}"
    
    class Meta:
        verbose_name = "Движение денег"
        verbose_name_plural = "Движения денег"

class Allocation(models.Model):
    common_cash = models.ForeignKey(CommonCash, default=1, on_delete=models.CASCADE, related_name='allocations')
    estimate_item = models.ForeignKey(EstimateItem, on_delete=models.CASCADE, null=True, blank=True, related_name='allocations', verbose_name="Позиция сметы")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма")
    description = models.TextField(verbose_name="Назначение")
    date = models.DateTimeField(auto_now_add=True)
    
    # def save(self, *args, **kwargs):
        # При выделении средств уменьшаем баланс Общага
        # if not self.pk :  # Если это новая запись
        #     self.common_cash.balance -= self.amount
        #     self.common_cash.save()
        # super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Выделение {self.amount} на {self.estimate_item}, {self.description}"
    
    class Meta:
        verbose_name = "Выделение средств"
        verbose_name_plural = "Выделения средств"

class Expense(models.Model):
    estimate_item = models.ForeignKey(EstimateItem, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма")
    description = models.TextField(verbose_name="Описание")
    date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Расход {self.amount} на {self.estimate_item}"
    
    class Meta:
        verbose_name = "Расход"
        verbose_name_plural = "Расходы"

class Sale(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='sales')
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Площадь квартиры")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма продажи")
    date = models.DateTimeField(auto_now_add=True)
    client_info = models.TextField(blank=True, verbose_name="Информация о клиенте")
    
    def save(self, *args, **kwargs):
        # При сохранении продажи обновляем проданную площадь и добавляем деньги в Общаг
        if not self.pk:  # Если это новая запись
            # self.block.sold_area += self.area
            self.block.save()
            # self.block.apartments.save()
            # Добавляем деньги в Общаг
            common_cash = CommonCash.objects.first()
            if common_cash:
                CashFlow.objects.create(
                    common_cash=common_cash,
                    flow_type='income',
                    amount=self.amount,
                    block=self.block,
                    description=f"Поступление за квартиру в {self.block}",
                    created_by=User.request.user  # Замените на текущего пользователя
                )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Продажа {self.area}м² в {self.block} за {self.amount}"
    
    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"