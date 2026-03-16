"""
CHANGES:
- create_visit: now saves preferred_at from validated_data
- schedule_visit: sets guardian_response=PENDING and guardian_response_deadline
- assign_nurse: no longer blocked by guardian_response — runs in parallel
- NEW confirm_visit: guardian confirms the scheduled time
- NEW cancel_by_guardian: guardian rejects scheduled time → visit cancelled
- NEW auto_confirm_visit: called by a scheduled task when deadline passes
"""

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.visits.models import Visit, VisitAssignment
from apps.visits.state_machine import transition, get_user_role_in_hospital
from apps.hospitals.models import HospitalMembership
from apps.dependents.models import Guardianship


def create_visit(validated_data: dict, requested_by) -> Visit:
    """
    Guardian books a visit.
    preferred_at is optional — guardian sets their desired time window.
    """
    hospital   = validated_data["hospital"]
    dependent  = validated_data["dependent"]
    visit_type = validated_data["visit_type"]

    is_guardian = Guardianship.objects.filter(
        user=requested_by, dependent=dependent, is_active=True,
    ).exists()
    if not is_guardian:
        raise PermissionDenied("You are not a guardian of this dependent.")

    if not hospital.is_active:
        raise ValidationError("This hospital is not currently active.")

    if visit_type.hospital_id != hospital.id:
        raise ValidationError("This visit type does not belong to the selected hospital.")

    return Visit.objects.create(
        **validated_data,
        requested_by=requested_by,
        status=Visit.Status.REQUESTED,
    )


def schedule_visit(visit: Visit, scheduled_at, triggered_by) -> Visit:
    """
    Admin schedules a visit — REQUESTED → SCHEDULED.

    Enforces two rules:
    1. Admin must schedule within VISIT_SCHEDULE_WITHIN_HOURS of visit creation (default 24h).
       Ensures admin acts promptly so guardian has enough lead time.
    2. scheduled_at must be at least VISIT_CONFIRMATION_BUFFER_HOURS from now (default 24h).
       Prevents scheduling imminent visits with no time for guardian to respond.

    Deadline logic:
        deadline = min(now + VISIT_CONFIRMATION_HOURS, scheduled_at - VISIT_CONFIRMATION_BUFFER_HOURS)
        if deadline <= now → auto-confirm immediately (visit is too soon to wait)

    Nurse assignment is NOT blocked — admin can assign in parallel.
    """
    now = timezone.now()

    schedule_within_hours  = getattr(settings, "VISIT_SCHEDULE_WITHIN_HOURS",    24)
    confirmation_hours     = getattr(settings, "VISIT_CONFIRMATION_HOURS",       24)
    buffer_hours           = getattr(settings, "VISIT_CONFIRMATION_BUFFER_HOURS", 2)

    # Rule 1: admin must schedule within 24h of visit creation
    schedule_deadline = visit.created_at + timedelta(hours=schedule_within_hours)
    if now > schedule_deadline:
        raise ValidationError(
            f"This visit must be scheduled within {schedule_within_hours} hours of creation. "
            f"Deadline was {schedule_deadline.strftime('%Y-%m-%d %H:%M UTC')}. "
            f"Ask the guardian to rebook."
        )

    # Rule 2: scheduled_at must be at least buffer_hours from now
    min_scheduled_at = now + timedelta(hours=buffer_hours)
    if scheduled_at < min_scheduled_at:
        raise ValidationError(
            f"scheduled_at must be at least {buffer_hours} hours from now."
        )

    # Compute guardian response deadline
    max_deadline     = now + timedelta(hours=confirmation_hours)
    buffer_deadline  = scheduled_at - timedelta(hours=buffer_hours)
    deadline         = min(max_deadline, buffer_deadline)

    if deadline <= now:
        # Visit is too soon for guardian to meaningfully respond — auto-confirm immediately
        guardian_response = Visit.GuardianResponse.AUTO_CONFIRMED
        guardian_response_at = now
    else:
        guardian_response    = Visit.GuardianResponse.PENDING
        guardian_response_at = None

    visit.scheduled_at               = scheduled_at
    visit.guardian_response          = guardian_response
    visit.guardian_response_at       = guardian_response_at
    visit.guardian_response_deadline = deadline
    visit.save(update_fields=[
        "scheduled_at",
        "guardian_response",
        "guardian_response_at",
        "guardian_response_deadline",
        "updated_at",
    ])

    return transition(visit, Visit.Status.SCHEDULED, triggered_by)


