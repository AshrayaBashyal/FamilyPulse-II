from django.db import models
from django.conf import settings
from common.models import UUIDModel
from apps.hospitals.models.hospital import Hospital


class HospitalMembership(UUIDModel):
    """
    Links a User to a Hospital with a specific role.
    """

    class Role(models.TextChoices):
        HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
        MEDICAL_ADMIN = "medical_admin", "Medical Admin"
        NURSE = "nurse", "Nurse"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hospital_memberships",
        # related_name lets you do: user.hospital_memberships.all()
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    role = models.CharField(max_length=30, choices=Role.choices)

    is_active = models.BooleanField(default=True)

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
    )

    class Meta:
        db_table = "hospitals_membership"
        unique_together = [("user", "hospital")]

    def __str__(self):
        return f"{self.user.email} → {self.hospital.name} ({self.role})"