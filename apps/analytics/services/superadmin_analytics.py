from django.db.models import (
    Count, Avg, Q, F, ExpressionWrapper,
    DurationField,
)

from apps.visits.models import Visit, VisitAssignment
from apps.reports.models import Report, ReportSection, ReportVersion
from apps.hospitals.models import Hospital, HospitalMembership

from apps.analytics.services.analytics_helpers import date_filter, TRUNC_MAP, COMPLETED_STATUSES


def superadmin_platform_summary(date_from=None, date_to=None) -> dict:
    """
    Platform-wide overview for superadmin.
    Shows health of the entire platform across all hospitals.
    """
    # Hospital counts by status
    hospital_qs = Hospital.objects.all()
    hospitals_by_status = (
        hospital_qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
 
    # User counts by role across all memberships
    membership_qs = HospitalMembership.objects.filter(is_active=True)
    users_by_role = (
        membership_qs.values("role")
        .annotate(count=Count("user_id", distinct=True))
        .order_by("role")
    )
 
    # Total unique users (any role)
    total_users = (
        HospitalMembership.objects.filter(is_active=True)
        .values("user_id")
        .distinct()
        .count()
    )
 
    # Visit counts
    visit_qs = Visit.objects.all()
    visit_qs = date_filter(visit_qs, "created_at", date_from, date_to)
    visits_by_status = (
        visit_qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
 
    # Report counts
    report_qs = Report.objects.all()
    report_qs = date_filter(report_qs, "created_at", date_from, date_to)
    reports_by_status = (
        report_qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
 
    return {
        "hospitals": {
            "total": hospital_qs.count(),
            "by_status": {row["status"]: row["count"] for row in hospitals_by_status},
        },
        "users": {
            "total_unique": total_users,
            "by_role": {row["role"]: row["count"] for row in users_by_role},
        },
        "visits": {
            "total": visit_qs.count(),
            "by_status": {row["status"]: row["count"] for row in visits_by_status},
        },
        "reports": {
            "total": report_qs.count(),
            "by_status": {row["status"]: row["count"] for row in reports_by_status},
        },
    }    