def confirm_visit(visit: Visit, guardian) -> Visit:
    """
    Guardian confirms the scheduled time.

    Rules:
    - Only the guardian who requested the visit (or any active guardian of the dependent).
    - Visit must be in SCHEDULED, ASSIGNED, or ACCEPTED status.
    - Guardian response must be PENDING.

    After confirmation visit continues in its normal lifecycle.
    If a nurse is already assigned, nothing changes — they proceed.
    """
    is_guardian = Guardianship.objects.filter(
        user=guardian,
        dependent=visit.dependent,
        is_active=True,
    ).exists()
    if not is_guardian:
        raise PermissionDenied("You are not a guardian of this dependent.")

    if visit.guardian_response != Visit.GuardianResponse.PENDING:
        raise ValidationError(
            f"This visit has already been responded to: {visit.guardian_response}."
        )

    if visit.status not in [
        Visit.Status.SCHEDULED,
        Visit.Status.ASSIGNED,
        Visit.Status.ACCEPTED,
    ]:
        raise ValidationError(
            "Visit can only be confirmed when it is scheduled, assigned, or accepted."
        )

    visit.guardian_response    = Visit.GuardianResponse.CONFIRMED
    visit.guardian_response_at = timezone.now()
    visit.save(update_fields=["guardian_response", "guardian_response_at", "updated_at"])
    return visit


def cancel_by_guardian(visit: Visit, guardian, reason: str = "") -> Visit:
    """
    Guardian rejects the scheduled time → visit CANCELLED.

    If a nurse was already assigned, their assignment is also cancelled.
    Guardian gets a full refund (hook for payments — add here when payments built).

    Rules:
    - Only works if guardian_response is PENDING.
    - Cannot cancel once visit is STARTED or beyond.
    """
    is_guardian = Guardianship.objects.filter(
        user=guardian,
        dependent=visit.dependent,
        is_active=True,
    ).exists()
    if not is_guardian:
        raise PermissionDenied("You are not a guardian of this dependent.")

    if visit.guardian_response != Visit.GuardianResponse.PENDING:
        raise ValidationError(
            f"This visit has already been responded to: {visit.guardian_response}."
        )

    if visit.status in [
        Visit.Status.STARTED,
        Visit.Status.COMPLETED,
        Visit.Status.REPORT_SUBMITTED,
        Visit.Status.APPROVED,
    ]:
        raise ValidationError("Visit cannot be cancelled once it has started.")

    # Cancel any active nurse assignments
    VisitAssignment.objects.filter(
        visit=visit,
        status__in=[
            VisitAssignment.AssignmentStatus.PENDING,
            VisitAssignment.AssignmentStatus.ACCEPTED,
        ],
    ).update(status=VisitAssignment.AssignmentStatus.CANCELLED)

    visit.guardian_response    = Visit.GuardianResponse.CANCELLED
    visit.guardian_response_at = timezone.now()
    visit.cancelled_by         = guardian
    visit.cancellation_reason  = reason or "Guardian rejected scheduled time."
    visit.save(update_fields=[
        "guardian_response", "guardian_response_at",
        "cancelled_by", "cancellation_reason", "updated_at",
    ])

    return transition(visit, Visit.Status.CANCELLED, guardian)


def auto_confirm_visit(visit: Visit) -> Visit:
    """
    Called by a scheduled task (e.g. Celery beat) when guardian_response_deadline passes.
    If guardian hasn't responded, visit is auto-confirmed and proceeds normally.

    TODO (notifications): before auto-confirming, send a final reminder notification
    to the guardian X hours before the deadline.

    TODO (scheduled task): wire this up in a Celery periodic task:
        - Query Visit.objects.filter(
              guardian_response=GuardianResponse.PENDING,
              guardian_response_deadline__lte=timezone.now(),
              status__in=[SCHEDULED, ASSIGNED, ACCEPTED],
          )
        - Call auto_confirm_visit() on each result.
    """
    if visit.guardian_response != Visit.GuardianResponse.PENDING:
        return visit  # already responded, nothing to do

    if timezone.now() < visit.guardian_response_deadline:
        raise ValidationError("Guardian response deadline has not passed yet.")

    visit.guardian_response    = Visit.GuardianResponse.AUTO_CONFIRMED
    visit.guardian_response_at = timezone.now()
    visit.save(update_fields=["guardian_response", "guardian_response_at", "updated_at"])
    return visit


