from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.projects_list, name='projects_list'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('block/<int:block_id>/', views.block_detail, name='block_detail'),
    path('block/<int:block_id>/apartments/', views.apartment_list, name='apartment_list'),
    path('apartment/<int:apartment_id>/', views.apartment_detail, name='apartment_detail'),
    path('block/<int:block_id>/add-apartment/', views.add_apartment, name='add_apartment'),
    path('apartment/<int:apartment_id>/add-payment/', views.add_payment, name='add_payment'),
    path('apartment/<int:apartment_id>/sell/', views.sell_apartment, name='sell_apartment'),
]