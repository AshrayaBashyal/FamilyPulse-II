import re
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.reports.models import Report, ReportSection, ReportTemplate, ReportVersion
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
