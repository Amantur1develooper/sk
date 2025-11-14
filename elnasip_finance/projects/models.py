from decimal import Decimal
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
def some_logic():
        from finances.models import Allocation 
        
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.db.models import Sum, Q

class Apartment(models.Model):
    block = models.ForeignKey("Block", on_delete=models.CASCADE, related_name='apartments')
    floor = models.IntegerField(verbose_name="Этаж", default=1)
    is_sold = models.BooleanField(default=False, verbose_name="Продано")
    apartment_number = models.CharField(max_length=20, verbose_name="Номер квартиры(обезательно)")
    rooms = models.IntegerField(default=0,verbose_name="Количество комнат(обезательно)")
    area = models.DecimalField(max_digits=10,default=0, decimal_places=2, verbose_name="Площадь (m²)(обезательно)")
    sold_area = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Проданная площадь (m²)")
    
    fact_price_per_m2 = models.DecimalField(max_digits=10,null=True, blank=True, decimal_places=2, default=0, verbose_name=" Цена за m²")
    deal_amount = models.DecimalField(max_digits=15,blank=True, null=True, default=0, decimal_places=2, verbose_name="Поступило с Сделки")
    deal_Fakt_deal_amount =  models.DecimalField(max_digits=15, blank=True, default=0, null=True,  decimal_places=2, verbose_name="Цена Сделки")
    deal_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Номер сделки")
    client_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="ФИО клиента")
    remaining_deal_amount = models.DecimalField(max_digits=15, blank=True, default=0, null=True, decimal_places=2, verbose_name="Остаток от сделки")
    is_reserved = models.BooleanField(default=False, verbose_name="Бронь")
    discount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Скидка (сом)", default=0, )
    planned_price_per_m2 = models.DecimalField(max_digits=10, default=0, decimal_places=2, blank=True, null=True, verbose_name="Планируемая цена m²(обезательно)")
    planned_deal_amount = models.DecimalField(max_digits=15, default=0, decimal_places=2, blank=True, null=True, verbose_name="Планируемая сделка")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_rented = models.BooleanField(default=False, verbose_name="Сдана в аренду")
    rent_price_per_month = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True, null=True,
        verbose_name="Цена аренды в месяц (сом)"
    )
    rent_start_date = models.DateField(blank=True, null=True, verbose_name="Начало аренды")
    rent_end_date = models.DateField(blank=True, null=True, verbose_name="Окончание аренды")
    tenant_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Арендатор")
    tenant_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон арендатора")
    tenant_contract = models.CharField(max_length=100, blank=True, null=True, verbose_name="Номер договора аренды")

    def save(self, *args, **kwargs):
        # Автоматический расчет сделки и остатка
        if self.sold_area and self.fact_price_per_m2:
            self.deal_amount = self.sold_area * self.fact_price_per_m2
            if self.planned_deal_amount:
                self.remaining_deal_amount = self.planned_deal_amount - self.deal_amount
            else:
                self.remaining_deal_amount = self.deal_Fakt_deal_amount - self.deal_amount
        
        # Автоматический расчет планируемой сделки
        if self.area and self.planned_price_per_m2:
            self.planned_deal_amount = self.area * self.planned_price_per_m2
            
        # Если квартира продана, снимаем с аренды
        if self.is_sold and self.is_rented:
            self.is_rented = False
            self.rent_start_date = None
            self.rent_end_date = None
            
        # Если квартира сдана в аренду, снимаем бронь
        if self.is_rented and self.is_reserved:
            self.is_reserved = False
            
        if self.is_sold:
            self.planned_deal_amount = 0
        
        super().save(*args, **kwargs)
    @property
    def rent_status(self):
        """Статус аренды"""
        from django.utils import timezone
        if not self.is_rented:
            return "not_rented"
        if self.rent_end_date and timezone.now().date() > self.rent_end_date:
            return "expired"
        return "active"
    
    @property
    def total_rent_income(self):
        """Общий доход от аренды"""
        return self.rent_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    # def save(self, *args, **kwargs):
    #     # Автоматический расчет сделки и остатка
    #     if self.sold_area and self.fact_price_per_m2:
    #         self.deal_amount = self.sold_area * self.fact_price_per_m2
    #         if self.planned_deal_amount:
    #             self.remaining_deal_amount = self.planned_deal_amount - self.deal_amount
    #         else:
    #             self.remaining_deal_amount = self.deal_Fakt_deal_amount - self.deal_amount
        
    #     # Автоматический расчет планируемой сделки
    #     if self.area and self.planned_price_per_m2:
    #         self.planned_deal_amount = self.area * self.planned_price_per_m2
    #     # Если квартира продана, применяем скидку к фактической сумме сделки
    #     # if self.is_sold and self.discount and self.deal_Fakt_deal_amount:
    #     # # Вычисляем сумму без скидки
    #     #     original_amount = self.deal_Fakt_deal_amount / (1 - self.discount / 100)
    #     #     self.deal_amount = original_amount
    #     #     self.planned_deal_amount = 0
    #     if self.is_sold==True:
    #         self.planned_deal_amount = 0
        
    #     super().save(*args, **kwargs)
    @property
    def sold_area_if_sold(self):
        """Вернёт проданную площадь только если квартира отмечена как проданная"""
        return self.sold_area if self.is_sold else 0
    @property
    def calculated_price(self):
        """Расчетная стоимость квартиры без скидки  !!!!   """
        return self.area * self.planned_price_per_m2
    @property
    def deal_amount_if_sold(self):
        """Вернёт сумму сделки только для проданных квартир"""
        return self.deal_amount if self.is_sold else 0
    def __str__(self):
        return f"Кв. {self.apartment_number} ({self.block})"
    
    class Meta:
        verbose_name = "Квартира"
        verbose_name_plural = "Квартиры"
        ordering = ['block', 'floor', 'apartment_number']


