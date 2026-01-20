from django.urls import path
from .views import contacts_view, home_view, objects_list_view, project_detail_view

app_name = "public_site"

urlpatterns = [
    path("", home_view, name="home"),
    path("contacts/", contacts_view, name="contacts"),
    path("objects/", objects_list_view, name="objects"),
    path("objects/<slug:slug>/", project_detail_view, name="project_detail"),
]
