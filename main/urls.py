from django.contrib import admin
from django.urls import path, include
from main.views import HealthCheckView

urlpatterns = [
    path("health", HealthCheckView.as_view(), name="health-check"),
    path("admin/", admin.site.urls),
    path("api/", include("ticketing.urls")),
]
