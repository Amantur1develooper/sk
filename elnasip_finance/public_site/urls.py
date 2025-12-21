from django.urls import path
from .views import contacts_view

app_name = "public_site"

urlpatterns = [
    path("contacts/", contacts_view, name="contacts"),
]
