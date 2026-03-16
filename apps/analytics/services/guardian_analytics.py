from django.db.models import (
    Count
)

from apps.visits.models import Visit
from apps.reports.models import Report, ReportSection

from apps.analytics.services.analytics_helpers import date_filter


 
def dependent_visit_summary(dependent, date_from=None, date_to=None) -> dict:
    """Guardian view: total visits for their dependent, broken down by status."""
    qs = Visit.objects.filter(dependent=dependent)
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
 
 
def dependent_health_trends(dependent, field_name: str, date_from=None, date_to=None) -> list:
    """
    Time-series of a specific report section value for a dependent.
    Only returns APPROVED reports.
 
    TODO (AI integration):
    - Before querying ReportSection directly, run AI extraction on submitted
      reports to normalize field values. Problems to solve:
        1. Same field different names: "temperature", "temp", "body_temp" —
           AI should map these to a canonical field name per hospital template.
        2. Different units: Celsius vs Fahrenheit, kg vs lbs —
           AI should detect the unit from the template field's help_text or
           choices, then normalize to a standard unit before storing.
           Suggested approach: add a `unit` field to TemplateField, store
           a `normalized_value` alongside `value` in ReportSection, AI fills
           normalized_value on report approval.
        3. Expand min_status to include SUBMITTED once AI can validate
           section values from not-yet-approved reports.
 
    TODO (scheduled_at):
    - Replace "report__visit__created_at" with "report__visit__scheduled_at"
      once scheduled_at is implemented on the Visit model.
    - Also replace created_at in the return dict below.
    """
    qs = ReportSection.objects.filter(
        report__visit__dependent=dependent,
        report__status=Report.Status.APPROVED,
        field__name=field_name,
    ).select_related("report__visit")
 
    # TODO (scheduled_at): replace created_at with scheduled_at below
    qs = date_filter(qs, "report__visit__created_at", date_from, date_to)
    qs = qs.order_by("report__visit__created_at")
 
    return [
        {
            # TODO (scheduled_at): replace created_at with scheduled_at
            "date": str(section.report.visit.created_at.date()),
            "value": section.value,
            "visit_id": str(section.report.visit_id),
        }
        for section in qs
    ]
 
 
def dependent_available_trend_fields(dependent) -> list:
    """
    Returns field names that have approved report data for this dependent.
 
    TODO (AI integration):
    - Once AI normalizes field names across templates, return canonical
      field names instead of raw template field names.
    - Also include fields from SUBMITTED reports that AI has processed.
    """
    return list(
        ReportSection.objects.filter(
            report__visit__dependent=dependent,
            report__status=Report.Status.APPROVED,
        )
        .values_list("field__name", flat=True)
        .distinct()
        .order_by("field__name")
    )