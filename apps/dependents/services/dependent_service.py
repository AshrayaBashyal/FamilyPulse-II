from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from apps.dependents.models import Dependent, Guardianship

User = get_user_model()


def create_dependent(validated_data: dict, guardian) -> Dependent:
    """
    Creates a dependent and immediately sets the creator as their first guardian.
    """
    dependent = Dependent.objects.create(**validated_data)

    Guardianship.objects.create(
        user=guardian,
        dependent=dependent,
        added_by=guardian,
    )

    return dependent


def update_dependent(dependent: Dependent, validated_data: dict) -> Dependent:
    """
    Updates dependent fields. Only called after guardian permission is verified.
    """
    for field, value in validated_data.items():
        setattr(dependent, field, value)
    dependent.save()
    return dependent


def add_guardian(dependent: Dependent, email: str, added_by) -> Guardianship:
    """
    Grants another user guardianship over a dependent.
    """
    user = User.objects.get(email__iexact=email)

    existing = Guardianship.objects.filter(user=user, dependent=dependent).first()
    if existing:
        if existing.is_active:
            raise ValidationError("This user is already a guardian of this dependent.")
        else:
            # Reactivate
            existing.is_active = True
            existing.added_by = added_by
            existing.save(update_fields=["is_active", "added_by", "updated_at"])
            return existing

    return Guardianship.objects.create(
        user=user,
        dependent=dependent,
        added_by=added_by,
    )


def revoke_guardian(guardianship: Guardianship, requesting_user) -> Guardianship:
    """
    Revokes a guardianship. Soft delete — record preserved.
    - Cannot remove the last guardian (dependent would be orphaned).
    """
    active_guardians_count = Guardianship.objects.filter(
        dependent=guardianship.dependent,
        is_active=True,
    ).count()

    if active_guardians_count <= 1:
        raise ValidationError(
            "Cannot remove the last guardian. "
            "Assign another guardian first before removing this one."
        )

    guardianship.is_active = False
    guardianship.save(update_fields=["is_active", "updated_at"])
    return guardianship