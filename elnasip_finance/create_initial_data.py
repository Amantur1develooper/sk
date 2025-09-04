import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elnasip_finance.settings')
django.setup()

from django.contrib.auth.models import User
from finances.models import CommonCash
from projects.models import Project, Block, EstimateCategory
from employees.models import Employee

def create_initial_data():
    # Создаем суперпользователя если его нет
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    
    # Создаем Общаг если его нет
    if not CommonCash.objects.exists():
        CommonCash.objects.create(balance=100000000)  # Начальный баланс
    
    # Создаем тестовые категории смет
    categories = ['Подготовка территории', 'Фундамент', 'Коробка здания', 'Отделка']
    for cat in categories:
        if not EstimateCategory.objects.filter(name=cat).exists():
            EstimateCategory.objects.create(name=cat)
    
    print("Начальные данные созданы!")

if __name__ == '__main__':
    create_initial_data()