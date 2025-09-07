from urllib import request
from django.db import models
from projects.models import Project, Block, EstimateItem
from django.contrib.auth.models import User
from django.db.models import Sum, Q


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
                self.common_cash.balance -= self.amount
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
    created_by = models.ForeignKey(User,blank=True,null=True, on_delete=models.CASCADE)
    
    
    def save(self, *args, **kwargs):
        # user = kwargs.pop('user', None)  # ждём, что из views передадим
        # super().save(*args, **kwargs)
        # При сохранении продажи обновляем проданную площадь и добавляем деньги в Общаг
        # if not self.pk:  # Если это новая запись
            # self.block.sold_area += self.area
            # self.block.save()
            # self.block.apartments.save()
            # Добавляем деньги в Общаг
        common_cash = CommonCash.objects.first()
        # print(user,'_____________________')
        if common_cash:
            CashFlow.objects.create(
                    common_cash=common_cash,
                    flow_type='income',
                    amount=self.amount,
                    block=self.block,
                    description=f"Поступление за квартиру в {self.block}",
                    created_by= self.created_by  # Замените на текущего пользователя
                )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Продажа {self.area}м² в {self.block} за {self.amount}"
    
    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"
        
        
        
        
class Loan(models.Model):
    LOAN_TYPES = (
        ('given', 'Выданный займ'),
        ('taken', 'Полученный займ'),
    )
    
    LOAN_STATUSES = (
        ('active', 'Активный'),
        ('repaid', 'Погашенный'),
        ('overdue', 'Просроченный'),
    )
    
    common_cash = models.ForeignKey(CommonCash, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=10, choices=LOAN_TYPES, verbose_name="Тип займа")
    contractor = models.CharField(max_length=200, verbose_name="Контрагент")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма займа")
    issued_date = models.DateField(verbose_name="Дата выдачи")
    due_date = models.DateField(verbose_name="Дата возврата")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Процентная ставка")
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(max_length=10, choices=LOAN_STATUSES, default='active', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            # При создании нового займа обновляем баланс Общага
            if self.loan_type == 'given':
                # Выдача займа - уменьшаем баланс
                # self.common_cash.balance -= self.amount
                # Создаем запись о расходе
                CashFlow.objects.create(
                    common_cash=self.common_cash,
                    flow_type='expense',
                    amount=self.amount,
                    description=f"Выдача займа {self.contractor}",
                    created_by=self.created_by
                )
            else:
                # Получение займа - увеличиваем баланс
                # self.common_cash.balance += self.amount
                # Создаем запись о приходе
                CashFlow.objects.create(
                    common_cash=self.common_cash,
                    flow_type='income',
                    amount=self.amount,
                    description=f"Получение займа от {self.contractor}",
                    created_by=self.created_by
                )
            self.common_cash.save()
        
        super().save(*args, **kwargs)
    
    @property
    def total_amount(self):
        # Общая сумма к возврату (с учетом процентов)
        return self.amount * (1 + self.interest_rate / 100)
    
    @property
    def repaid_amount(self):
        # Сумма уже возвращенных средств
        return self.payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    @property
    def remaining_amount(self):
        # Остаток к возврату
        return self.total_amount - self.repaid_amount
    
    @property
    def is_overdue(self):
        # Проверка просрочки
        from django.utils import timezone
        return self.status == 'active' and timezone.now().date() > self.due_date
    
    def __str__(self):
        return f"{self.get_loan_type_display()} {self.amount} {self.contractor}"
    
    class Meta:
        verbose_name = "Займ"
        verbose_name_plural = "Займы"

class LoanPayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма платежа")
    payment_date = models.DateField(verbose_name="Дата платежа")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        super().save(*args, **kwargs)
        
        if is_new:
            # Обновляем баланс Общага при возврате займа
            common_cash = self.loan.common_cash
            
            if self.loan.loan_type == 'given':
                # Возврат выданного займа - увеличиваем баланс
                # common_cash.balance += self.amount
                # Создаем запись о приходе
                CashFlow.objects.create(
                    common_cash=common_cash,
                    flow_type='income',
                    amount=self.amount,
                    description=f"Возврат займа от {self.loan.contractor}",
                    created_by=self.created_by
                )
            else:
                # Возврат полученного займа - уменьшаем баланс
                # common_cash.balance -= self.amount
                # Создаем запись о расходе
                CashFlow.objects.create(
                    common_cash=common_cash,
                    flow_type='expense',
                    amount=self.amount,
                    description=f"Возврат займа {self.loan.contractor}",
                    created_by=self.created_by
                )
            
            common_cash.save()
            
            # Проверяем, полностью ли погашен займ
            if self.loan.remaining_amount <= 0:
                self.loan.status = 'repaid'
                self.loan.save()
    
    def __str__(self):
        return f"Платеж {self.amount} по займу {self.loan}"
    
    class Meta:
        verbose_name = "Платеж по займу"
        verbose_name_plural = "Платежи по займам"