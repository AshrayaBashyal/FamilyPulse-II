import re
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.reports.models import Report, ReportSection, ReportTemplate, ReportVersion, TemplateField, Rep
from apps.visits.models import Visit, VisitAssignment
# from apps.visits.services.visit_service import mark_report_submitted


def _build_sections_snapshot(report: Report) -> list:
    return [
        {
            "field_id": str(section.field_id),
            "field_name": section.field.name,
            "label": section.field.label,
            "field_type": section.field.field_type,
            "value": section.value,
        }
        for section in report.sections.select_related("field").all()
    ]


def _snapshot_version(report: Report, action: str, triggered_by, notes: str = "") -> ReportVersion:
    return ReportVersion.objects.create(
        report=report,
        version_number=report.version,
        sections_snapshot=_build_sections_snapshot(report),
        action=action,
        triggered_by=triggered_by,
        notes=notes,
    )


def _validate_field_value(field, value: str):
    """
    Validates a value against its field type.
    Returns error message string if invalid, None if valid.
    """
    ft = TemplateField.FieldType

    if field.field_type == ft.NUMBER:
        try:
            float(value)
        except ValueError:
            return f"{field.label} must be a number."

    elif field.field_type == ft.BOOLEAN:
        if value.lower() not in ["true", "false"]:
            return f"{field.label} must be 'true' or 'false'."

    elif field.field_type == ft.BLOOD_PRESSURE:
        if not re.match(r"^\d{2,3}/\d{2,3}$", value):
            return f"{field.label} must be in the format 120/80."

    elif field.field_type == ft.CHOICE:
        options = field.choices if isinstance(field.choices, list) else []
        if value not in options:
            return f"{field.label} must be one of: {', '.join(options)}."

    elif field.field_type == ft.ATTACHMENT:
        if not re.match(r"^https?://[^\s]+$", value):
            return f"{field.label} must be a valid URL (upload the file first)."

    return None