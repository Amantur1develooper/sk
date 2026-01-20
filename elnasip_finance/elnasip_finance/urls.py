from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from employees.views import login_view, logout_view
from finances.views import dashboard
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),

    path("i18n/", include("django.conf.urls.i18n")),

    path("select2/", include("django_select2.urls")),
    path("finances/", include("finances.urls")),
    path("projects/", include("projects.urls")),
    path("employees/", include("employees.urls")),
    path("reports/", include("reports.urls")),
]

urlpatterns += i18n_patterns(
    path("", include("public_site.urls")),
    prefix_default_language=False,  # ru без префикса, ky/en с префиксом
)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)