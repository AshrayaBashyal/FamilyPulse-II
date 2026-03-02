"""
VisitType is defined by each hospital.
Examples: General Checkup, Sample Collection, Dressing Change, Post-Surgery Check.
- Different hospitals offer different services.
- Each type can have custom required vitals, attachments, duration, and pricing.
- Hospital admins manage their own types — platform doesn't dictate them.
"""

from django.db import models
from common.models import UUIDModel
from apps.hospitals.models import Hospital


class VisitType(UUIDModel):

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name="visit_types",
    )

    name = models.CharField(max_length=100)
    # e.g. General Checkup, Sample Collection

    description = models.TextField(blank=True, default="")

    duration_minutes = models.PositiveIntegerField(default=30, help_text="Estimated visit duration in minutes.",)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,)

    # What this visit type require?
    requires_vitals = models.BooleanField(default=False)
    requires_attachments = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "visits_visit_type"
        unique_together = [("hospital", "name")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.hospital.name})"