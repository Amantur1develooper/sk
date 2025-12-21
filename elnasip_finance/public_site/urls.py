from django.urls import path
from .views import contacts_view, home_view

app_name = "public_site"

urlpatterns = [
    path("", home_view, name="home"),
    path("contacts/", contacts_view, name="contacts"),
]
