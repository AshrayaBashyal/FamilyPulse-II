from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.hospitals.models import Hospital, HospitalMembership

User = get_user_model()


def create_hospital(validated_data: dict, created_by) -> Hospital:
    """
    Creates a new hospital in PENDING status.
    Platform superadmin must approve it before it becomes ACTIVE.
    """
    hospital = Hospital.objects.create(**validated_data)

    HospitalMembership.objects.create(
        user=created_by,
        hospital=hospital,
        role=HospitalMembership.Role.HOSPITAL_ADMIN,
        invited_by=created_by,
    )

    return hospital


def update_hospital_status(hospital: Hospital, new_status: str) -> Hospital:
    """
    Only callable by platform superadmin (enforced in the view).
    """
    hospital.status = new_status
    hospital.save(update_fields=["status", "updated_at"])
    return hospital


def add_staff_member(hospital: Hospital, email: str, role: str, invited_by) -> HospitalMembership:
    """
    Adds an existing user to a hospital with a given role.
    """
    user = User.objects.get(email__iexact=email)

    existing = HospitalMembership.objects.filter(user=user, hospital=hospital).first()
    if existing:
        if existing.is_active:
            raise ValidationError("This user is already a member of this hospital.")
        else:
            # Reactivate instead of creating a duplicate
            existing.role = role
            existing.is_active = True
            existing.invited_by = invited_by
            existing.save(update_fields=["role", "is_active", "invited_by", "updated_at"])
            return existing

    if role == HospitalMembership.Role.NURSE:
        nurse_elsewhere = HospitalMembership.objects.filter(
            user=user,
            role=HospitalMembership.Role.NURSE,
            is_active=True,
        ).exists()
        if nurse_elsewhere:
            raise ValidationError(
                "This nurse already belongs to another hospital. "
                "A nurse can only be assigned to one hospital at a time."
            )

    return HospitalMembership.objects.create(
        user=user,
        hospital=hospital,
        role=role,
        invited_by=invited_by,
    )


def remove_staff_member(membership: HospitalMembership) -> HospitalMembership:
    """
    Deactivates a membership (soft remove).
    """
    membership.is_active = False
    membership.save(update_fields=["is_active", "updated_at"])
    return membership