"""
URL configuration for elnasip_finance project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
# elnasip_finance/urls.py
from employees.views import login_view, logout_view
from django.contrib import admin
from django.urls import path, include
from finances.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path('', dashboard, name='dashboard'),
    path('finances/', include('finances.urls')),
    path('projects/', include('projects.urls')),
    path('employees/', include('employees.urls')),
    path('reports/', include('reports.urls')),

]
