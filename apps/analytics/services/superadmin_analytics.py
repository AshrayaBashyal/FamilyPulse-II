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


def superadmin_hospital_breakdown(date_from=None, date_to=None) -> list:
    """
    Per-hospital activity breakdown for superadmin.
    Shows which hospitals are active, growing, or stagnant.
    Ordered by total visits descending.
    """
    visit_qs = Visit.objects.all()
    visit_qs = date_filter(visit_qs, "created_at", date_from, date_to)
 
    rows = (
        visit_qs.values("hospital__id", "hospital__name", "hospital__status")
        .annotate(
            total_visits=Count("id"),
            completed_visits=Count("id", filter=Q(status__in=COMPLETED_STATUSES)),
            cancelled_visits=Count("id", filter=Q(status=Visit.Status.CANCELLED)),
            total_nurses=Count(
                "hospital__memberships__user_id",
                filter=Q(
                    hospital__memberships__role=HospitalMembership.Role.NURSE,
                    hospital__memberships__is_active=True,
                ),
                distinct=True,
            ),
            total_hospital_admins=Count(
                "hospital__memberships__user_id",
                filter=Q(
                    hospital__memberships__role=HospitalMembership.Role.HOSPITAL_ADMIN,
                    hospital__memberships__is_active=True,
                ),
                distinct=True,
            ),
            total_medical_admins=Count(
                "hospital__memberships__user_id",
                filter=Q(
                    hospital__memberships__role=HospitalMembership.Role.MEDICAL_ADMIN,
                    hospital__memberships__is_active=True,
                ),
                distinct=True,
            ),
        )
        .order_by("-total_visits")
    )
 
    return [
        {
            "hospital_id": str(row["hospital__id"]),
            "hospital_name": row["hospital__name"],
            "hospital_status": row["hospital__status"],
            "total_visits": row["total_visits"],
            "completed_visits": row["completed_visits"],
            "cancelled_visits": row["cancelled_visits"],
            "total_active_nurses": row["total_nurses"],
            "total_active_hospital_admins": row["total_hospital_admins"],
            "total_active_medical_admins": row["total_medical_admins"],
        }
        for row in rows
    ]    


def superadmin_visits_over_time(date_from=None, date_to=None, group_by="day") -> list:
    """
    Platform-wide visit counts over time.
    Tells superadmin if the platform is growing.
    """
    trunc_fn = TRUNC_MAP[group_by]
    qs = Visit.objects.all()
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    rows = (
        qs.annotate(period=trunc_fn("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )
 
    return [{"period": str(row["period"]), "count": row["count"]} for row in rows]
 