class ApartmentComment(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="comments", verbose_name="Квартира")
    text = models.TextField(verbose_name="Комментарий / Примечание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    author = models.CharField(max_length=150, blank=True, null=True, verbose_name="Автор")

    def __str__(self):
        return f"Комментарий к {self.apartment.apartment_number} — {self.text[:30]}"

class DealPayment(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма платежа")
    payment_date = models.DateTimeField(verbose_name="Дата платежа")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='created_payments')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='updated_payments')
    

    def save(self, *args, **kwargs):
        # Сначала сохраняем сам платеж
        super().save(*args, **kwargs)
    
        apartment = self.apartment
        total_paid = apartment.payments.aggregate(Sum('amount'))['amount__sum'] or 0

        # Безопасное значение deal_amount
        deal_amount = apartment.deal_amount or 0

        if apartment.fact_price_per_m2 and apartment.planned_price_per_m2 > 0:
            # Рассчитываем проданную площадь
            apartment.sold_area = total_paid / apartment.fact_price_per_m2
            apartment.sold_area = min(apartment.sold_area, apartment.area)  # не больше общей площади

        # Определяем статус "продана"
        if deal_amount > 0:
            apartment.is_sold = True
        else:
            apartment.is_sold = False

        apartment.save()


    def __str__(self):
        return f"Платеж {self.amount} для кв. {self.apartment.apartment_number}"

    class Meta:
        verbose_name = "Платеж по сделке"
        verbose_name_plural = "Платежи по сделкам"
        ordering = ['-payment_date']
    # def save(self, *args, **kwargs):
    #     # Сначала сохраняем сам платеж
    #     super().save(*args, **kwargs)
    
    #     apartment = self.apartment
    #     total_paid = apartment.payments.aggregate(Sum('amount'))['amount__sum'] or 0

    #     # Безопасное значение deal_amount
    #     deal_amount = apartment.deal_amount or 0

    #     if apartment.fact_price_per_m2 and apartment.planned_price_per_m2 > 0:
    #         # Рассчитываем проданную площадь
    #         apartment.sold_area = total_paid / apartment.fact_price_per_m2
    #         apartment.sold_area = min(apartment.sold_area, apartment.area)  # не больше общей площади



    #     apartment.save()

  

    # def __str__(self):
    #     return f"Платеж {self.amount} для кв. {self.apartment.apartment_number}"

    # class Meta:
    #     verbose_name = "Платеж по сделке"
    #     verbose_name_plural = "Платежи по сделкам"
    #     ordering = ['-payment_date']

