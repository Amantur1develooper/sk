from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ФИО сотрудника")  # Новое поле
    position = models.CharField(max_length=100, verbose_name="Должность")
    hire_date = models.DateField(verbose_name="Дата приема")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Оклад")
    bank_details = models.TextField(verbose_name="Банковские реквизиты")
    blocks = models.ForeignKey( 'projects.Block', on_delete=models.CASCADE,
        related_name='employees', 
        blank=True, null=True,
        verbose_name="Строительные блоки"
    )
    def __str__(self):
        return f"{self.full_name} - {self.position}" 
    
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

class SalaryPayment(models.Model):
    PAYMENT_TYPES = (
        ('salary', 'Зарплата'),
        ('advance', 'Аванс'),
        ('bonus', 'Бонус'),
        ('premia', 'Премия')
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES, verbose_name="Тип выплаты")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    date = models.DateTimeField(auto_now_add=True)
    period = models.DateField(verbose_name="За период")
    # created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        # Сначала сохраняем объект
        super().save(*args, **kwargs)
        
        # Создаем движение денег в общаге
        from finances.models import CommonCash, CashFlow
        common_cash = CommonCash.objects.first()
        if common_cash:
            CashFlow.objects.create(
                common_cash=common_cash,
                flow_type='expense',
                amount=self.amount,
                block = self.employee.blocks,
                description=f"{self.get_payment_type_display()} для {self.employee.full_name} {self.employee.position}",
                created_by=User.objects.first()
            )

        # Создаем расходы в сметах связанных блоков
        if self.employee.blocks:  # так как ForeignKey
            self.create_expenses_in_blocks()
        # if self.employee.blocks.exists():
        #     self.create_expenses_in_blocks()
    def create_expenses_in_blocks(self):
        from projects.models import EstimateCategory, EstimateItem
        from finances.models import Expense, Allocation, CommonCash

        salary_category = EstimateCategory.get_salary_category()

        block = self.employee.blocks  # один блок
        amount_per_block = self.amount
