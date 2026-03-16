from django.db.models import (
    Avg, F, ExpressionWrapper,
    DurationField,
)

from apps.reports.models import Report,  ReportVersion

from apps.analytics.services.analytics_helpers import date_filter


def medical_admin_review_summary(hospital, reviewed_by=None, date_from=None, date_to=None) -> dict:
    """
    Report review stats: pending, approved, rejected counts + avg review time.
    avg_review_time uses ReportVersion SUBMITTED snapshot created_at as start
    time — not Report.updated_at which changes on every save.
    """
    qs = Report.objects.filter(visit__hospital=hospital)
    qs = date_filter(qs, "created_at", date_from, date_to)
 
    if reviewed_by:
        qs = qs.filter(reviewed_by=reviewed_by)
 
    pending = qs.filter(status=Report.Status.SUBMITTED).count()
    approved = qs.filter(status=Report.Status.APPROVED).count()
    rejected_count = qs.filter(status=Report.Status.REJECTED).count()
 
    reviewed_versions = ReportVersion.objects.filter(
        report__visit__hospital=hospital,
        action=ReportVersion.Action.SUBMITTED,
        report__reviewed_at__isnull=False,
    )
    if reviewed_by:
        reviewed_versions = reviewed_versions.filter(report__reviewed_by=reviewed_by)
    if date_from:
        reviewed_versions = reviewed_versions.filter(created_at__date__gte=date_from)
    if date_to:
        reviewed_versions = reviewed_versions.filter(created_at__date__lte=date_to)
 
    avg_review_time = reviewed_versions.annotate(
        review_duration=ExpressionWrapper(
            F("report__reviewed_at") - F("created_at"),
            output_field=DurationField(),
        )
    ).aggregate(avg=Avg("review_duration"))
 
    avg_hours = None
    if avg_review_time["avg"]:
        avg_hours = round(avg_review_time["avg"].total_seconds() / 3600, 1)
 
    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected_count,
        "avg_review_time_hours": avg_hours,
    }