"""
Tracks which nurse is assigned to a visit.
"""

from django.db import models
from django.conf import settings
from common.models import UUIDModel
from apps.visits.models.visit import Visit


class VisitAssignment(UUIDModel):

    class AssignmentStatus(models.TextChoices):
        PENDING   = "pending",   "Pending"    # nurse hasn't responded yet
        ACCEPTED  = "accepted",  "Accepted"   # nurse accepted
        REJECTED  = "rejected",  "Rejected"   # nurse rejected
        CANCELLED = "cancelled", "Cancelled"  # admin cancelled this assignment

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="assignments",)

    nurse = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="visit_assignments",)

    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="made_assignments",)

    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.PENDING,
    )

    rejection_reason = models.TextField(blank=True, default="")

    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "visits_assignment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Assignment({self.nurse.email} → Visit {self.visit_id}, {self.status})"