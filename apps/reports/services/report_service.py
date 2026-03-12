import re
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.reports.models import Report, ReportSection, ReportTemplate, ReportVersion, TemplateField, Rep
from apps.visits.models import Visit, VisitAssignment
from apps.visits.services.visit_service import mark_report_submitted


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


def _validate_and_save_sections(report: Report, sections_input: list) -> None:
    """
    Validates section input against the visit type's template.
    Checks:
      - No duplicate, unknown field IDs sent by client 
      - All required fields are present and non-empty
      - All values match their field type
    Then creates/updates ReportSection rows.
    """
    try:
        template = report.visit.visit_type.report_template
    except Exception:
        raise ValidationError(
            "This visit type has no report template defined. "
            "Ask the hospital admin to set one up first."
        )

    template_fields = {str(f.id): f for f in template.fields.all()}

    # Detect duplicate field IDs in input before building the map
    seen_field_ids = []
    duplicates = []
    for s in sections_input:
        fid = str(s["field_id"])
        if fid in seen_field_ids:
            duplicates.append(fid)
        seen_field_ids.append(fid)

    if duplicates:
        raise ValidationError(
            {"sections": f"Duplicate field IDs submitted: {', '.join(set(duplicates))}."}
        )

    input_map = {str(s["field_id"]): s["value"] for s in sections_input}

    # Reject unknown field IDs
    unknown = [fid for fid in input_map if fid not in template_fields]
    if unknown:
        raise ValidationError(
            {"sections": f"Unknown field IDs not in this template: {', '.join(unknown)}."}
        )

    # Validate required fields and type correctness
    errors = {}
    for field_id, field in template_fields.items():
        value = input_map.get(field_id, "").strip()

        if field.required and not value:
            errors[field.name] = f"{field.label} is required."
            continue

        if value:
            type_error = _validate_field_value(field, value)
            if type_error:
                errors[field.name] = type_error

    if errors:
        raise ValidationError(errors)

    # Save sections
    for field_id, field in template_fields.items():
        value = input_map.get(field_id, "")
        ReportSection.objects.update_or_create(
            report=report,
            field=field,
            defaults={"value": value},
        )    


def create_report(visit_id: str, sections_input: list, nurse) -> Report:
    try:
        visit = Visit.objects.select_related(
            "visit_type__report_template"
        ).get(id=visit_id)
    except Visit.DoesNotExist:
        raise ValidationError("Visit not found.")

    if visit.status not in [Visit.Status.COMPLETED, Visit.Status.REPORT_SUBMITTED]:
        raise ValidationError("Reports can only be created for completed visits.")

    is_assigned = VisitAssignment.objects.filter(
        visit=visit,
        nurse=nurse,
        status=VisitAssignment.AssignmentStatus.ACCEPTED,
    ).exists()
    if not is_assigned:
        raise PermissionDenied("You are not the accepted nurse for this visit.")

    report = Report.objects.create(
        visit=visit,
        nurse=nurse,
        status=Report.Status.DRAFT,
    )

    _validate_and_save_sections(report, sections_input)
    return report        


def update_report(report: Report, sections_input: list) -> Report:
    if report.is_locked:
        raise ValidationError("This report has been approved and cannot be edited.")
    if report.status == Report.Status.SUBMITTED:
        raise ValidationError("This report has been submitted. (??Withdraw it first to edit??).")

    _validate_and_save_sections(report, sections_input)
    report.save()
    return report


def submit_report(report: Report, nurse) -> Report:
    if report.status != Report.Status.DRAFT:
        raise ValidationError("Only draft reports can be submitted.")

    report.status = Report.Status.SUBMITTED
    report.save(update_fields=["status", "updated_at"])

    _snapshot_version(report, ReportVersion.Action.SUBMITTED, triggered_by=nurse)

    if report.visit.status == Visit.Status.COMPLETED:
        mark_report_submitted(report.visit, nurse)

    return report    