from django.urls import path
from apps.reports.views.nurse import (
    ReportListCreateView,
    ReportDetailView,
    ReportSubmitView,
)
from apps.reports.views.review import ReportReviewView
from apps.reports.views.template import (
    ReportTemplateView,
    TemplateFieldListCreateView,
    TemplateFieldDeleteView,
)

urlpatterns = [
    # Report templates
    path("templates/", ReportTemplateView.as_view(), name="report-template"),
    path("templates/<uuid:template_id>/fields/", TemplateFieldListCreateView.as_view(), name="template-field-create"),
    path("templates/<uuid:template_id>/fields/<uuid:field_id>/", TemplateFieldDeleteView.as_view(), name="template-field-delete"),

    # Reports
    path("", ReportListCreateView.as_view(), name="report-list-create"),
    path("<uuid:report_id>/", ReportDetailView.as_view(), name="report-detail"),
    path("<uuid:report_id>/submit/", ReportSubmitView.as_view(), name="report-submit"),
    path("<uuid:report_id>/review/", ReportReviewView.as_view(), name="report-review"),
]