from django.db.models import (
    Count
)

from apps.visits.models import Visit, VisitAssignment
from apps.reports.models import Report
from apps.hospitals.models import HospitalMembership

from apps.analytics.services.analytics_helpers import date_filter, TRUNC_MAP, COMPLETED_STATUSES




def nurse_visit_summary(nurse, hospital=None, date_from=None, date_to=None) -> dict:
    """
    Nurse's own performance: visits by status, completion rate.
    Without a hospital filter, only active hospital memberships are counted.
    """
    qs = Visit.objects.filter(
        assignments__nurse=nurse,
        assignments__status=VisitAssignment.AssignmentStatus.ACCEPTED,
    )
 
    if hospital:
        qs = qs.filter(hospital=hospital)
    else:
        active_hospital_ids = HospitalMembership.objects.filter(
            user=nurse,
            role=HospitalMembership.Role.NURSE,
            is_active=True,
        ).values_list("hospital_id", flat=True)
        qs = qs.filter(hospital_id__in=active_hospital_ids)
 
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    total = qs.count()
    by_status = (
        qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    status_map = {row["status"]: row["count"] for row in by_status}
 
    completed = sum(status_map.get(s, 0) for s in COMPLETED_STATUSES)
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0
 
    return {
        "total": total,
        "completed": completed,
        "completion_rate_pct": completion_rate,
        "by_status": status_map,
    }
 
 
def nurse_visits_over_time(nurse, date_from=None, date_to=None, group_by="week") -> list:
    """Nurse's visit counts grouped by week/month."""
    trunc_fn = TRUNC_MAP[group_by]
 
    qs = Visit.objects.filter(
        assignments__nurse=nurse,
        assignments__status=VisitAssignment.AssignmentStatus.ACCEPTED,
    )
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    rows = (
        qs.annotate(period=trunc_fn("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )
 
    return [{"period": str(row["period"]), "count": row["count"]} for row in rows]
 
 
def nurse_report_summary(nurse, date_from=None, date_to=None) -> dict:
    """Nurse's report stats: drafts, submitted, approved, rejected."""
    qs = Report.objects.filter(nurse=nurse)
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    by_status = (
        qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
 
    return {
        "total": qs.count(),
        "by_status": {row["status"]: row["count"] for row in by_status},
    }
 