# Обновляем модель Block для добавления вычисляемых свойств

from django.db.models import Sum, F, ExpressionWrapper, DecimalField

class Project(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название ЖК")
    total_area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая площадь ЖК")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    @property
    def calc_total_area(self):
        """Общая площадь всех квартир во всех блоках проекта"""
        result = Apartment.objects.filter(block__project=self).aggregate(Sum("area"))["area__sum"]
        return result or 0
    @property
    def total_received_amount(self):
        total = Decimal(0)
        for block in self.blocks.all():  # related_name="blocks" в ForeignKey(Project)
            total += block.received_amount or 0
        return total
    @property
    def calc_sold_area(self):
        """Проданная площадь всех квартир проекта"""
        result = Apartment.objects.filter(block__project=self).aggregate(Sum("sold_area"))["sold_area__sum"]
        return result or 0
    @property
    def total_estimate_plan(self):
        """План по смете всего проекта (сумма quantity * unit_price по всем сметам блоков)"""
        result = EstimateItem.objects.filter(block__project=self).aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("unit_price"),
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
        )["total"]
        return result or 0
    # @property
    # def total_estimate_plan(self):
    #     # сумма всех смет проекта (через ЖК и Блоки)
    #     return self.jks.aggregate(
    #         total=Sum("blocks__estimate_items__amount")
    #     )["total"] or 0
    @property
    def remaining_area(self):
        """Оставшаяся (свободная) площадь"""
        return self.calc_total_area - self.calc_sold_area
    class Meta:
        verbose_name = "Объект (ЖК)"
        verbose_name_plural = "Объекты (ЖК)"

