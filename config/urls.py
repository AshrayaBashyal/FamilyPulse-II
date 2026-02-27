from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),


    # API routes — all versioned under /api/v1/
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/hospitals/", include("apps.hospitals.urls")),
    path("api/v1/dependents/", include("apps.dependents.urls")),
    path("api/v1/visits/", include("apps.visits.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),


    # API Docs (dev only — lock these down in prod)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]