from django.urls import path
from apps.analytics.views.superadmin import (
    SuperadminPlatformSummaryView,
    SuperadminHospitalBreakdownView,
    SuperadminVisitsOverTimeView,
)
from apps.analytics.views.hospital import (
    HospitalVisitSummaryView,
    HospitalVisitsOverTimeView,
    HospitalReportSummaryView,
    HospitalNurseSummaryView,
)
from apps.analytics.views.medical_admin import MedicalAdminReviewSummaryView
from apps.analytics.views.nurse import (
    NurseVisitSummaryView,
    NurseVisitsOverTimeView,
    NurseReportSummaryView,
)
from apps.analytics.views.guardian import (
    DependentVisitSummaryView,
    DependentHealthTrendsView,
    DependentAvailableFieldsView,
)

urlpatterns = [
    # Superadmin — platform wide
    path("platform/summary/", SuperadminPlatformSummaryView.as_view(), name="platform-summary"),
    path("platform/hospitals/", SuperadminHospitalBreakdownView.as_view(), name="platform-hospitals"),
    path("platform/visits/over-time/", SuperadminVisitsOverTimeView.as_view(), name="platform-visits-over-time"),

    # Hospital admin
    path("hospitals/<uuid:hospital_id>/visits/summary/", HospitalVisitSummaryView.as_view(), name="hospital-visit-summary"),
    path("hospitals/<uuid:hospital_id>/visits/over-time/", HospitalVisitsOverTimeView.as_view(), name="hospital-visits-over-time"),
    path("hospitals/<uuid:hospital_id>/reports/summary/", HospitalReportSummaryView.as_view(), name="hospital-report-summary"),
    path("hospitals/<uuid:hospital_id>/nurses/summary/", HospitalNurseSummaryView.as_view(), name="hospital-nurse-summary"),

    # Medical admin
    path("hospitals/<uuid:hospital_id>/reviews/summary/", MedicalAdminReviewSummaryView.as_view(), name="medical-review-summary"),

    # Nurse (own data)
    path("nurses/me/visits/summary/", NurseVisitSummaryView.as_view(), name="nurse-visit-summary"),
    path("nurses/me/visits/over-time/", NurseVisitsOverTimeView.as_view(), name="nurse-visits-over-time"),
    path("nurses/me/reports/summary/", NurseReportSummaryView.as_view(), name="nurse-report-summary"),

    # Guardian / dependent health
    path("dependents/<uuid:dependent_id>/visits/summary/", DependentVisitSummaryView.as_view(), name="dependent-visit-summary"),
    path("dependents/<uuid:dependent_id>/health/trends/", DependentHealthTrendsView.as_view(), name="dependent-health-trends"),
    path("dependents/<uuid:dependent_id>/health/fields/", DependentAvailableFieldsView.as_view(), name="dependent-health-fields"),
]