def assign_nurse(visit: Visit, nurse, assigned_by) -> VisitAssignment:
    """
    Admin assigns a nurse — SCHEDULED → ASSIGNED.

    CHANGE: No longer blocked by guardian_response.
    Admin can assign in parallel while guardian is still PENDING.
    If guardian later cancels, cancel_by_guardian() handles the assignment cancellation.
    """
    is_nurse_here = HospitalMembership.objects.filter(
        user=nurse,
        hospital=visit.hospital,
        role=HospitalMembership.Role.NURSE,
        is_active=True,
    ).exists()
    if not is_nurse_here:
        raise ValidationError("This nurse does not belong to this hospital.")

    VisitAssignment.objects.filter(
        visit=visit,
        status=VisitAssignment.AssignmentStatus.PENDING,
    ).update(status=VisitAssignment.AssignmentStatus.CANCELLED)

    transition(visit, Visit.Status.ASSIGNED, assigned_by)

    return VisitAssignment.objects.create(
        visit=visit,
        nurse=nurse,
        assigned_by=assigned_by,
    )


def accept_visit(visit: Visit, nurse) -> Visit:
    """Nurse accepts — ASSIGNED → ACCEPTED."""
    assignment = VisitAssignment.objects.filter(
        visit=visit,
        nurse=nurse,
        status=VisitAssignment.AssignmentStatus.PENDING,
    ).first()
    if not assignment:
        raise PermissionDenied("You are not the assigned nurse for this visit.")

    assignment.status      = VisitAssignment.AssignmentStatus.ACCEPTED
    assignment.accepted_at = timezone.now()
    assignment.save(update_fields=["status", "accepted_at", "updated_at"])

    return transition(visit, Visit.Status.ACCEPTED, nurse)


def reject_assignment(visit: Visit, nurse, reason: str = "") -> Visit:
    """Nurse rejects — back to SCHEDULED so admin can reassign."""
    assignment = VisitAssignment.objects.filter(
        visit=visit,
        nurse=nurse,
        status=VisitAssignment.AssignmentStatus.PENDING,
    ).first()
    if not assignment:
        raise PermissionDenied("You are not the assigned nurse for this visit.")

    assignment.status           = VisitAssignment.AssignmentStatus.REJECTED
    assignment.rejection_reason = reason
    assignment.rejected_at      = timezone.now()
    assignment.save(update_fields=["status", "rejection_reason", "rejected_at", "updated_at"])

    return transition(visit, Visit.Status.SCHEDULED, nurse)


def start_visit(visit: Visit, nurse) -> Visit:
    """Nurse starts — ACCEPTED → STARTED."""
    assignment = VisitAssignment.objects.filter(
        visit=visit, nurse=nurse,
        status=VisitAssignment.AssignmentStatus.ACCEPTED,
    ).first()
    if not assignment:
        raise PermissionDenied("You are not the accepted nurse for this visit.")
    return transition(visit, Visit.Status.STARTED, nurse)


def complete_visit(visit: Visit, nurse) -> Visit:
    """Nurse completes — STARTED → COMPLETED."""
    assignment = VisitAssignment.objects.filter(
        visit=visit, nurse=nurse,
        status=VisitAssignment.AssignmentStatus.ACCEPTED,
    ).first()
    if not assignment:
        raise PermissionDenied("You are not the accepted nurse for this visit.")
    return transition(visit, Visit.Status.COMPLETED, nurse)


def mark_report_submitted(visit: Visit, nurse) -> Visit:
    """Nurse submits report — COMPLETED → REPORT_SUBMITTED."""
    return transition(visit, Visit.Status.REPORT_SUBMITTED, nurse)


def cancel_visit(visit: Visit, cancelled_by, reason: str = "") -> Visit:
    """Admin cancels. For guardian cancellation use cancel_by_guardian()."""
    role = get_user_role_in_hospital(cancelled_by, visit.hospital)

    if role == "hospital_admin":
        if not reason:
            raise ValidationError("A reason is required when an admin cancels a visit.")
    else:
        if visit.status in [
            Visit.Status.STARTED, Visit.Status.COMPLETED,
            Visit.Status.REPORT_SUBMITTED, Visit.Status.APPROVED,
            Visit.Status.REJECTED,
        ]:
            raise ValidationError("Visit cannot be cancelled once it has started.")

    visit.cancelled_by        = cancelled_by
    visit.cancellation_reason = reason
    visit.save(update_fields=["cancelled_by", "cancellation_reason", "updated_at"])

    return transition(visit, Visit.Status.CANCELLED, cancelled_by)