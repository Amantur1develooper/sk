from django.urls import path
from .views import apartment_detail, contacts_view, home_view, objects_list_view, project_detail_view, apartments_list

app_name = "public_site"

urlpatterns = [
    path("", home_view, name="home"),
    path("contacts/", contacts_view, name="contacts"),
    path("objects/", objects_list_view, name="objects"),
    path("objects/<slug:slug>/", project_detail_view, name="project_detail"),
    
    path("apartments/", apartments_list, name="apartments"),
    path("apartments/<int:pk>/", apartment_detail, name="apartment_detail"),
]