# bonus
        if self.payment_type == 'bonus':
            estimate_item, created = EstimateItem.objects.get_or_create(
        block=block,
        category=salary_category,
        name="Бонус отделу продаж",
    )
        elif self.payment_type == 'salary' or self.payment_type == 'advance':
            estimate_item, created = EstimateItem.objects.get_or_create(  # смета - EstimateItem
        block=block,
        category=salary_category,
        name="Фонд оплаты труда",
    )
       
            
        if self.payment_type != 'premia':
            common_cash = CommonCash.objects.first()
            if common_cash:
                Allocation.objects.create(
            common_cash=common_cash,
            estimate_item=estimate_item,
            amount=amount_per_block,
            description=f"Автоматическое выделение на {self.get_payment_type_display()} для {self.employee.full_name}"
            )

            Expense.objects.create(
            estimate_item=estimate_item,
            amount=amount_per_block,
            description=f"{self.get_payment_type_display()} для {self.employee.full_name} за {self.period}",
            created_by=User.objects.first()
            )
    # def create_expenses_in_blocks(self):
    #     from projects.models import EstimateCategory, EstimateItem
    #     from finances.models import Expense, Allocation, CommonCash
    
    # # Получаем или создаем категорию "Зарплата"
    #     salary_category = EstimateCategory.get_salary_category()
    
    # # Распределяем сумму выплаты по блокам
    #     blocks_count = self.employee.blocks.count()
    #     amount_per_block = self.amount / blocks_count
    #     # print(f"Создаём расходы для блока {block.id} - {block}")
    #     for block in self.employee.blocks.all():
    #     # Находим или создаем позицию сметы для зарплат в этом блоке
    #         estimate_item, created = EstimateItem.objects.get_or_create(
    #         block=block,
    #         category=salary_category,
    #         name="Фонд оплаты труда",
            
    #     )
    #     # print("EstimateItem:", estimate_item, "Создан?", created)
    #     # Если позиция уже существует, обновляем ее
    #         # if not created:
               
    #             # estimate_item.save()
        
    #     # Автоматически выделяем средства из Общага
    #     common_cash = CommonCash.objects.first()
    #     if common_cash:
            
    #             allocation = Allocation.objects.create( 
    #                 common_cash=common_cash,
    #                 estimate_item=estimate_item,
    #                 amount=amount_per_block,
    #                 description=f"Автоматическое выделение на {self.get_payment_type_display()} для {self.employee.full_name}"
    #            )
        
    #     # Создаем расход в смете блока
    #     Expense.objects.create(
    #         estimate_item=estimate_item,
    #         amount=amount_per_block,
    #         description=f"{self.get_payment_type_display()} для {self.employee.full_name} за {self.period}",
    #         created_by=User.objects.first()
    #     )
    # def create_expenses_in_blocks(self):
    #     from projects.models import EstimateCategory, EstimateItem
    #     from finances.models import Expense
        
    #     # Получаем или создаем категорию "Зарплата"
    #     salary_category = EstimateCategory.get_salary_category()
        
    #     # Распределяем сумму выплаты по блокам
    #     blocks_count = self.employee.blocks.count()
    #     amount_per_block = self.amount / blocks_count
        
    #     for block in self.employee.blocks.all():
    #         # Находим или создаем позицию сметы для зарплат в этом блоке
    #         estimate_item, created = EstimateItem.objects.get_or_create(
    #             block=block,
    #             category=salary_category,
    #             name="Фонд оплаты труда",
    #             defaults={
    #                 'unit': 'мес',
    #                 'quantity': 1,
    #                 'unit_price': amount_per_block,
    #                 'fakt_quantity': 1,
    #             }
    #         )
            
    #         # Если позиция уже существует, обновляем ее
    #         if not created:
    #             estimate_item.unit_price += amount_per_block
    #             estimate_item.save()
            
    #         # Создаем расход в смете блока
    #         Expense.objects.create(
    #             estimate_item=estimate_item,
    #             amount=amount_per_block,
    #             description=f"{self.get_payment_type_display()} для {self.employee.full_name} за {self.period}",
    #             created_by=User.objects.first())
    # def save(self, *args, **kwargs):
    #     # Сначала сохраняем  1674276679 1674274679
    #     super().save(*args, **kwargs)
        
    #     # Создаем движение денег в общаге
    #     from finances.models import CommonCash, CashFlow
    #     common_cash = CommonCash.objects.first()
    #     if common_cash:
    #         CashFlow.objects.create(
    #             common_cash=common_cash,
    #             flow_type='expense',
    #             amount=self.amount,
    #             description=f"{self.get_payment_type_display()} для {self.employee.full_name}",
    #             created_by=User.objects.first()  # Замените на логику получения текущего пользователя
    #         )
        
    #     # Создаем расходы в сметах связанных блоков
    #     if self.employee.blocks.exists():
    #         self.create_expenses_in_blocks()
            
            
    # def create_expenses_in_blocks(self):
    #     from projects.models import EstimateCategory, EstimateItem
    #     from finances.models import Expense
        
    #     # Получаем или создаем категорию "Зарплата"
    #     salary_category = EstimateCategory.get_salary_category()
        
    #     # Распределяем сумму выплаты по блокам
    #     blocks_count = self.employee.blocks.count()
    #     amount_per_block = self.amount / blocks_count
        
    #     for block in self.employee.blocks.all():
    #         # Получаем или создаем позицию сметы для зарплат в этом блоке
    #         estimate_item, created = EstimateItem.objects.get_or_create(
    #             block=block,
    #             category=salary_category,
    #             name=f"Зарплата {self.employee.full_name}",
    #             defaults={
    #                 'unit': 'мес',
    #                 'quantity': 1,
    #                 'unit_price': amount_per_block,
    #                 'fakt_quantity': 1,
    #             }
    #         )
            
    #         # Создаем расход в смете блока
    #         Expense.objects.create(
    #             estimate_item=estimate_item,
    #             amount=amount_per_block,
    #             description=f"{self.get_payment_type_display()} для {self.employee.full_name} за {self.period}",
    #             created_by=User.objects.first()  # Замените на логику получения текущего пользователя
    #         )
    # def save(self, *args, **kwargs):
    #     if not self.pk:  # Если это новая запись
    #         from finances.models import CommonCash, CashFlow
    #         common_cash = CommonCash.objects.first()
    #         if common_cash:
    #             # Убрали передачу created_by (теперь не требуется)
    #             CashFlow.objects.create(
    #                 common_cash=common_cash,
    #                 flow_type='expense',
    #                 amount=self.amount,
    #                 description=f"{self.get_payment_type_display()} для {self.employee.full_name}",  # Используем employee.full_name
    #              created_by=User.objects.first())
    #     super().save(*args, **kwargs)
    # def save(self, *args, **kwargs): 121778000 121768000
    #     # При выплате зарплаты уменьшаем баланс Общага
    #     if not self.pk:  # Если это новая запись
    #         from finances.models import CommonCash, CashFlow
    #         common_cash = CommonCash.objects.first()
    #         if common_cash:
    #             CashFlow.objects.create(
    #                 common_cash=common_cash,
    #                 flow_type='expense',
    #                 amount=self.amount,
    #                 description=f"{self.get_payment_type_display()} для {self.employee}",
    #                 created_by=User.objects.first()  # Замените на текущего пользователя
    #             )
    #     super().save(*args, **kwargs)
    
    # def __str__(self):
        # return f"{self.get_payment_type_display()} {self.amount} для {self.employee.full_name}"
    def __str__(self):
        return f"{self.get_payment_type_display()} {self.amount} для {self.employee.full_name}"

    class Meta:
        verbose_name = "Выплата зарплаты"
        verbose_name_plural = "Выплаты зарплаты"