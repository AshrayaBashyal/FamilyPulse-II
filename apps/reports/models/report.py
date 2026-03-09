"""
Lifecycle: DRAFT → SUBMITTED → APPROVED / REJECTED
Content lives in ReportSection rows. This model holds metadata and review state only.
"""

from django.db import models
from django.conf import settings
from common.models import UUIDModel
from apps.visits.models import Visit


class Report(UUIDModel):

    class Status(models.TextChoices):
        DRAFT      = "draft",      "Draft"
        SUBMITTED  = "submitted",  "Submitted"
        APPROVED   = "approved",   "Approved"
        REJECTED   = "rejected",   "Rejected"

    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name="reports")
    nurse = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the nurse submitted this report for review.",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reviewed_reports",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default="")
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "reports_report"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report(Visit={self.visit_id}, v{self.version}, {self.status})"

    @property
    def is_locked(self):
        return self.status == self.Status.APPROVED