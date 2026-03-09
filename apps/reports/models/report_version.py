"""
Immutable snapshot of a report at each key action.
Sections stored as JSON so history is self-contained.
"""

from django.db import models
from django.conf import settings
from common.models import UUIDModel
from apps.reports.models.report import Report


class ReportVersion(UUIDModel):

    class Action(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        REJECTED  = "rejected",  "Rejected"
        APPROVED  = "approved",  "Approved"

    report = models.ForeignKey(Report, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()

    sections_snapshot = models.JSONField(
        default=list,
        help_text="Snapshot of all report sections at time of this action.",
    )

    action = models.CharField(max_length=20, choices=Action.choices)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="report_versions",
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "reports_version"
        ordering = ["version_number"]
        unique_together = [("report", "version_number")]
        indexes = [
            models.Index(fields=["created_at"]),
            # Audit queries filter/order by time of action
        ]

    def __str__(self):
        return f"ReportVersion(report={self.report_id}, v{self.version_number}, {self.action})"