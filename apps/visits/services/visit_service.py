from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.visits.models import Visit, VisitType, VisitAssignment
from apps.visits.state_machine import transition
from apps.hospitals.models import Hospital, HospitalMembership
from apps.dependents.models import Guardianship


def create_visit(validated_data: dict, requested_by) -> Visit:
    """
    Creates a new visit in REQUESTED state.
    """
    hospital = validated_data["hospital"]
    dependent = validated_data["dependent"]
    visit_type = validated_data["visit_type"]

    is_guardian = Guardianship.objects.filter(
        user=requested_by,
        dependent=dependent,
        is_active=True,
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
    """Admin schedules the visit — moves REQUESTED -> SCHEDULED."""
    visit.scheduled_at = scheduled_at
    visit.save(update_fields=["scheduled_at", "updated_at"])
    return transition(visit, Visit.Status.SCHEDULED, triggered_by)


def assign_nurse(visit: Visit, nurse, assigned_by) -> VisitAssignment:  #transaction.atomic later
    """
    Admin assigns a nurse — moves SCHEDULED -> ASSIGNED.
    Creates a VisitAssignment record.
    Cancels any previous pending assignment first.---?? May Change
    """
    # Verify nurse belongs to this hospital
    is_nurse_here = HospitalMembership.objects.filter(
        user=nurse,
        hospital=visit.hospital,
        role=HospitalMembership.Role.NURSE,
        is_active=True,
    ).exists()
    if not is_nurse_here:
        raise ValidationError("This nurse does not belong to this hospital.")
    
    # Cancel any existing pending assignment
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
    """Nurse accepts — moves ASSIGNED -> ACCEPTED."""
    assignment = VisitAssignment.objects.filter(
        visit=visit,
        nurse=nurse,
        status=VisitAssignment.AssignmentStatus.PENDING,
    ).first()
    if not assignment:
        raise PermissionDenied("You are not the assigned nurse for this visit.")

    assignment.status = VisitAssignment.AssignmentStatus.ACCEPTED
    assignment.accepted_at = timezone.now()
    assignment.save(update_fields=["status", "accepted_at", "updated_at"])

    return transition(visit, Visit.Status.ACCEPTED, nurse)


def start_visit(visit: Visit, nurse) -> Visit:
    """Nurse starts — moves ACCEPTED -> STARTED."""
    assignment = VisitAssignment.objects.filter(
        visit=visit,
        nurse=nurse,
    ).first()
    if not assignment:
        raise PermissionDenied("You are not the assigned nurse for this visit.")
    return transition(visit, Visit.Status.STARTED, nurse)


def complete_visit(visit: Visit, nurse) -> Visit:
    """Nurse completes — moves STARTED -> COMPLETED."""
    assignment = VisitAssignment.objects.filter(
        visit=visit,
        nurse=nurse,
    ).first()
    if not assignment:
        raise PermissionDenied("You are not the assigned nurse for this visit.")
    return transition(visit, Visit.Status.COMPLETED, nurse)


def cancel_visit(visit: Visit, cancelled_by, reason: str = "") -> Visit:
    """
    Cancels a visit. Allowed before STARTED for guardians and admins.
    Admins can cancel at any time (reason required).
    """
    from apps.visits.state_machine import get_user_role_in_hospital
    role = get_user_role_in_hospital(cancelled_by, visit.hospital)

    if role == "hospital_admin":
        if not reason:
            raise ValidationError("A reason is required when an admin cancels a visit.")
    else:
        # Guardian — can only cancel before STARTED
        if visit.status in [Visit.Status.STARTED, Visit.Status.COMPLETED,
                             Visit.Status.REPORT_SUBMITTED, Visit.Status.APPROVED,
                             Visit.Status.REJECTED]:
            raise ValidationError("Visit cannot be cancelled once it has started.")

    visit.cancelled_by = cancelled_by
    visit.cancellation_reason = reason
    visit.save(update_fields=["cancelled_by", "cancellation_reason", "updated_at"])

    return transition(visit, Visit.Status.CANCELLED, cancelled_by)