class Block(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='blocks')
    name = models.CharField(max_length=100, verbose_name="Название/Литер блока")
    floors = models.IntegerField(verbose_name="Количество этажей")
    total_area = models.DecimalField(max_digits=10, default=100, decimal_places=2, verbose_name="Общая площадь блока")
    sold_area = models.DecimalField(max_digits=10, default=1, decimal_places=2, verbose_name="Проданная площадь")
    
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"
    # @property
    # def area_sum(self):
        # """Сумма проданных площадей по квартирам с галочкой 'Продано'"""
        # return self.apartments.all().aggregate(total=Sum('area'))['total'] or 0
        
    @property
    def not_sold_minus_allocated(self):
        received_amount = self.received_amount or 0
        allocated = self.get_allocated_sum() or 0
        return received_amount - allocated

    @property
    def sold_apartments_count(self):
        """Количество проданных квартир"""
        return self.apartments.filter(is_sold=True).count()
    @property
    def received_amount(self):
        """Сумма денег, поступивших по проданным квартирам"""
        return (
            self.apartments.filter(is_sold=True)
            .aggregate(total=Sum('deal_amount'))['total'] or 0
        )
    @property
    def sold_area_sum(self):
        """Сумма проданных площадей по квартирам с галочкой 'Продано'"""
        return self.apartments.filter(is_sold=True).aggregate(total=Sum('area'))['total'] or 0
    def not_sold_area_sum(self):
        """Сумма проданных площадей по квартирам с галочкой 'Продано'"""
        return self.apartments.filter(is_sold=False).aggregate(total=Sum('area'))['total'] or 0

    def get_allocated_sum(self):
        # some_logic()
        from finances.models import Allocation
        return Allocation.objects.filter(
            estimate_item__block=self
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
    @property
    def calc_total_area(self):
        result = self.apartments.aggregate(Sum('area'))['area__sum']
        return result if result else 0

    @property
    def calc_sold_area(self):
        result = self.apartments.aggregate(Sum('sold_area'))['sold_area__sum']
        return result if result else 0
    
    
    @property
    def total_area(self):
        result = self.apartments.aggregate(Sum('area'))['area__sum']
        return result if result else 0 #!!!
    
    @property
    def sold_area(self):
        result = self.apartments.aggregate(Sum('sold_area'))['sold_area__sum']
        return result if result else 0 #!!!
    
    
    
    
    @property
    def total_discount(self):
        result = self.apartments.aggregate(Sum('discount'))['discount__sum']
        return result if result else 0
    
    @property
    def remaining_area(self):
        return self.total_area - self.sold_area
    
    
    # @property
    # def allocated_sum(self):
    #     return sum(item.allocated for item in self.estimate_items.all())
    

    class Meta:
        verbose_name = "Блок"
        verbose_name_plural = "Блоки"

class EstimateCategory(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_salary_category(cls):
        category, created = cls.objects.get_or_create(
            name='Зарплата',
            defaults={'description': 'Расходы на оплату труда сотрудников'}
        )
        return category
    
    class Meta:
        verbose_name = "Категория сметы"
        verbose_name_plural = "Категории смет"

class EstimateItem(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='estimate_items')
    category = models.ForeignKey(EstimateCategory, on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Наименование материала/работы")
    unit = models.CharField(max_length=50, verbose_name="Единица измерения")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")
    fakt_quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Факт Количества")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Цена за единицу")
    
    @property
    def planned_amount(self):
        return self.quantity * self.unit_price
    
    @property
    def spent_amount(self):
        return sum(expense.amount for expense in self.expenses.all())
    
    def get_allocated_sum(self):
        """Возвращает сумму всех выделений для этой позиции сметы"""
        from finances.models import Allocation
        return Allocation.objects.filter(estimate_item=self).aggregate(Sum('amount'))['amount__sum'] or 0

    @property
    def margin(self):
        return self.planned_amount - self.get_allocated_sum()
    
    
    def __str__(self):
        return f"{self.block.name} — {self.category.name} — {self.name}"
    
    
    
    class Meta:
        verbose_name = "Позиция сметы"
        verbose_name_plural = "Позиции смет"
        
        
class RentPayment(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='rent_payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма платежа")
    payment_date = models.DateTimeField(verbose_name="Дата платежа")
    period_start = models.DateField(verbose_name="Начало периода")
    period_end = models.DateField(verbose_name="Конец периода")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='created_rent_payments')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='updated_rent_payments')
    
    def save(self, *args, **kwargs):
        # Создаем запись в движении денег
        from finances.models import CommonCash, CashFlow
        common_cash = CommonCash.objects.first()
        if common_cash and not self.pk:  # Только для новых записей
            CashFlow.objects.create(
                common_cash=common_cash,
                flow_type='income',
                amount=self.amount,
                description=f"Аренда кв. {self.apartment.apartment_number} ({self.period_start} - {self.period_end})",
                block=self.apartment.block,
                created_by=self.created_by
            )
            
            # Помечаем квартиру как сданную в аренду
            if not self.apartment.is_rented:
                self.apartment.is_rented = True
                self.apartment.save()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Создаем запись об удалении в движении денег
        from finances.models import CommonCash, CashFlow
        common_cash = CommonCash.objects.first()
        if common_cash:
            CashFlow.objects.create(
                common_cash=common_cash,
                flow_type='expense',  # Обратная операция
                amount=self.amount,
                description=f"УДАЛЕНИЕ: Аренда кв. {self.apartment.apartment_number}",
                block=self.apartment.block,
                created_by=User.objects.filter(is_superuser=True).first()
            )
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"Арендный платеж {self.amount} для кв. {self.apartment.apartment_number}"
    
    class Meta:
        verbose_name = "Платеж по аренде"
        verbose_name_plural = "Платежи по аренде"
        ordering = ['-payment_date']