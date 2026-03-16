from django.db.models import (
    Count, Q)

from apps.visits.models import Visit, VisitAssignment
from apps.reports.models import Report

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
 

 
def hospital_nurse_summary(hospital, date_from=None, date_to=None) -> list:
    """
    Per-nurse breakdown of visit activity within a hospital.
 
    Counts distinct visits (not assignment rows) to avoid double-counting
    when a nurse is assigned, reassigned, or rejected and reassigned again.
    _________________________________________________________________________________________
    - total_visits_assigned: unique visits this nurse was ever assigned to
    - total_accepted:         visits nurse accepted (accepted assignment)
    - total_started:          visits nurse actually started
    - total_completed:        visits nurse completed (any terminal success status)
    - total_rejected:         assignments nurse rejected (may be < visits if reassigned)
    - total_reassigned:       visits where nurse was replaced (assignment cancelled by admin)
 
    """
    AS = VisitAssignment.AssignmentStatus
 
    # Base: all assignments for this hospital in date range
    qs = VisitAssignment.objects.filter(visit__hospital=hospital)
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    rows = (
        qs.values("nurse__id", "nurse__first_name", "nurse__last_name", "nurse__email")
        .annotate(
            # count distinct visit IDs not assignment rows —
            total_visits_assigned=Count("visit_id", distinct=True),
 
            # How many assignments did the nurse accept
            total_accepted=Count(
                "visit_id",
                filter=Q(status=AS.ACCEPTED),
                distinct=True,
            ),
            # How many assignments did the nurse reject
            total_rejected=Count(
                "id",
                filter=Q(status=AS.REJECTED),
            ),
            # How many assignments were cancelled (admin reassigned to someone else)
            total_reassigned=Count(
                "id",
                filter=Q(status=AS.CANCELLED),
            ),
        )
        .order_by("-total_visits_assigned")
    )
 
    # For started/completed we query Visit directly scoped to accepted assignments
    nurse_ids = [row["nurse__id"] for row in rows]
    visit_status_map = {}
 
    if nurse_ids:
        visit_rows = (
            Visit.objects.filter(
                hospital=hospital,
                assignments__nurse_id__in=nurse_ids,
                assignments__status=AS.ACCEPTED,
            )
            .values("assignments__nurse_id")
            .annotate(
                total_started=Count(
                    "id",
                    filter=Q(status__in=[
                        Visit.Status.STARTED,
                        Visit.Status.COMPLETED,
                        Visit.Status.REPORT_SUBMITTED,
                        Visit.Status.APPROVED,
                    ]),
                    distinct=True,
                ),
                total_completed=Count(
                    "id",
                    filter=Q(status__in=COMPLETED_STATUSES),
                    distinct=True,
                ),
            )
        )
        visit_status_map = {
            str(r["assignments__nurse_id"]): r
            for r in visit_rows
        }
 
    result = []
    for row in rows:
        nid = str(row["nurse__id"])
        vstats = visit_status_map.get(nid, {})
        result.append({
            "nurse_id": nid,
            "nurse_name": f"{row['nurse__first_name']} {row['nurse__last_name']}".strip(),
            "nurse_email": row["nurse__email"],
            "total_visits_assigned": row["total_visits_assigned"],
            "total_accepted": row["total_accepted"],
            "total_started": vstats.get("total_started", 0),
            "total_completed": vstats.get("total_completed", 0),
            "total_rejected": row["total_rejected"],
            "total_reassigned": row["total_reassigned"],
        })
 
    return result
 

  
def hospital_visits_over_time(hospital, date_from=None, date_to=None, group_by="day") -> list:
    """
    Visit counts grouped by day/week/month.
     """
    trunc_fn = TRUNC_MAP[group_by]
 
    qs = Visit.objects.filter(hospital=hospital)
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    rows = (
        qs.annotate(period=trunc_fn("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )
 
    return [
        {"period": str(row["period"]), "count": row["count"]}
        for row in rows
    ]