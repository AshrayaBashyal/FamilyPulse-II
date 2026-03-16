from django.db.models import (
    Count, Avg, Q, F, ExpressionWrapper,
    DurationField,
)

from apps.visits.models import Visit, VisitAssignment
from apps.reports.models import Report, ReportSection, ReportVersion
from apps.hospitals.models import Hospital, HospitalMembership

from apps.analytics.services.analytics_helpers import date_filter, TRUNC_MAP, COMPLETED_STATUSES


def hospital_visit_summary(hospital, date_from=None, date_to=None) -> dict:
    """Total visits broken down by status."""
    qs = Visit.objects.filter(hospital=hospital)
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    total = qs.count()
    by_status = (
        qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
 
    return {
        "total": total,
        "by_status": {row["status"]: row["count"] for row in by_status},
    }
 

def hospital_report_summary(hospital, date_from=None, date_to=None) -> dict:
    """Report approval/rejection rates for the hospital."""
    qs = Report.objects.filter(visit__hospital=hospital)
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    total = qs.count()
    by_status = (
        qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
 
    return {
        "total": total,
        "by_status": {row["status"]: row["count"] for row in by_status},
    }
 