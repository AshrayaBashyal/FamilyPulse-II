"""
All visit status transition logic.
"""

from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.visits.models.visit import Visit
from apps.hospitals.models import HospitalMembership


VALID_TRANSITIONS = {
    Visit.Status.REQUESTED:        [Visit.Status.SCHEDULED, Visit.Status.CANCELLED],
    Visit.Status.SCHEDULED:        [Visit.Status.ASSIGNED, Visit.Status.CANCELLED],
    Visit.Status.ASSIGNED:         [Visit.Status.ACCEPTED, Visit.Status.SCHEDULED, Visit.Status.CANCELLED],
    Visit.Status.ACCEPTED:         [Visit.Status.STARTED, Visit.Status.CANCELLED],
    Visit.Status.STARTED:          [Visit.Status.COMPLETED],
    Visit.Status.COMPLETED:        [Visit.Status.REPORT_SUBMITTED],
    Visit.Status.REPORT_SUBMITTED: [Visit.Status.APPROVED, Visit.Status.REJECTED],
    Visit.Status.APPROVED:         [],  
    Visit.Status.REJECTED:         [],   
    Visit.Status.CANCELLED:        [],   
}


TRANSITION_PERMISSIONS = {
    (Visit.Status.REQUESTED,        Visit.Status.SCHEDULED):        ["hospital_admin"],
    (Visit.Status.SCHEDULED,        Visit.Status.ASSIGNED):         ["hospital_admin"],
    (Visit.Status.ASSIGNED,         Visit.Status.ACCEPTED):         ["nurse"],
    (Visit.Status.ASSIGNED,         Visit.Status.SCHEDULED):        ["hospital_admin"],
    (Visit.Status.ACCEPTED,         Visit.Status.STARTED):          ["nurse"],
    (Visit.Status.STARTED,          Visit.Status.COMPLETED):        ["nurse"],
    (Visit.Status.COMPLETED,        Visit.Status.REPORT_SUBMITTED): ["nurse"],
    (Visit.Status.REPORT_SUBMITTED, Visit.Status.APPROVED):         ["medical_admin"],
    (Visit.Status.REPORT_SUBMITTED, Visit.Status.REJECTED):         ["medical_admin"],

    (Visit.Status.REQUESTED,        Visit.Status.CANCELLED):        ["guardian", "hospital_admin"],
    (Visit.Status.SCHEDULED,        Visit.Status.CANCELLED):        ["guardian", "hospital_admin"],
    (Visit.Status.ASSIGNED,         Visit.Status.CANCELLED):        ["guardian", "hospital_admin"],
    (Visit.Status.ACCEPTED,         Visit.Status.CANCELLED):        ["guardian", "hospital_admin"],
}


def get_user_role_in_hospital(user, hospital) -> str | None:
    membership = HospitalMembership.objects.filter(
        user=user,
        hospital=hospital,
        is_active=True,
    ).first()

    if membership:
        return membership.role  

    return "guardian"  


def transition(visit: Visit, new_status: str, triggered_by) -> Visit:  
    current = visit.status

    # 1. Is this transition valid at all?
    allowed_next = VALID_TRANSITIONS.get(current, [])
    if new_status not in allowed_next:
        raise ValidationError(
            f"Cannot move visit from '{current}' to '{new_status}'. "
            f"Allowed transitions: {[s for s in allowed_next] or 'none (terminal state)'}."
        )

    # 2. Does this user have the right role to trigger this transition?
    role = get_user_role_in_hospital(triggered_by, visit.hospital)
    allowed_roles = TRANSITION_PERMISSIONS.get((current, new_status), [])

    if role not in allowed_roles:
        raise PermissionDenied(
            f"Your role ('{role}') cannot move a visit from '{current}' to '{new_status}'. "
            f"Required: {allowed_roles}."
        )

    # 3. Apply the transition
    visit.status = new_status
    visit.save(update_fields=["status", "updated_at"])

    return visit